import os, sys
from app.data_models import Settings, Activation, Account, ApiResponse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from server.app.salesforce_api import (
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
    convert_datetime_to_utc_z_format,
    datetime_to_iso_string_z,
    get_team_member_salesforce_ids,
)
from datetime import datetime, timezone


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
        first_prospecting_activity = activations[0].first_prospecting_activity
        activations.sort(key=lambda x: x.last_prospecting_activity, reverse=True)

        today = datetime.now().date()
        unresponsive_activation_candidates = [
            activation
            for activation in activations
            if add_days(
                activation.last_prospecting_activity.date(),
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
                convert_datetime_to_utc_z_format(first_prospecting_activity),
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


def increment_existing_activations(activations: list[Activation], settings: Settings):
    """
    Processes a list of activation objects and updates their counters based on criteria specified in the settings.

    Parameters:
    - `activations` (list): A list of activation objects to be processed, ASSUMED TO BE ORDERED BY first_prospecting_activity ASC.
    - `settings` (dict): A dictionary containing various criteria used to determine how the activation objects should be updated.

    Returns:
    - ApiResponse: `data` param is a collection of updated activation objects.
    """
    response = ApiResponse(data=[], message="", success=False)
    try:
        salesforce_user_ids = get_team_member_salesforce_ids(settings)

        first_prospecting_activity = convert_datetime_to_utc_z_format(
            activations[0].first_prospecting_activity
        )
        activations.sort(key=lambda x: x.last_prospecting_activity, reverse=True)
        account_ids = list(pluck(activations, "account.id"))
        already_counted_task_ids = [
            task_id for activation in activations for task_id in activation.task_ids
        ]
        criteria_group_tasks_by_account_id = (
            fetch_tasks_by_account_ids_from_date_not_in_ids(
                account_ids,
                first_prospecting_activity,
                settings.criteria,
                already_counted_task_ids,
                salesforce_user_ids,
            ).data
        )

        opportunities = fetch_opportunities_by_account_ids_from_date(
            account_ids, first_prospecting_activity, salesforce_user_ids
        ).data

        meetings_by_account_id = get_meetings_by_account_id(
            settings,
            account_ids,
            first_prospecting_activity,
            salesforce_user_ids,
        )

        activations_by_account_id = {
            activation.account.id: activation for activation in activations
        }

        for account_id in criteria_group_tasks_by_account_id:
            activation = activations_by_account_id.get(account_id)
            criteria_name_by_task_id = {}
            all_tasks = []

            for criteria in criteria_group_tasks_by_account_id[account_id]:
                for task in criteria_group_tasks_by_account_id[account_id][criteria]:
                    criteria_name_by_task_id[task.get("Id")] = criteria
                    all_tasks.append(task)

            # opportunity for merge sort implementation
            all_tasks = sorted(all_tasks, key=lambda x: x.get("CreatedDate"))
            for task in all_tasks:
                is_task_within_inactivity_threshold = is_model_date_field_within_window(
                    task,
                    activation.last_prospecting_activity,
                    settings.inactivity_threshold,
                )
                if not is_task_within_inactivity_threshold:
                    break
                activation.task_ids.append(task.get("Id"))
                activation.last_prospecting_activity = datetime.strptime(
                    task.get("CreatedDate"), "%Y-%m-%dT%H:%M:%S.%f%z"
                )
                activation.active_contact_ids.append(task.get("WhoId"))
                activations_by_account_id[account_id] = activation
                # rollup prospecting metadata via criteria_name_by_task_id

        opportunities_by_account_id = group_by(opportunities, "AccountId")

        for account_id in activations_by_account_id:
            activation = activations_by_account_id[account_id]
            opportunities = opportunities_by_account_id.get(account_id, [])
            events = meetings_by_account_id.get(account_id, [])

            if events:
                for event in events:
                    is_event_within_window = is_model_date_field_within_window(
                        event,
                        activation.first_prospecting_activity,
                        settings.inactivity_threshold,
                        date_field="CreatedDate",
                    )
                    if is_event_within_window and activation.status == "Activated":
                        activation.status = "Meeting Set"
                    elif is_event_within_window and (
                        activation.event_ids == None
                        or event["Id"] not in activation.event_ids
                    ):
                        activation.event_ids = (
                            [] if activation.event_ids is None else activation.event_ids
                        )
                        activation.event_ids.append(event["Id"])

            if opportunities:
                for opportunity in opportunities:
                    if is_model_date_field_within_window(
                        opportunity,
                        activation.first_prospecting_activity,
                        settings.inactivity_threshold,
                        date_field="CreatedDate",
                    ) and activation.status in ["Activated", "Meeting Set"]:
                        activation.opportunity = opportunities[0]
                        activation.status = "Opportunity Created"
                        break

            activations_by_account_id[account_id] = activation

        response.data = activations_by_account_id.values()
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

            start_tracking_period = all_tasks_under_account[0].get("CreatedDate")

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
                    task, start_tracking_period, settings.tracking_period
                )
                if is_task_in_tracking_period:
                    if task.get("WhoId") not in valid_task_ids_by_who_id:
                        valid_task_ids_by_who_id[task.get("WhoId")] = []
                        account_first_prospecting_activity = datetime.strptime(
                            task.get("CreatedDate"), "%Y-%m-%dT%H:%M:%S.%f%z"
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
                            account_first_prospecting_activity = datetime.strptime(
                                task.get("CreatedDate"), "%Y-%m-%dT%H:%M:%S.%f%z"
                            )
                            task_ids = [task.get("Id")]
                            last_valid_task_creator_id = task.get("OwnerId")
                        continue

                    # Can add Prospecting Metadata by
                    # finding Task Ids within task_ids_by_criteria_name
                    activations.append(
                        Activation(
                            id=generate_unique_id(),
                            account=Account(
                                name=contact_by_id[active_contact_ids[0]].account.name,
                                id=account_id,
                            ),
                            activated_date=account_first_prospecting_activity,
                            activated_by_id=last_valid_task_creator_id,
                            active_contact_ids=active_contact_ids,
                            last_prospecting_activity=datetime.strptime(
                                task.get("CreatedDate"), "%Y-%m-%dT%H:%M:%S.%f%z"
                            ),
                            first_prospecting_activity=account_first_prospecting_activity,
                            task_ids=task_ids,
                            opportunity=qualifying_opportunity,
                            event_ids=(
                                [qualifying_event["Id"]] if qualifying_event else None
                            ),
                            status=(
                                "Opportunity Created"
                                if qualifying_opportunity
                                else "Meeting Set" if qualifying_event else "Activated"
                            ),
                        )
                    )

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

            # Can add Prospecting Metadata by
            activations.append(
                Activation(
                    id=generate_unique_id(),
                    account=Account(
                        id=account_id,
                        name=contact_by_id[active_contact_ids[0]].account.name,
                    ),
                    activated_date=account_first_prospecting_activity.date(),
                    active_contact_ids=active_contact_ids,
                    activated_by_id=last_valid_task_creator_id,
                    first_prospecting_activity=account_first_prospecting_activity.date(),
                    last_prospecting_activity=datetime.strptime(
                        task.get("CreatedDate"), "%Y-%m-%dT%H:%M:%S.%f%z"
                    ).date(),
                    opportunity=qualifying_opportunity,
                    event_ids=[qualifying_event["Id"]] if qualifying_event else None,
                    task_ids=task_ids,
                    status=(
                        "Opportunity Created"
                        if qualifying_opportunity
                        else "Meeting Set" if qualifying_event else "Activated"
                    ),
                )
            )

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


def get_all_tasks_under_account(tasks_by_criteria_by_who_id):
    all_tasks_under_account = []
    for contact_id, tasks_by_criteria in tasks_by_criteria_by_who_id.items():
        for criteria, tasks in tasks_by_criteria.items():
            all_tasks_under_account.extend(tasks)
    return all_tasks_under_account


def get_first_prospecting_activity_date(tasks_by_criteria):
    first_prospecting_activity = None
    for criteria_key, tasks in tasks_by_criteria.items():
        for task in tasks:
            task_created_date = (
                datetime.strptime(task.get("CreatedDate"), "%Y-%m-%dT%H:%M:%S.%f%z")
                .astimezone(timezone.utc)
                .replace(tzinfo=None)
            )
            first_prospecting_activity = (
                task_created_date
                if not first_prospecting_activity
                else min(first_prospecting_activity, task_created_date)
            )
    if not first_prospecting_activity:
        first_prospecting_activity = datetime.now()
    return datetime_to_iso_string_z(first_prospecting_activity)


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
