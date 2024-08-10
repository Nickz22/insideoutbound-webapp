import os, sys
from app.data_models import (
    Settings,
    Activation,
    FilterContainer,
    ProspectingMetadata,
    ProspectingEffort,
    ApiResponse,
    StatusEnum,
)
from typing import List, Dict
from datetime import timedelta


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from app.salesforce_api import (
    fetch_tasks_by_account_ids_from_date_not_in_ids,
    fetch_opportunities_by_account_ids_from_date,
    fetch_events_by_account_ids_from_date,
)
from app.utils import (
    generate_unique_id,
    add_days,
    is_model_date_field_within_window,
    group_by,
    pluck,
    format_error_message,
    convert_date_to_salesforce_datetime_format,
    get_team_member_salesforce_ids,
    parse_datetime_string_with_timezone,
)
from datetime import datetime, date
from app.mapper.mapper import convert_dict_to_opportunity


def find_unresponsive_activations(
    activations: list[Activation], settings: Settings
) -> ApiResponse:
    """
    This function processes a list of activation objects and a settings dictionary to determine which activations are unresponsive.
    An activation is considered unresponsive if it has not had any prospecting activity within a specified threshold period.
    The function performs the following steps:

    1. Sorts activations in descending order based on their last prospecting activity date.
    2. Filters out activations that have not had any prospecting activity within the threshold period defined in the settings.
    3. Fetches tasks associated with the filtered activations that are not already counted and groups them by account ID.
    4. For each account, it checks if there are any new prospecting activities within the threshold period. If not, the activation status is updated to "Unresponsive".
    5. Returns a collection of activations that have been marked as unresponsive.

    Parameters:
        activations (list): A list of activation objects. Each activation object must have attributes for prospecting activity dates, account ID, and task IDs.
        settings (dict): A dictionary containing settings that define the criteria for considering an activation as unresponsive. This includes the account inactivity threshold and criteria for fetching tasks.

    Returns:
        ApiResponse: `data` parameter is a collection of activation objects that have been identified as unresponsive based on the lack of recent prospecting activity.
    """
    response = ApiResponse(data=[], message="", success=False)

    try:
        first_prospecting_activity = convert_date_to_salesforce_datetime_format(
            activations[0].first_prospecting_activity
        )
        activations.sort(key=lambda x: x.last_prospecting_activity, reverse=True)

        today = datetime.now().date()
        unresponsive_activation_candidates = [
            activation
            for activation in activations
            if add_days(
                activation.last_prospecting_activity,
                settings.inactivity_threshold,
            )
            < today
        ]

        if len(unresponsive_activation_candidates) == 0:
            response.data = []
            response.success = True
            return response

        account_ids = pluck(unresponsive_activation_candidates, "account.id")
        already_counted_task_ids = [
            task_id
            for activation in unresponsive_activation_candidates
            for task_id in activation.task_ids
        ]
        criteria_group_tasks_by_account_id = (
            fetch_tasks_by_account_ids_from_date_not_in_ids(
                list(account_ids),
                first_prospecting_activity,
                settings.criteria,
                already_counted_task_ids,
                get_team_member_salesforce_ids(settings),
            ).data
        )

        activations_by_account_id = {
            activation.account.id: activation
            for activation in unresponsive_activation_candidates
        }

        for account_id in criteria_group_tasks_by_account_id:
            activation = activations_by_account_id.get(account_id)
            criteria_name_by_task_id = {}
            all_tasks = []

            for criteria in criteria_group_tasks_by_account_id[account_id]:
                for task in criteria_group_tasks_by_account_id[account_id][criteria]:
                    criteria_name_by_task_id[task.get("Id")] = criteria
                    all_tasks.append(task)

            found_prospecting_activity = False
            for task in all_tasks:
                is_task_within_inactivity_threshold = is_model_date_field_within_window(
                    task,
                    activation.last_prospecting_activity,
                    settings["inactivity_threshold"],
                )
                if is_task_within_inactivity_threshold:
                    found_prospecting_activity = True
                    break

            if not found_prospecting_activity:
                activation.status = "Unresponsive"
                activations_by_account_id[account_id] = activation

        response.data = activations_by_account_id.values()
        response.success = True
    except Exception as e:
        raise Exception(format_error_message(e))

    return response


def increment_existing_activations(activations: List[Activation], settings: Settings):
    response = ApiResponse(data=[], message="", success=False)
    try:
        today = date.today()
        salesforce_user_ids = get_team_member_salesforce_ids(settings)

        first_prospecting_activity = convert_date_to_salesforce_datetime_format(
            min(activation.first_prospecting_activity for activation in activations)
        )
        activations.sort(key=lambda x: x.last_prospecting_activity, reverse=True)
        account_ids = list(set(activation.account.id for activation in activations))
        already_counted_task_ids = set(
            task_id for activation in activations for task_id in activation.task_ids
        )

        criteria_group_tasks_by_account_id = (
            fetch_tasks_by_account_ids_from_date_not_in_ids(
                account_ids,
                first_prospecting_activity,
                settings.criteria,
                already_counted_task_ids,
                salesforce_user_ids,
            ).data
        )

        opportunities_by_account_id: List[Dict] = group_by(
            fetch_opportunities_by_account_ids_from_date(
                account_ids, first_prospecting_activity, salesforce_user_ids
            ).data,
            "AccountId",
        )

        meetings_by_account_id: Dict[str, List[Dict]] = get_meetings_by_account_id(
            settings,
            account_ids,
            first_prospecting_activity,
            salesforce_user_ids,
        )

        activations_by_account_id: Dict[str, List[Activation]] = {
            activation.account.id: activation for activation in activations
        }

        for account_id, tasks_by_criteria in criteria_group_tasks_by_account_id.items():
            activation = activations_by_account_id.get(account_id)
            if not activation:
                continue

            all_tasks = []
            for criteria_name, tasks in tasks_by_criteria.items():
                all_tasks.extend((task, criteria_name) for task in tasks)
            all_tasks.sort(key=lambda x: x[0]["CreatedDate"])

            opportunities = opportunities_by_account_id.get(account_id, [])
            meetings = meetings_by_account_id.get(account_id, [])

            current_pe = (
                activation.prospecting_effort[-1]
                if activation.prospecting_effort
                else None
            )
            # shouldn't happen, but jic
            if not current_pe:
                current_pe = ProspectingEffort(
                    activation_id=activation.id,
                    prospecting_metadata=[],
                    status=activation.status,
                    date_entered=activation.activated_date,
                    tasks=[],
                )
                activation.prospecting_effort.append(current_pe)

            for task, criteria_name in all_tasks:
                task_created_datetime = parse_datetime_string_with_timezone(
                    task["CreatedDate"]
                )

                if task["Id"] in activation.task_ids:
                    continue

                # Determine new status
                new_status = get_new_status(
                    activation, settings.criteria, task, opportunities, meetings
                )

                if new_status != current_pe.status:
                    new_pe = ProspectingEffort(
                        activation_id=activation.id,
                        prospecting_metadata=[],
                        status=new_status,
                        date_entered=task_created_datetime.date(),
                        task_ids=[],
                    )
                    activation.prospecting_effort.append(new_pe)
                    current_pe = new_pe

                # Update activation and current PE
                activation.task_ids.add(task["Id"])
                activation.last_prospecting_activity = max(
                    activation.last_prospecting_activity, task_created_datetime.date()
                )
                activation.active_contact_ids.add(task["WhoId"])
                current_pe.task_ids.add(task["Id"])

                # Update ProspectingMetadata
                update_prospecting_metadata(current_pe, task, criteria_name)

                # Update Activation's metadata
                activation_metadata = next(
                    (
                        m
                        for m in activation.prospecting_metadata
                        if m.name == criteria_name
                    ),
                    None,
                )
                if activation_metadata:
                    activation_metadata.last_occurrence = max(
                        activation_metadata.last_occurrence,
                        task_created_datetime.date(),
                    )
                    activation_metadata.total += 1
                else:
                    activation.prospecting_metadata.append(
                        ProspectingMetadata(
                            name=criteria_name,
                            first_occurrence=task_created_datetime.date(),
                            last_occurrence=task_created_datetime.date(),
                            total=1,
                        )
                    )

                # Update engagement date if necessary
                if not activation.engaged_date and is_inbound_task(
                    task, settings.criteria
                ):
                    activation.engaged_date = task_created_datetime.date()

            # Update activation status and dates
            activation.status = current_pe.status
            activation.days_activated = (today - activation.activated_date).days
            if activation.engaged_date:
                activation.days_engaged = (today - activation.engaged_date).days

            # Update opportunity if necessary
            activation.opportunity = (
                convert_dict_to_opportunity(opportunities[0]) if opportunities else None
            )
            if (
                activation.opportunity
                and activation.status != StatusEnum.opportunity_created
            ):
                activation.status = StatusEnum.opportunity_created

            # Update meeting/event if necessary
            if meetings:
                if activation.event_ids is None:
                    activation.event_ids = []
                activation.event_ids.extend([meeting["Id"] for meeting in meetings])

            if (
                activation.event_ids
                and len(activation.event_ids) > 0
                and activation.status in [StatusEnum.activated, StatusEnum.engaged]
            ):
                activation.status = StatusEnum.meeting_set

        response.data = list(activations_by_account_id.values())
        response.success = True
    except Exception as e:
        raise Exception(format_error_message(e))

    return response


def is_inbound_task(task, criteria):
    for criterion in criteria:
        if (
            criterion.name == task["TaskSubtype"]
            and criterion.direction.lower() == "inbound"
        ):
            return True
    return False


def get_new_status(
    activation: Activation,
    task: Dict,
    criteria: List[FilterContainer],
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
    elif activation.status == StatusEnum.activated and is_inbound_task(task, criteria):
        return StatusEnum.engaged

    return activation.status


def update_prospecting_metadata(prospecting_effort, task, criteria_name):
    metadata = next(
        (m for m in prospecting_effort.prospecting_metadata if m.name == criteria_name),
        None,
    )
    task_date = parse_datetime_string_with_timezone(task["CreatedDate"]).date()

    if metadata:
        metadata.last_occurrence = max(metadata.last_occurrence, task_date)
        metadata.total += 1
    else:
        prospecting_effort.prospecting_metadata.append(
            ProspectingMetadata(
                name=criteria_name,
                first_occurrence=task_date,
                last_occurrence=task_date,
                total=1,
            )
        )


def has_any_inbound_task(
    task_ids, task_ids_by_criteria_name, criteria_name_by_direction
):
    for criteria_name, task_id_set in task_ids_by_criteria_name.items():
        if any(task_id in task_id_set for task_id in task_ids):
            if criteria_name_by_direction.get(criteria_name).lower() == "inbound":
                return True
    return False


def compute_activated_accounts(tasks_by_criteria, contacts, settings):
    """
    This function, `compute_activated_accounts`, is designed to process a collection of tasks, contacts, and settings to identify and construct activations for accounts.
    It aggregates tasks by account and contact, evaluates these tasks against a set of criteria defined in the settings, and determines whether an account has been activated within a specific tracking period.

    Parameters:
    - `tasks_by_criteria` (dict): A dictionary where each key represents a specific criteria name and each value is a list of task objects that meet that criteria.
    - `contacts` (list): A list of contact objects, where each contact is associated with an account.
    - `settings` (dict): A dictionary containing various settings that influence the activation computation. This includes:

    Returns:
    - `ApiResponse`: `data` parameter contains all activations and any relevant messages.
    """
    response = ApiResponse(data=[], message="", success=True)

    try:
        salesforce_user_ids = get_team_member_salesforce_ids(settings)
        tasks_by_account_id = get_tasks_by_account_id(tasks_by_criteria, contacts)
        first_prospecting_activity = get_first_prospecting_activity_date(
            tasks_by_criteria
        )
        opportunity_by_account_id = group_by(
            fetch_opportunities_by_account_ids_from_date(
                list(tasks_by_account_id.keys()),
                first_prospecting_activity,
                salesforce_user_ids,
            ).data,
            "AccountId",
        )
        meetings_by_account_id = get_meetings_by_account_id(
            settings,
            tasks_by_account_id.keys(),
            first_prospecting_activity,
            salesforce_user_ids,
        )

        criteria_name_by_direction = {
            criteria.name: criteria.direction for criteria in settings.criteria
        }
        task_ids_by_criteria_name = get_task_ids_by_criteria_name(tasks_by_account_id)
        contact_by_id = {contact.id: contact for contact in contacts}
        for account_id, tasks_by_criteria_by_who_id in tasks_by_account_id.items():
            all_tasks_under_account = get_all_tasks_under_account(
                tasks_by_criteria_by_who_id
            )

            if len(all_tasks_under_account) == 0:
                continue

            activations = []

            # although the Task API query is sorted already, grouping them potentially breaks a perfect sort
            ## so we'll sort again here to be safe...opportunity for optimization via merge sort
            all_tasks_under_account = sorted(
                all_tasks_under_account, key=lambda x: x.get("CreatedDate")
            )

            start_tracking_period = parse_datetime_string_with_timezone(
                all_tasks_under_account[0].get("CreatedDate")
            )

            qualifying_event = get_qualifying_meeting(
                meetings_by_account_id.get(account_id, []),
                start_tracking_period,
                settings.tracking_period,
            )

            qualifying_opportunity = get_qualifying_opportunity(
                opportunity_by_account_id.get(account_id, []),
                start_tracking_period,
                settings.tracking_period,
            )

            valid_task_ids_by_who_id = {}
            task_ids = []
            last_valid_task_creator_id = None

            for task in all_tasks_under_account:
                is_task_in_tracking_period = is_model_date_field_within_window(
                    sobject_model=task,
                    start_date=start_tracking_period,
                    period_days=settings.tracking_period,
                )
                if is_task_in_tracking_period:
                    if task.get("WhoId") not in valid_task_ids_by_who_id:
                        valid_task_ids_by_who_id[task.get("WhoId")] = []
                        account_first_prospecting_activity = (
                            parse_datetime_string_with_timezone(
                                task.get("CreatedDate")
                            ).date()
                        )
                    valid_task_ids_by_who_id[task.get("WhoId")].append(task.get("Id"))
                    last_valid_task_creator_id = task.get("OwnerId")
                    task_ids.append(task.get("Id"))

                if not is_task_in_tracking_period:
                    active_contact_ids = get_active_contact_ids(
                        valid_task_ids_by_who_id, settings.activities_per_contact
                    )

                    is_account_active_for_tracking_period = (
                        len(active_contact_ids) >= settings.contacts_per_account
                        or qualifying_event
                        or qualifying_opportunity
                    )
                    if not is_account_active_for_tracking_period:
                        start_tracking_period = add_days(
                            start_tracking_period,
                            settings.tracking_period + settings.inactivity_threshold,
                        )
                        valid_task_ids_by_who_id.clear()
                        account_first_prospecting_activity = None
                        task_ids.clear()
                        if is_model_date_field_within_window(
                            task, start_tracking_period, settings.tracking_period
                        ):
                            valid_task_ids_by_who_id[task.get("WhoId")] = [
                                task.get("Id")
                            ]
                            account_first_prospecting_activity = (
                                parse_datetime_string_with_timezone(
                                    task.get("CreatedDate")
                                ).date()
                            )
                            task_ids = [task.get("Id")]
                            last_valid_task_creator_id = task.get("OwnerId")
                        continue

                    last_prospecting_activity = parse_datetime_string_with_timezone(
                        task.get("CreatedDate")
                    ).date()

                    is_active_via_meeting_or_opportunity = len(active_contact_ids) == 0
                    active_contact_ids = (
                        list(valid_task_ids_by_who_id.keys())
                        if is_active_via_meeting_or_opportunity
                        else active_contact_ids
                    )
                    activation = create_activation(
                        contact_by_id,
                        account_first_prospecting_activity,
                        active_contact_ids,
                        last_valid_task_creator_id,
                        last_prospecting_activity,
                        task_ids,
                        qualifying_opportunity,
                        qualifying_event,
                        task_ids_by_criteria_name,
                        criteria_name_by_direction,
                        settings,
                        all_tasks_under_account,
                    )
                    activations.append(activation)

            # this account's tasks have ended, check for activation
            active_contact_ids = get_active_contact_ids(
                valid_task_ids_by_who_id, settings.activities_per_contact
            )

            is_account_active_for_tracking_period = (
                len(active_contact_ids) >= settings.contacts_per_account
                or qualifying_event
                or qualifying_opportunity
            )
            if not is_account_active_for_tracking_period:
                continue

            last_prospecting_activity = parse_datetime_string_with_timezone(
                task.get("CreatedDate")
            ).date()

            is_active_via_meeting_or_opportunity = len(active_contact_ids) == 0
            active_contact_ids = (
                list(valid_task_ids_by_who_id.keys())
                if is_active_via_meeting_or_opportunity
                else active_contact_ids
            )
            activation = create_activation(
                contact_by_id,
                account_first_prospecting_activity,
                active_contact_ids,
                last_valid_task_creator_id,
                last_prospecting_activity,
                task_ids,
                qualifying_opportunity,
                qualifying_event,
                task_ids_by_criteria_name,
                criteria_name_by_direction,
                settings,
                all_tasks_under_account,
            )
            activations.append(activation)
            response.data.extend(activations)

    except Exception as e:
        raise Exception(format_error_message(e))

    return response


def create_activation(
    contact_by_id,
    account_first_prospecting_activity,
    active_contact_ids,
    last_valid_task_creator_id,
    last_prospecting_activity,
    task_ids,
    qualifying_opportunity,
    qualifying_event,
    task_ids_by_criteria_name,
    criteria_name_by_direction,
    settings,
    all_tasks_under_account,
):
    today = date.today()

    # Find the first inbound task
    first_inbound_task = next(
        (
            task
            for task in all_tasks_under_account
            if task["Id"] in task_ids
            and any(
                task["Id"] in task_set
                for criteria_name, task_set in task_ids_by_criteria_name.items()
                if criteria_name_by_direction.get(criteria_name, "").lower()
                == "inbound"
            )
        ),
        None,
    )

    engaged_date = (
        parse_datetime_string_with_timezone(first_inbound_task["CreatedDate"])
        if first_inbound_task
        else None
    )

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
                if task["Id"] in task_ids
                and len(
                    [
                        t
                        for t in all_tasks_under_account
                        if t["CreatedDate"] <= task["CreatedDate"]
                        and t["Id"] in task_ids
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

    activation = Activation(
        id=generate_unique_id(),
        account=contact_by_id[active_contact_ids[0]].account,
        activated_date=activated_date,
        days_activated=(today - activated_date).days,
        engaged_date=engaged_date.date() if engaged_date else None,
        days_engaged=(today - engaged_date.date()).days if engaged_date else None,
        active_contact_ids=active_contact_ids,
        activated_by_id=last_valid_task_creator_id,
        first_prospecting_activity=account_first_prospecting_activity,
        last_prospecting_activity=last_prospecting_activity,
        opportunity=(
            convert_dict_to_opportunity(qualifying_opportunity)
            if qualifying_opportunity
            else None
        ),
        event_ids=[qualifying_event["Id"]] if qualifying_event else None,
        task_ids=task_ids,
        status=(
            StatusEnum.opportunity_created
            if qualifying_opportunity
            else (
                StatusEnum.meeting_set
                if qualifying_event
                else (
                    StatusEnum.engaged
                    if has_any_inbound_task(
                        task_ids, task_ids_by_criteria_name, criteria_name_by_direction
                    )
                    else StatusEnum.activated
                )
            )
        ),
        prospecting_metadata=create_prospecting_metadata(
            task_ids, task_ids_by_criteria_name, all_tasks_under_account
        ),
    )

    is_last_prospecting_activity_outside_of_inactivity_threshold = (
        add_days(last_prospecting_activity, settings.inactivity_threshold) < today
    )
    if is_last_prospecting_activity_outside_of_inactivity_threshold:
        activation.status = StatusEnum.unresponsive

    # Create ProspectingEfforts
    prospecting_efforts = []
    current_status = StatusEnum.activated
    current_status_date = activated_date
    current_tasks = []

    for task in all_tasks_under_account:
        if task["Id"] not in task_ids:
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
                current_status_date = parse_datetime_string_with_timezone(
                    qualifying_opportunity["CreatedDate"]
                ).date()
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
                current_status_date = parse_datetime_string_with_timezone(
                    qualifying_event["CreatedDate"]
                ).date()
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

    activation.prospecting_effort = prospecting_efforts

    return activation


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
            [task["Id"] for task in tasks], task_ids_by_criteria_name, tasks
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
                )
            )
    return metadata_list


# helpers with side effects
def get_meetings_by_account_id(
    settings: Settings,
    account_ids: list[str],
    first_prospecting_activity: datetime,
    salesforce_user_ids: list[str],
):
    meetings_by_account_id = {}
    if settings.meeting_object == "Event":
        meetings_by_account_id = fetch_events_by_account_ids_from_date(
            list(account_ids),
            first_prospecting_activity,
            salesforce_user_ids,
            settings.meetings_criteria,
        ).data
    elif settings.meeting_object == "Task":
        meetings_by_criteria_name_by_account_id = (
            fetch_tasks_by_account_ids_from_date_not_in_ids(
                list(account_ids),
                first_prospecting_activity,
                [settings.meetings_criteria],
                [],
                salesforce_user_ids,
            ).data
        )

        for (
            account_id,
            meetings_by_criteria,
        ) in meetings_by_criteria_name_by_account_id.items():
            if account_id not in meetings_by_account_id:
                meetings_by_account_id[account_id] = []
            for criteria, meetings in meetings_by_criteria.items():
                meetings_by_account_id[account_id].extend(meetings)
    return meetings_by_account_id


# helpers


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
