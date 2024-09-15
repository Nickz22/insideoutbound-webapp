import os, sys
from app.data_models import (
    Settings,
    Activation,
    ProspectingMetadata,
    ProspectingEffort,
    ApiResponse,
    StatusEnum,
)
from typing import List, Dict
from flask import current_app as app

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from app.salesforce_api import (
    fetch_opportunities_by_account_ids_from_date,
    fetch_events_by_account_ids_from_date,
    fetch_salesforce_users,
)
from app.utils import (
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
from app.helpers.activation_helper import (
    update_prospecting_metadata,
    get_new_status,
    create_activation,
    get_task_ids_by_criteria_name,
    get_all_tasks_under_account,
    get_first_prospecting_activity_date,
    get_tasks_by_account_id,
    get_qualifying_meeting,
    get_qualifying_opportunity,
    get_active_contact_ids,
    get_filtered_tasks_under_account,
    get_inbound_tasks_within_period,
)


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
        async_response = app.async_fetch_tasks_by_account_ids_from_date_not_in_ids(
            list(account_ids),
            first_prospecting_activity,
            settings.criteria,
            already_counted_task_ids,
            get_team_member_salesforce_ids(settings),
        )

        criteria_group_tasks_by_account_id = async_response.data

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
            last_prospecting_activity_naive = datetime.combine(
                activation.last_prospecting_activity, datetime.min.time()
            )
            for task in all_tasks:
                is_task_within_inactivity_threshold = is_model_date_field_within_window(
                    task,
                    last_prospecting_activity_naive,
                    settings.inactivity_threshold,
                )
                if is_task_within_inactivity_threshold:
                    found_prospecting_activity = True
                    break

            if not found_prospecting_activity:
                activation.status = "Unresponsive"
                activations_by_account_id[account_id] = activation

        response.data = list(activations_by_account_id.values())
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

        response = app.async_fetch_tasks_by_account_ids_from_date_not_in_ids(
            account_ids,
            first_prospecting_activity,
            settings.criteria,
            already_counted_task_ids,
            salesforce_user_ids,
        )

        criteria_group_tasks_by_account_id = response.data

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
        
        criterion_by_name = {criterion.name: criterion for criterion in settings.criteria}

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

            current_prospecting_effort = (
                activation.prospecting_effort[-1]
                if activation.prospecting_effort
                else None
            )
            # shouldn't happen, but jic
            if not current_prospecting_effort:
                current_prospecting_effort = ProspectingEffort(
                    activation_id=activation.id,
                    prospecting_metadata=[],
                    status=activation.status,
                    date_entered=activation.activated_date,
                    tasks=[],
                )
                activation.prospecting_effort.append(current_prospecting_effort)

            for task, criteria_name in all_tasks:
                task_created_datetime = parse_datetime_string_with_timezone(
                    task["CreatedDate"]
                )

                if task["Id"] in activation.task_ids:
                    continue

                # Determine new status
                new_status = get_new_status(
                    activation=activation,
                    criterion=criterion_by_name.get(criteria_name),
                    opportunities=opportunities,
                    events=meetings,
                )

                if new_status != current_prospecting_effort.status:
                    new_pe = ProspectingEffort(
                        activation_id=activation.id,
                        prospecting_metadata=[],
                        status=new_status,
                        date_entered=task_created_datetime.date(),
                        task_ids=[],
                    )
                    activation.prospecting_effort.append(new_pe)
                    current_prospecting_effort = new_pe

                # Update activation and current PE
                activation.task_ids.add(task["Id"])
                activation.last_prospecting_activity = max(
                    activation.last_prospecting_activity, task_created_datetime.date()
                )
                activation.active_contact_ids.add(task["WhoId"])
                current_prospecting_effort.task_ids.add(task["Id"])

                # Update ProspectingMetadata
                update_prospecting_metadata(current_prospecting_effort, task, criteria_name)

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
                if not activation.engaged_date and criterion_by_name.get(criteria_name).direction.lower() == "inbound":
                    activation.engaged_date = task_created_datetime.date()

            # Update activation status and dates
            activation.status = current_prospecting_effort.status
            activation.days_activated = (today - activation.activated_date).days
            if activation.engaged_date:
                activation.days_engaged = (today - activation.engaged_date).days

            # Update opportunity if necessary
            activation.opportunity = (
                convert_dict_to_opportunity(opportunities[0])
                if opportunities and len(opportunities) > 0
                else None
            )
            if (
                activation.opportunity
                and activation.status != StatusEnum.opportunity_created
            ):
                activation.status = StatusEnum.opportunity_created
                # create new prospecting effort
                new_pe = ProspectingEffort(
                    activation_id=activation.id,
                    prospecting_metadata=[],
                    status=activation.status,
                    date_entered=activation.activated_date,
                    task_ids=[],
                )
                activation.prospecting_effort.append(new_pe)
                current_prospecting_effort = new_pe

            # Update meeting/event if necessary
            if meetings:
                if activation.event_ids is None:
                    activation.event_ids = set()
                activation.event_ids.update(meeting["Id"] for meeting in meetings)

            if (
                activation.event_ids
                and len(activation.event_ids) > 0
                and activation.status in [StatusEnum.activated, StatusEnum.engaged]
            ):
                activation.status = StatusEnum.meeting_set
                new_pe = ProspectingEffort(
                    activation_id=activation.id,
                    prospecting_metadata=[],
                    status=activation.status,
                    date_entered=activation.activated_date,
                    task_ids=[],
                )
                activation.prospecting_effort.append(new_pe)
                current_prospecting_effort = new_pe

        response.data = list(activations_by_account_id.values())
        response.success = True
    except Exception as e:
        raise Exception(format_error_message(e))

    return response


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

    def fetch_account_data(settings, tasks_by_account_id, first_prospecting_activity):
        salesforce_user_ids = get_team_member_salesforce_ids(settings)
        salesforce_user_by_id = group_by(
            fetch_salesforce_users(salesforce_user_ids).data, "id"
        )
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
        return salesforce_user_by_id, opportunity_by_account_id, meetings_by_account_id

    response = ApiResponse(data=[], message="", success=True)

    try:
        tasks_by_account_id = get_tasks_by_account_id(tasks_by_criteria, contacts)
        salesforce_user_by_id, opportunity_by_account_id, meetings_by_account_id = (
            fetch_account_data(
                settings,
                tasks_by_account_id,
                get_first_prospecting_activity_date(tasks_by_criteria),
            )
        )

        task_ids_by_criteria_name = get_task_ids_by_criteria_name(tasks_by_account_id)
        contact_by_id = {contact.id: contact for contact in contacts}
        for account_id, tasks_by_criteria_by_who_id in tasks_by_account_id.items():
            all_tasks_under_account = get_all_tasks_under_account(
                tasks_by_criteria_by_who_id
            )

            all_outbound_tasks_under_account = get_filtered_tasks_under_account(
                tasks_by_criteria_by_who_id, settings.criteria, "outbound"
            )

            if len(all_outbound_tasks_under_account) == 0:
                continue

            # Get all inbound tasks for this account
            all_inbound_tasks = get_filtered_tasks_under_account(
                tasks_by_criteria_by_who_id, settings.criteria, "inbound"
            )

            activations = []

            # although the Task API query is sorted already,
            ## grouping them potentially breaks a perfect sort
            ### so we'll sort again here to be safe...opportunity for optimization via merge sort
            all_tasks_under_account = sorted(
                all_tasks_under_account, key=lambda x: x.get("CreatedDate")
            )
            all_outbound_tasks_under_account = sorted(
                all_outbound_tasks_under_account, key=lambda x: x.get("CreatedDate")
            )
            all_inbound_tasks = sorted(
                all_inbound_tasks, key=lambda x: x.get("CreatedDate")
            )

            start_tracking_period = parse_datetime_string_with_timezone(
                all_outbound_tasks_under_account[0].get("CreatedDate")
            )

            valid_task_ids_by_who_id = {}
            task_ids = []
            last_valid_task_assignee_id = None

            for task in all_outbound_tasks_under_account:
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
                    last_valid_task_assignee_id = task.get("OwnerId")
                    task_ids.append(task.get("Id"))

                if not is_task_in_tracking_period:
                    active_contact_ids = get_active_contact_ids(
                        valid_task_ids_by_who_id, settings.activities_per_contact
                    )

                    is_account_active_for_tracking_period = (
                        len(active_contact_ids) >= settings.contacts_per_account
                        or (qualifying_event and settings.activate_by_meeting)
                        or (qualifying_opportunity and settings.activate_by_opportunity)
                    )
                    if not is_account_active_for_tracking_period:
                        ## reset tracking
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
                            last_valid_task_assignee_id = task.get("OwnerId")
                        continue

                    last_prospecting_activity = parse_datetime_string_with_timezone(
                        task.get("CreatedDate")
                    ).date()

                    is_active_via_meeting_or_opportunity = (
                        len(active_contact_ids) < settings.contacts_per_account
                    )
                    active_contact_ids = (
                        list(valid_task_ids_by_who_id.keys())
                        if is_active_via_meeting_or_opportunity
                        else active_contact_ids
                    )

                    # Get inbound tasks within the current tracking period
                    inbound_tasks_in_period = get_inbound_tasks_within_period(
                        all_inbound_tasks,
                        start_tracking_period,
                        settings.tracking_period,
                    )
                    engaged_date = (
                        parse_datetime_string_with_timezone(
                            inbound_tasks_in_period[0].get("CreatedDate")
                        )
                        if len(inbound_tasks_in_period) > 0
                        else None
                    )

                    activation = create_activation(
                        contact_by_id=contact_by_id,
                        account_first_prospecting_activity=account_first_prospecting_activity,
                        active_contact_ids=active_contact_ids,
                        last_valid_task_creator=salesforce_user_by_id.get(
                            last_valid_task_assignee_id
                        )[0],
                        last_prospecting_activity=last_prospecting_activity,
                        outbound_task_ids=task_ids,
                        qualifying_opportunity=qualifying_opportunity,
                        qualifying_event=qualifying_event,
                        task_ids_by_criteria_name=task_ids_by_criteria_name,
                        settings=settings,
                        all_tasks_under_account=all_tasks_under_account,
                        engaged_date=engaged_date,
                    )
                    activations.append(activation)
                    ## reset tracking period
                    start_tracking_period = add_days(
                        start_tracking_period,
                        settings.tracking_period + settings.inactivity_threshold,
                    )
                    valid_task_ids_by_who_id.clear()
                    account_first_prospecting_activity = None
                    task_ids.clear()

            # this account's tasks have ended, check for activation
            active_contact_ids = get_active_contact_ids(
                valid_task_ids_by_who_id, settings.activities_per_contact
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

            is_account_active_for_tracking_period = (
                len(active_contact_ids) >= settings.contacts_per_account
                or (qualifying_event and settings.activate_by_meeting)
                or (qualifying_opportunity and settings.activate_by_opportunity)
            )
            if not is_account_active_for_tracking_period:
                continue

            last_prospecting_activity = parse_datetime_string_with_timezone(
                task.get("CreatedDate")
            ).date()

            is_active_via_meeting_or_opportunity = (
                len(active_contact_ids) < settings.contacts_per_account
            )
            active_contact_ids = (
                list(valid_task_ids_by_who_id.keys())
                if is_active_via_meeting_or_opportunity
                else active_contact_ids
            )

            inbound_tasks_in_period = get_inbound_tasks_within_period(
                all_inbound_tasks, start_tracking_period, settings.tracking_period
            )
            engaged_date = (
                parse_datetime_string_with_timezone(
                    inbound_tasks_in_period[0].get("CreatedDate")
                )
                if len(inbound_tasks_in_period) > 0
                else None
            )
            activation = create_activation(
                contact_by_id=contact_by_id,
                account_first_prospecting_activity=account_first_prospecting_activity,
                active_contact_ids=active_contact_ids,
                last_valid_task_creator=salesforce_user_by_id.get(
                    last_valid_task_assignee_id
                )[0],
                last_prospecting_activity=last_prospecting_activity,
                outbound_task_ids=task_ids,
                qualifying_opportunity=qualifying_opportunity,
                qualifying_event=qualifying_event,
                task_ids_by_criteria_name=task_ids_by_criteria_name,
                settings=settings,
                all_tasks_under_account=all_tasks_under_account,
                engaged_date=engaged_date,
            )
            activations.append(activation)
            response.data.extend(activations)

    except Exception as e:
        raise Exception(format_error_message(e))

    return response


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
        task_meetings = app.async_fetch_tasks_by_account_ids_from_date_not_in_ids(
            list(account_ids),
            first_prospecting_activity,
            [settings.meetings_criteria],
            [],
            salesforce_user_ids,
        )
        meetings_by_criteria_name_by_account_id = task_meetings.data

        for (
            account_id,
            meetings_by_criteria,
        ) in meetings_by_criteria_name_by_account_id.items():
            if account_id not in meetings_by_account_id:
                meetings_by_account_id[account_id] = []
            for criteria, meetings in meetings_by_criteria.items():
                meetings_by_account_id[account_id].extend(meetings)
    return meetings_by_account_id
