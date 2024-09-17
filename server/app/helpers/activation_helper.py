from typing import Dict, List
from datetime import datetime, date
from collections import defaultdict
from app.data_models import Activation
from app.utils import (
    parse_datetime_string_with_timezone,
    add_days,
    generate_unique_id,
    is_model_date_field_within_window,
    convert_date_to_salesforce_datetime_format,
)
from app.data_models import (
    ProspectingMetadata,
    FilterContainer,
    StatusEnum,
    ProspectingEffort,
)
from app.mapper.mapper import convert_dict_to_opportunity


def generate_summary(activations: list[Activation]) -> dict:
    today = datetime.now().date()
    summary = {
        "total_activations": len(activations),
        "activations_today": 0,
        "total_tasks": 0,
        "total_events": 0,
        "total_contacts": 0,
        "total_accounts": 0,
        "total_deals": 0,
        "total_pipeline_value": 0,
        "engaged_activations": 0,
        "total_active_contacts": 0,
    }

    account_contacts = defaultdict(set)

    for activation in activations:
        if activation.activated_date == today:
            summary["activations_today"] += 1

        summary["total_tasks"] += len(activation.task_ids)
        summary["total_events"] += (
            len(activation.event_ids) if activation.event_ids else 0
        )
        account_id = activation.account.id
        account_contacts[account_id].update(activation.active_contact_ids)

        if activation.opportunity:
            summary["total_deals"] += 1
            summary["total_pipeline_value"] += activation.opportunity.amount
        if activation.status == "Engaged":
            summary["engaged_activations"] += 1

    summary["total_contacts"] = sum(
        len(contacts) for contacts in account_contacts.values()
    )
    summary["total_active_contacts"] = len(account_contacts)
    summary["total_accounts"] = len(account_contacts)
    summary["avg_tasks_per_contact"] = (
        summary["total_tasks"] / summary["total_contacts"]
        if summary["total_contacts"] > 0
        else 0
    )
    summary["avg_contacts_per_account"] = (
        summary["total_contacts"] / summary["total_accounts"]
        if summary["total_accounts"] > 0
        else 0
    )

    return summary


def update_prospecting_metadata(prospecting_effort, task, criteria_name):
    metadata = next(
        (m for m in prospecting_effort.prospecting_metadata if m.name == criteria_name),
        None,
    )
    task_date = parse_datetime_string_with_timezone(task["CreatedDate"]).date()

    if metadata:
        metadata.last_occurrence = max(metadata.last_occurrence, task_date)
        metadata.total += 1
        metadata.tasks.append(task)
    else:
        prospecting_effort.prospecting_metadata.append(
            ProspectingMetadata(
                name=criteria_name,
                first_occurrence=task_date,
                last_occurrence=task_date,
                total=1,
                tasks=[task],
            )
        )


def get_new_status(
    activation: Activation,
    criterion: FilterContainer,
    opportunities: List[Dict],
    events: List[Dict],
):

    if (
        opportunities
        and opportunities[0]
        and activation.status != StatusEnum.opportunity_created
    ):
        return StatusEnum.opportunity_created
    elif (
        events
        and events[0]
        and activation.status != StatusEnum.meeting_set
        and activation.status != StatusEnum.opportunity_created
    ):
        return StatusEnum.meeting_set
    elif activation.status == StatusEnum.activated and criterion.direction.lower() == "inbound":
        return StatusEnum.engaged

    return activation.status


def create_activation(
    contact_by_id,
    account_first_prospecting_activity,
    active_contact_ids,
    last_valid_task_creator,
    last_prospecting_activity,
    outbound_task_ids,
    qualifying_opportunity,
    qualifying_event,
    task_ids_by_criteria_name,
    settings,
    all_tasks_under_account,
    engaged_date,
):
    today = date.today()

    # Determine the activated_date based on the activation condition
    if qualifying_opportunity:
        activated_date = parse_datetime_string_with_timezone(
            qualifying_opportunity["CreatedDate"]
        ).date()
    elif qualifying_event:
        activated_date = parse_datetime_string_with_timezone(
            qualifying_event["CreatedDate"]
        ).date()
    else:
        # Find the task that caused the account to meet the activation criteria
        activating_task = next(
            (
                task
                for task in reversed(all_tasks_under_account)
                if task["Id"] in outbound_task_ids
                and len(
                    [
                        t
                        for t in all_tasks_under_account
                        if t["CreatedDate"] <= task["CreatedDate"]
                        and t["Id"] in outbound_task_ids
                    ]
                )
                >= settings.activities_per_contact * settings.contacts_per_account
            ),
            None,
        )
        activated_date = (
            parse_datetime_string_with_timezone(activating_task["CreatedDate"]).date()
            if activating_task
            else account_first_prospecting_activity
        )

    activation_status = (
        StatusEnum.opportunity_created
        if qualifying_opportunity
        else (
            StatusEnum.meeting_set
            if qualifying_event
            else (StatusEnum.engaged if engaged_date else StatusEnum.activated)
        )
    )
    activation = Activation(
        id=generate_unique_id(),
        account=(
            contact_by_id[active_contact_ids[0]].account
            if active_contact_ids
            else next(iter(contact_by_id.values())).account
        ),
        activated_date=activated_date,
        days_activated=(today - activated_date).days,
        engaged_date=engaged_date.date() if engaged_date else None,
        days_engaged=(today - engaged_date.date()).days if engaged_date else None,
        active_contact_ids=active_contact_ids,
        active_contacts=[contact_by_id[contact_id] for contact_id in active_contact_ids if contact_id in contact_by_id],
        activated_by=last_valid_task_creator,
        first_prospecting_activity=account_first_prospecting_activity,
        last_prospecting_activity=last_prospecting_activity,
        opportunity=(
            convert_dict_to_opportunity(qualifying_opportunity)
            if qualifying_opportunity
            else None
        ),
        event_ids=[qualifying_event["Id"]] if qualifying_event else None,
        task_ids=outbound_task_ids,
        status=activation_status,
        prospecting_metadata=create_prospecting_metadata(
            task_ids=outbound_task_ids,
            task_ids_by_criteria_name=task_ids_by_criteria_name,
            all_tasks_under_account=all_tasks_under_account
        ),
    )

    is_last_prospecting_activity_outside_of_inactivity_threshold = (
        add_days(last_prospecting_activity, settings.inactivity_threshold) < today
    )
    if is_last_prospecting_activity_outside_of_inactivity_threshold:
        activation.status = StatusEnum.unresponsive

    activation.prospecting_effort = create_prospecting_efforts(
        activation,
        all_tasks_under_account,
        outbound_task_ids,
        task_ids_by_criteria_name,
        qualifying_opportunity,
        qualifying_event,
        engaged_date,
        activated_date,
    )

    return activation


def create_prospecting_efforts(
    activation: Activation,
    all_tasks_under_account: List[Dict],
    outbound_task_ids: List[str],
    task_ids_by_criteria_name: Dict[str, List[str]],
    qualifying_opportunity: Dict,
    qualifying_event: Dict,
    engaged_date: datetime,
    activated_date: date,
) -> List[ProspectingEffort]:
    prospecting_efforts = []
    current_status = StatusEnum.activated
    current_status_date = activated_date
    current_tasks = []

    meeting_time = None
    opportunity_time = None
    for task in all_tasks_under_account:
        if task["Id"] not in outbound_task_ids:
            continue

        task_date = parse_datetime_string_with_timezone(task["CreatedDate"])

        if qualifying_opportunity and task_date >= parse_datetime_string_with_timezone(
            qualifying_opportunity["CreatedDate"]
        ):
            if current_status != StatusEnum.opportunity_created:
                prospecting_efforts.append(
                    create_prospecting_effort(
                        activation.id,
                        current_status,
                        current_status_date,
                        current_tasks,
                        task_ids_by_criteria_name,
                    )
                )
                current_status = StatusEnum.opportunity_created
                opportunity_time = parse_datetime_string_with_timezone(
                    qualifying_opportunity["CreatedDate"]
                )
                current_status_date = opportunity_time.date()
                current_tasks = []

        elif qualifying_event and task_date >= parse_datetime_string_with_timezone(
            qualifying_event["CreatedDate"]
        ):
            if current_status != StatusEnum.meeting_set:
                prospecting_efforts.append(
                    create_prospecting_effort(
                        activation.id,
                        current_status,
                        current_status_date,
                        current_tasks,
                        task_ids_by_criteria_name,
                    )
                )
                current_status = StatusEnum.meeting_set
                meeting_time = parse_datetime_string_with_timezone(
                    qualifying_event["CreatedDate"]
                )
                current_status_date = meeting_time.date()
                current_tasks = []
        elif (
            engaged_date
            and task_date >= engaged_date
            and current_status == StatusEnum.activated
        ):
            prospecting_efforts.append(
                create_prospecting_effort(
                    activation.id,
                    current_status,
                    current_status_date,
                    current_tasks,
                    task_ids_by_criteria_name,
                )
            )
            current_status = StatusEnum.engaged
            current_status_date = engaged_date
            current_tasks = []

        current_tasks.append(task)

    # Add the final ProspectingEffort
    prospecting_efforts.append(
        create_prospecting_effort(
            activation.id,
            current_status,
            current_status_date,
            current_tasks,
            task_ids_by_criteria_name,
        )
    )

    # Create prospecting effort for the current status if no tasks have been created since that Status has been set
    if not any(pe.status == activation.status for pe in prospecting_efforts):
        prospecting_efforts.append(
            create_prospecting_effort(
                activation.id, activation.status, activation.activated_date, [], {}
            )
        )
        if activation.status == StatusEnum.opportunity_created:
            opportunity_time = parse_datetime_string_with_timezone(
                qualifying_opportunity["CreatedDate"]
            )
        elif activation.status == StatusEnum.meeting_set:
            meeting_time = parse_datetime_string_with_timezone(
                qualifying_event["CreatedDate"]
            )

    if engaged_date:
        has_meeting_set = any(pe.status == StatusEnum.meeting_set for pe in prospecting_efforts)
        has_engaged = any(pe.status == StatusEnum.engaged for pe in prospecting_efforts)
        has_opportunity = any(pe.status == StatusEnum.opportunity_created for pe in prospecting_efforts)
        
        if not has_meeting_set and not has_engaged and not has_opportunity:
            prospecting_efforts.append(
                create_prospecting_effort(
                    activation.id, StatusEnum.engaged, engaged_date, [], {}
                )
            )
        elif has_meeting_set and not has_engaged:
            meeting_set_index = next(i for i, pe in enumerate(prospecting_efforts) if pe.status == StatusEnum.meeting_set)
            if engaged_date < meeting_time:
                prospecting_efforts.insert(
                    meeting_set_index,
                    create_prospecting_effort(
                        activation.id, StatusEnum.engaged, engaged_date, [], {}
                    )
                )
        elif has_opportunity and not has_engaged and not has_meeting_set:
            opportunity_index = next(i for i, pe in enumerate(prospecting_efforts) if pe.status == StatusEnum.opportunity_created)
            if engaged_date < opportunity_time:
                prospecting_efforts.insert(
                    opportunity_index,
                    create_prospecting_effort(
                        activation.id, StatusEnum.engaged, engaged_date, [], {}
                    )
                )
    
    # Sort this mess, because apparently chronological order is too much to ask for
    prospecting_efforts.sort(key=lambda pe: pe.date_entered)

    return prospecting_efforts


def create_prospecting_effort(
    activation_id, status, date_entered, tasks, task_ids_by_criteria_name
):
    date_value_date_entered = None
    if isinstance(date_entered, datetime):
        date_value_date_entered = date_entered.date()
    else:
        date_value_date_entered = date_entered
    return ProspectingEffort(
        activation_id=activation_id,
        prospecting_metadata=create_prospecting_metadata(
            task_ids=[task["Id"] for task in tasks],
            task_ids_by_criteria_name=task_ids_by_criteria_name,
            all_tasks_under_account=tasks,
        ),
        status=status,
        date_entered=date_value_date_entered,
        task_ids=[task["Id"] for task in tasks],
    )


def create_prospecting_metadata(
    task_ids: List[str],
    task_ids_by_criteria_name: Dict[str, List[str]],
    all_tasks_under_account: List[Dict],
) -> List[ProspectingMetadata]:
    metadata_list = []
    for criteria_name, criteria_task_ids in task_ids_by_criteria_name.items():
        matching_task_ids = set(task_ids) & set(criteria_task_ids)
        if matching_task_ids:
            matching_tasks = [
                task
                for task in all_tasks_under_account
                if task["Id"] in matching_task_ids
            ]
            first_occurrence = min(
                datetime.strptime(task["CreatedDate"], "%Y-%m-%dT%H:%M:%S.%f%z").date()
                for task in matching_tasks
            )
            last_occurrence = max(
                datetime.strptime(task["CreatedDate"], "%Y-%m-%dT%H:%M:%S.%f%z").date()
                for task in matching_tasks
            )
            metadata_list.append(
                ProspectingMetadata(
                    name=criteria_name,
                    first_occurrence=first_occurrence,
                    last_occurrence=last_occurrence,
                    total=len(matching_task_ids),
                    tasks=matching_tasks,
                )
            )

    return metadata_list


def get_task_ids_by_criteria_name(tasks_by_account_id):
    task_ids_by_criteria_name = {}
    for account_id, tasks_by_criteria_by_who_id in tasks_by_account_id.items():
        for contact_id, tasks_by_criteria in tasks_by_criteria_by_who_id.items():
            for criteria, tasks in tasks_by_criteria.items():
                if criteria not in task_ids_by_criteria_name:
                    task_ids_by_criteria_name[criteria] = set()
                task_ids_by_criteria_name[criteria].update(
                    [task.get("Id") for task in tasks]
                )

    return task_ids_by_criteria_name


def get_all_tasks_under_account(tasks_by_criteria_by_who_id) -> List[Dict]:
    all_tasks_under_account = []
    for contact_id, tasks_by_criteria in tasks_by_criteria_by_who_id.items():
        for criteria, tasks in tasks_by_criteria.items():
            all_tasks_under_account.extend(tasks)
    return all_tasks_under_account


def get_filtered_tasks_under_account(
    tasks_by_criteria_by_who_id, criteria_list: List[FilterContainer], direction: str
) -> List[Dict]:
    filtered_tasks = []
    criteria_directions = {
        criteria.name: criteria.direction.lower() for criteria in criteria_list
    }

    for contact_id, tasks_by_criteria in tasks_by_criteria_by_who_id.items():
        for criteria_name, tasks in tasks_by_criteria.items():
            if criteria_directions.get(criteria_name) == direction.lower():
                filtered_tasks.extend(tasks)

    return filtered_tasks


def get_first_prospecting_activity_date(tasks_by_criteria):
    first_prospecting_activity = None
    for criteria_key, tasks in tasks_by_criteria.items():
        for task in tasks:
            task_created_date = parse_datetime_string_with_timezone(
                task.get("CreatedDate")
            )
            first_prospecting_activity = (
                task_created_date
                if not first_prospecting_activity
                else min(first_prospecting_activity, task_created_date)
            )
    if not first_prospecting_activity:
        first_prospecting_activity = datetime.now()
    return convert_date_to_salesforce_datetime_format(first_prospecting_activity.date())


def get_tasks_by_account_id(tasks_by_criteria, contacts):
    tasks_by_account_id = {}
    contact_by_id = {contact.id: contact for contact in contacts}
    for criteria_key, tasks in tasks_by_criteria.items():
        for task in tasks:
            contact = contact_by_id.get(task.get("WhoId"))
            if not contact:
                continue
            account_id = contact.account_id
            if account_id not in tasks_by_account_id.keys():
                tasks_by_account_id[account_id] = {}
            if task.get("WhoId") not in tasks_by_account_id[account_id]:
                tasks_by_account_id[account_id][task.get("WhoId")] = {}
            if criteria_key not in tasks_by_account_id[account_id][task.get("WhoId")]:
                tasks_by_account_id[account_id][task.get("WhoId")][criteria_key] = []
            tasks_by_account_id[account_id][task.get("WhoId")][criteria_key].append(
                task
            )
    return tasks_by_account_id


def get_qualifying_meeting(meetings, start_date, tracking_period):
    qualifying_meeting = None
    if len(meetings) == 0:
        return qualifying_meeting
    is_task = meetings[0].get("Id").startswith("00T")
    for meeting in meetings:
        if is_model_date_field_within_window(
            meeting,
            start_date,
            tracking_period,
            "StartDateTime" if not is_task else "CreatedDate",
        ):
            qualifying_meeting = meeting
            break
    return qualifying_meeting


def get_qualifying_opportunity(opportunities, start_date, tracking_period):
    qualifying_opportunity = None
    for opportunity in opportunities:
        if is_model_date_field_within_window(
            opportunity, start_date, tracking_period, date_field="CreatedDate"
        ):
            qualifying_opportunity = opportunity
            break
    return qualifying_opportunity


def get_active_contact_ids(task_ids_by_who_id, activities_per_contact):
    active_contact_ids = []
    for who_id, valid_task_ids in task_ids_by_who_id.items():
        is_contact_active = len(valid_task_ids) >= activities_per_contact
        if is_contact_active:
            active_contact_ids.append(who_id)
    return active_contact_ids


def get_inbound_tasks_within_period(inbound_tasks, start_date, period_days):
    return [
        task
        for task in inbound_tasks
        if is_model_date_field_within_window(task, start_date, period_days)
    ]
