import os, sys
import traceback
from app.data_models import (
    FilterContainer,
    Settings,
    Activation,
    ProspectingMetadata,
    ProspectingEffort,
    ApiResponse,
    StatusEnum,
    Contact,
)
from typing import List, Dict
from flask import current_app as app
import asyncio
from sentry_sdk import capture_exception, set_context

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from app.salesforce_api import (
    fetch_contacts_by_account_ids,
    fetch_events_by_contact_ids_from_date,
    fetch_opportunities_by_account_ids_from_date,
    fetch_salesforce_users,
    fetch_prospecting_tasks_by_account_ids_from_date_not_in_ids,
)
from app.utils import (
    add_days,
    is_model_date_field_within_window,
    group_by,
    format_error_message,
    convert_date_to_salesforce_datetime_format,
    get_team_member_salesforce_ids,
    parse_datetime_string_with_timezone,
)
from datetime import datetime, date
from app.mapper.mapper import convert_dict_to_opportunity
from app.helpers.activation_helper import (
    increment_prospecting_effort_metadata,
    get_new_status,
    create_activation,
    get_task_ids_by_criteria_name,
    get_all_tasks_under_account,
    get_first_prospecting_activity_date,
    get_qualifying_meeting,
    get_qualifying_opportunity,
    get_active_contact_ids,
    get_filtered_tasks_under_account,
    get_inbound_tasks_within_period,
)


async def find_unresponsive_activations(
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
    5. Returns a collection of activations that have been marked as unresponsive based on the lack of recent prospecting activity.

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
        unresponsive_activation_candidates = []
        candidate_account_ids = set()

        for activation in activations:
            if (
                add_days(
                    activation.last_prospecting_activity,
                    settings.inactivity_threshold,
                )
                < today
            ):
                unresponsive_activation_candidates.append(activation)
                candidate_account_ids.add(activation.account.id)

        if len(unresponsive_activation_candidates) == 0:
            response.data = []
            response.success = True
            return response

        ## not filtering by account ids because that would incur potentially large
        ## number of API calls given the need to batch to adhere to 16k uri limit
        async_response = (
            await fetch_prospecting_tasks_by_account_ids_from_date_not_in_ids(
                first_prospecting_activity,
                settings.criteria,
                [],
                get_team_member_salesforce_ids(settings),
            )
        )

        criteria_group_tasks_by_account_id = async_response.data

        # remove keys from criteria group that are not in candidates
        criteria_group_tasks_by_account_id = {
            account_id: tasks
            for account_id, tasks in criteria_group_tasks_by_account_id.items()
            if account_id in candidate_account_ids
        }

        activations_by_account_id = {
            activation.account.id: activation
            for activation in unresponsive_activation_candidates
        }

        account_ids_with_activity = set()
        for account_id, contacts_tasks in criteria_group_tasks_by_account_id.items():
            activation = activations_by_account_id.get(account_id)
            criteria_name_by_task_id = {}
            all_tasks = []

            for contact_id, criteria_tasks in contacts_tasks.items():
                for criteria, tasks in criteria_tasks.items():
                    for task in tasks:
                        try:
                            task_id = task.get("Id")
                            if task_id:
                                criteria_name_by_task_id[task_id] = criteria
                                all_tasks.append(task)
                            else:
                                print(
                                    f"Warning: Task without Id found for account {account_id}, contact {contact_id}"
                                )
                        except Exception as e:
                            set_context(
                                "problematic_task",
                                {
                                    "task": task,
                                    "account_id": account_id,
                                    "contact_id": contact_id,
                                    "criteria": criteria,
                                    "error": str(e),
                                    "error_type": type(e).__name__,
                                },
                            )
                            capture_exception(e)
                            print(f"Error processing task: {task}")
                            traceback.print_exc()
                            # Continue to the next task instead of raising
                            continue

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
                    account_ids_with_activity.add(account_id)
                    break

        activations_to_inactivate = [
            activation
            for activation in unresponsive_activation_candidates
            if activation.account.id not in account_ids_with_activity
        ]

        for activation in activations_to_inactivate:
            activation.status = StatusEnum.unresponsive

        response.data = activations_to_inactivate
        response.success = True
    except Exception as e:
        capture_exception(e)
        raise Exception(format_error_message(e))

    return response


async def increment_existing_activations(
    activations: List[Activation],
    settings: Settings,
    relevant_task_criteria: List[FilterContainer],
):
    response = ApiResponse(data=[], message="", success=False)
    try:
        today = date.today()
        salesforce_user_ids = get_team_member_salesforce_ids(settings)

        # must be UTC since that's how Salesforce will filter against Task CreatedDate
        benchmark_dt = convert_date_to_salesforce_datetime_format(
            settings.latest_date_queried
        )

        activations.sort(key=lambda x: x.last_prospecting_activity, reverse=True)
        account_ids = list(set(activation.account.id for activation in activations))
        already_counted_task_ids = set(
            task_id for activation in activations for task_id in activation.task_ids
        )

        async_response = (
            await fetch_prospecting_tasks_by_account_ids_from_date_not_in_ids(
                benchmark_dt,
                relevant_task_criteria,
                already_counted_task_ids,
                salesforce_user_ids,
            )
        )

        criteria_group_tasks_by_account_id = async_response.data
        # only keep account tasks which are a part of the activations we are incrementing
        criteria_group_tasks_by_account_id = {
            account_id: tasks
            for account_id, tasks in criteria_group_tasks_by_account_id.items()
            if account_id in account_ids
        }

        opportunities_by_account_id: List[Dict] = group_by(
            fetch_opportunities_by_account_ids_from_date(
                account_ids, benchmark_dt, salesforce_user_ids
            ).data,
            "AccountId",
        )

        meetings_by_account_id: Dict[str, List[Dict]] = (
            await get_meetings_by_account_id_via_activations(
                settings,
                activations,
                criteria_group_tasks_by_account_id,
                benchmark_dt,
                salesforce_user_ids,
            )
        )

        activations_by_account_id: Dict[str, Activation] = {
            activation.account.id: activation
            for activation in activations
            if activation.account.id in criteria_group_tasks_by_account_id
            or activation.account.id in opportunities_by_account_id
            or activation.account.id in meetings_by_account_id
        }

        criterion_by_name = {
            criterion.name: criterion for criterion in relevant_task_criteria
        }

        changed_activations = []

        for account_id, activation in activations_by_account_id.items():
            original_activation = Activation(**activation.to_dict())

            opportunities = opportunities_by_account_id.get(account_id, [])
            meetings = meetings_by_account_id.get(account_id, [])

            tasks_by_criteria_by_who_id = criteria_group_tasks_by_account_id.get(
                account_id, {}
            )

            tasks_by_criteria_name = {}
            for who_id, tasks_by_criteria in tasks_by_criteria_by_who_id.items():
                for criteria_name, tasks in tasks_by_criteria.items():
                    if criteria_name not in tasks_by_criteria_name:
                        tasks_by_criteria_name[criteria_name] = []
                    tasks_by_criteria_name[criteria_name].extend(tasks)

            all_tasks = [
                (task, criteria_name)
                for criteria_name, tasks in tasks_by_criteria_name.items()
                for task in tasks
            ]
            all_tasks.sort(key=lambda x: x[0]["CreatedDate"])

            current_prospecting_effort = (
                activation.prospecting_effort[-1]
                if activation.prospecting_effort
                else None
            )

            if not current_prospecting_effort:
                current_prospecting_effort = ProspectingEffort(
                    activation_id=activation.id,
                    prospecting_metadata=[],
                    status=activation.status,
                    date_entered=activation.activated_date,
                    task_ids=[],
                )
                activation.prospecting_effort.append(current_prospecting_effort)

            # Check if there are no tasks but opportunities or meetings exist
            if (not all_tasks or len(all_tasks) == 0) and (opportunities or meetings):
                # Update activation status based on opportunities and meetings
                if opportunities:
                    activation.status = StatusEnum.opportunity_created
                    activation.opportunity = convert_dict_to_opportunity(
                        opportunities[0]
                    )
                elif meetings and activation.status in [
                    StatusEnum.activated,
                    StatusEnum.engaged,
                ]:
                    activation.status = StatusEnum.meeting_set

                # Create a new prospecting effort
                new_pe = ProspectingEffort(
                    activation_id=activation.id,
                    prospecting_metadata=[],
                    status=activation.status,
                    date_entered=datetime.now().date(),
                    task_ids=[],
                )
                activation.prospecting_effort.append(new_pe)
                current_prospecting_effort = new_pe

                # Update event_ids if there are meetings
                if meetings:
                    if activation.event_ids is None:
                        activation.event_ids = set()
                    activation.event_ids.update(meeting["Id"] for meeting in meetings)

            else:
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
                    activation.tasks.append(task)
                    activation.last_prospecting_activity = max(
                        activation.last_prospecting_activity,
                        task_created_datetime.date(),
                    )
                    activation.active_contact_ids.add(task["WhoId"])
                    current_prospecting_effort.task_ids.add(task["Id"])

                    current_prospecting_effort = increment_prospecting_effort_metadata(
                        current_prospecting_effort, task, criteria_name
                    )

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
                        activation_metadata.task_ids.append(task["Id"])
                        activation_metadata.total += 1
                    else:
                        activation.prospecting_metadata.append(
                            ProspectingMetadata(
                                name=criteria_name,
                                first_occurrence=task_created_datetime.date(),
                                last_occurrence=task_created_datetime.date(),
                                task_ids=[task["Id"]],
                                total=1,
                            )
                        )

                    # Update engagement date if necessary
                    if not activation.engaged_date and (
                        criterion_by_name.get(criteria_name).name == "meetingsCriteria"
                        or criterion_by_name.get(criteria_name).direction.lower()
                        == "inbound"
                    ):
                        activation.engaged_date = task_created_datetime.date()

            # Update activation status and dates
            activation.status = current_prospecting_effort.status
            activation.days_activated = (today - activation.activated_date).days
            if activation.engaged_date:
                activation.days_engaged = (today - activation.engaged_date).days

            # Update opportunity if necessary
            activation.opportunity = (
                (
                    convert_dict_to_opportunity(opportunities[0])
                    if opportunities and len(opportunities) > 0
                    else None
                )
                if not original_activation.opportunity
                else original_activation.opportunity
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

            # Check if the activation has changed
            if activation != original_activation:
                changed_activations.append(activation)

        response.data = changed_activations
        response.success = True
    except Exception as e:
        raise Exception(format_error_message(e))

    return response


async def compute_activated_accounts(
    criteria_tasks_by_who_id_by_account_id, settings
) -> ApiResponse:
    """
    This function, `compute_activated_accounts`, is designed to process a collection of tasks, contacts, and settings to identify and construct activations for accounts.
    It aggregates tasks by account and contact, evaluates these tasks against a set of criteria defined in the settings, and determines whether an account has been activated within a specific tracking period.

    Parameters:
    - `criteria_tasks_by_who_id_by_account_id` (dict): A dictionary where each key represents a specific criteria name and each value is a list of task objects that meet that criteria.
    - `settings` (dict): A dictionary containing various settings that influence the activation computation. This includes:

    Returns:
    - `ApiResponse`: `data` parameter contains all activations and any relevant messages.
    """

    async def fetch_account_data(
        settings, criteria_tasks_by_who_id_by_account_id, first_prospecting_activity
    ):
        print("Fetching account data")
        salesforce_user_ids = get_team_member_salesforce_ids(settings)
        print("Fetching salesforce users")
        salesforce_user_by_id = group_by(
            fetch_salesforce_users(salesforce_user_ids).data, "id"
        )
        print("Fetching first prospecting activity date")
        first_prospecting_activity = get_first_prospecting_activity_date(
            criteria_tasks_by_who_id_by_account_id
        )
        print("Fetching opportunities by account id")
        opportunity_by_account_id = group_by(
            fetch_opportunities_by_account_ids_from_date(
                list(criteria_tasks_by_who_id_by_account_id.keys()),
                first_prospecting_activity,
                salesforce_user_ids,
            ).data,
            "AccountId",
        )

        print("Fetching meetings by account id")
        meetings_by_account_id = await get_meetings_by_account_id(
            settings,
            criteria_tasks_by_who_id_by_account_id,
            first_prospecting_activity,
            salesforce_user_ids,
        )
        print("Account data fetched successfully")
        return salesforce_user_by_id, opportunity_by_account_id, meetings_by_account_id

    response = ApiResponse(data=[], message="", success=True)

    try:
        print("Fetching account data")
        salesforce_user_by_id, opportunity_by_account_id, meetings_by_account_id = (
            await fetch_account_data(
                settings,
                criteria_tasks_by_who_id_by_account_id,
                get_first_prospecting_activity_date(
                    criteria_tasks_by_who_id_by_account_id
                ),
            )
        )

        print("Getting task ids by criteria name")
        task_ids_by_criteria_name = get_task_ids_by_criteria_name(
            criteria_tasks_by_who_id_by_account_id
        )
        for (
            account_id,
            tasks_by_criteria_by_who_id,
        ) in criteria_tasks_by_who_id_by_account_id.items():
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

                is_task_in_tracking_period = is_model_date_field_within_window(
                    sobject_model=task,
                    start_date=start_tracking_period,
                    period_days=settings.tracking_period,
                )

                # if the task is not in the tracking period, but was created before the start of the tracking period,
                # let's proceed until we find a task that is in the tracking period
                if (
                    not is_task_in_tracking_period
                    and parse_datetime_string_with_timezone(task.get("CreatedDate"))
                    < start_tracking_period
                ):
                    continue

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

                if is_task_in_tracking_period:
                    if task.get("WhoId") not in valid_task_ids_by_who_id:
                        valid_task_ids_by_who_id[task.get("WhoId")] = []
                    valid_task_ids_by_who_id[task.get("WhoId")].append(task.get("Id"))
                    last_valid_task_assignee_id = task.get("OwnerId")
                    task_ids.append(task.get("Id"))

                if not is_task_in_tracking_period:
                    try:
                        active_contact_ids = get_active_contact_ids(
                            valid_task_ids_by_who_id, settings.activities_per_contact
                        )
                        is_eligible_for_meeting_activation = (
                            qualifying_event and settings.activate_by_meeting
                        )
                        is_eligible_for_opportunity_activation = (
                            qualifying_opportunity and settings.activate_by_opportunity
                        )
                        is_account_active_for_tracking_period = len(
                            active_contact_ids
                        ) >= settings.contacts_per_account or (
                            len(task_ids) > 0
                            and (
                                is_eligible_for_meeting_activation
                                or is_eligible_for_opportunity_activation
                            )
                        )
                        if not is_account_active_for_tracking_period:
                            ## reset tracking

                            # if we found no valid tasks it means we just elapsed a tracking period
                            # without finding any outbound correspondence, so we don't have to increment
                            # by another {inactivity_threshold} days, we'll just take the very next Task
                            # and treat that as the start of the next tracking period
                            start_tracking_period = (
                                add_days(
                                    start_tracking_period,
                                    settings.tracking_period
                                    + settings.inactivity_threshold,
                                )
                                if len(task_ids) > 0
                                else parse_datetime_string_with_timezone(
                                    task.get("CreatedDate")
                                )
                            )
                            valid_task_ids_by_who_id.clear()
                            task_ids.clear()
                            if is_model_date_field_within_window(
                                task, start_tracking_period, settings.tracking_period
                            ):
                                valid_task_ids_by_who_id[task.get("WhoId")] = [
                                    task.get("Id")
                                ]
                                task_ids = [task.get("Id")]
                                last_valid_task_assignee_id = task.get("OwnerId")
                            continue

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

                        if not last_valid_task_assignee_id in salesforce_user_by_id:
                            for task in all_tasks_under_account:
                                if task.get("OwnerId") in salesforce_user_by_id:
                                    last_valid_task_assignee_id = task.get("OwnerId")
                                    break
                            else:
                                print(
                                    f"Warning: No valid Salesforce user found for account {account_id}"
                                )
                        if last_valid_task_assignee_id in salesforce_user_by_id:
                            outbound_tasks_in_tracking_period = [
                                task
                                for task in all_outbound_tasks_under_account
                                if task["Id"] in task_ids
                            ]
                            activation = create_activation(
                                account_first_prospecting_activity=parse_datetime_string_with_timezone(
                                    outbound_tasks_in_tracking_period[0]["CreatedDate"]
                                ).date(),
                                active_contact_ids=active_contact_ids,
                                last_valid_task_creator=salesforce_user_by_id.get(
                                    last_valid_task_assignee_id
                                )[0],
                                outbound_task_ids=task_ids,
                                qualifying_opportunity=qualifying_opportunity,
                                qualifying_event=qualifying_event,
                                task_ids_by_criteria_name=task_ids_by_criteria_name,
                                settings=settings,
                                outbound_tasks_under_account=outbound_tasks_in_tracking_period,
                                engaged_date=engaged_date,
                            )
                            activations.append(activation)
                            ## reset tracking period
                            start_tracking_period = add_days(
                                start_tracking_period,
                                settings.tracking_period
                                + settings.inactivity_threshold,
                            )
                            valid_task_ids_by_who_id.clear()
                            task_ids.clear()
                    except Exception as e:
                        set_context(
                            "activation_service.compute_activated_accounts",
                            {
                                "last_valid_task_assignee_id": last_valid_task_assignee_id,
                                "salesforce_user_by_id": salesforce_user_by_id,
                                "qualifying_event": qualifying_event,
                                "qualifying_opportunity": qualifying_opportunity,
                                "account_id": account_id,
                                "task": task,
                            },
                        )
                        raise e

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

            is_eligible_for_meeting_activation = (
                qualifying_event and settings.activate_by_meeting
            )
            is_eligible_for_opportunity_activation = (
                qualifying_opportunity and settings.activate_by_opportunity
            )
            is_account_active_for_tracking_period = len(
                active_contact_ids
            ) >= settings.contacts_per_account or (
                len(task_ids) > 0
                and (
                    is_eligible_for_meeting_activation
                    or is_eligible_for_opportunity_activation
                )
            )
            if is_account_active_for_tracking_period:

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
                try:
                    outbound_tasks_in_tracking_period = [
                        task
                        for task in all_outbound_tasks_under_account
                        if task["Id"] in task_ids
                    ]
                    activation = create_activation(
                        account_first_prospecting_activity=parse_datetime_string_with_timezone(
                            outbound_tasks_in_tracking_period[0]["CreatedDate"]
                        ).date(),
                        active_contact_ids=active_contact_ids,
                        last_valid_task_creator=salesforce_user_by_id.get(
                            last_valid_task_assignee_id
                        )[0],
                        outbound_task_ids=task_ids,
                        qualifying_opportunity=qualifying_opportunity,
                        qualifying_event=qualifying_event,
                        task_ids_by_criteria_name=task_ids_by_criteria_name,
                        settings=settings,
                        outbound_tasks_under_account=outbound_tasks_in_tracking_period,
                        engaged_date=engaged_date,
                    )
                    activations.append(activation)
                except Exception as e:
                    set_context(
                        "activation_service.compute_activated_accounts",
                        {
                            "last_valid_task_assignee_id": last_valid_task_assignee_id,
                            "salesforce_user_by_id": salesforce_user_by_id,
                            "qualifying_event": qualifying_event,
                            "qualifying_opportunity": qualifying_opportunity,
                            "account_id": account_id,
                            "task": task,
                        },
                    )
                    raise e

            response.data.extend(activations)

    except Exception as e:
        raise Exception(format_error_message(e))

    return response


# helpers with side effects


# Difference between this and get_meetings_by_account_id is that we cannot assume
# our contacts are already fetched and contained in the criteria_tasks_by_who_id_by_account_id map...
# it's meant to be used for the incrementation of activations already in our database
async def get_meetings_by_account_id_via_activations(
    settings: Settings,
    activations: list[Activation],
    criteria_tasks_by_who_id_by_account_id: Dict[str, Dict[str, List[Dict]]],
    first_prospecting_activity: datetime,
    salesforce_user_ids: list[str],
):
    meetings_by_account_id = {}

    if settings.meeting_object == "Event":

        contacts = await fetch_contacts_by_account_ids(
            list(set(activation.account.id for activation in activations))
        )
        contact_by_id = {contact.id: contact for contact in contacts}
        contact_ids = list(contact_by_id.keys())

        meetings_by_contact_id = fetch_events_by_contact_ids_from_date(
            contact_ids,
            first_prospecting_activity,
            salesforce_user_ids,
            settings.meetings_criteria,
        ).data

        for contact_id, meetings in meetings_by_contact_id.items():

            account_id = contact_by_id[contact_id].account_id
            if account_id not in meetings_by_account_id:
                meetings_by_account_id[account_id] = []

            meetings_by_account_id[account_id].extend(meetings)
    elif settings.meeting_object == "Task":
        for (
            account_id,
            criteria_tasks_by_who_id,
        ) in criteria_tasks_by_who_id_by_account_id.items():
            meetings_by_account_id[account_id] = []
            for who_id, criteria_tasks in criteria_tasks_by_who_id.items():
                for task in criteria_tasks.get(settings.meetings_criteria.name, []):
                    if (
                        task["CreatedDate"] >= first_prospecting_activity
                        and task["OwnerId"] in salesforce_user_ids
                    ):
                        meetings_by_account_id[account_id].append(task)

    return meetings_by_account_id


# Difference between this and get_meetings_by_account_id_via_activations is that this
# assumes its contacts are already fetched and contained in the criteria_tasks_by_who_id_by_account_id map...
# it's meant to be used for the initial creation of activations
async def get_meetings_by_account_id(
    settings: Settings,
    criteria_tasks_by_who_id_by_account_id: Dict[str, Dict[str, List[Dict]]],
    first_prospecting_activity: datetime,
    salesforce_user_ids: list[str],
):
    meetings_by_account_id = {}

    contacts: list[Contact] = extract_contacts_from_account_criteria_task_map(
        criteria_tasks_by_who_id_by_account_id
    )
    contact_by_id = {contact.id: contact for contact in contacts}
    if settings.meeting_object == "Event":
        contact_ids = list(contact_by_id.keys())

        meetings_by_contact_id = fetch_events_by_contact_ids_from_date(
            contact_ids,
            first_prospecting_activity,
            salesforce_user_ids,
            settings.meetings_criteria,
        ).data

        for contact_id, meetings in meetings_by_contact_id.items():
            if contact_id not in contact_by_id:
                continue

            account_id = contact_by_id[contact_id].account_id
            if account_id not in meetings_by_account_id:
                meetings_by_account_id[account_id] = []

            meetings_by_account_id[account_id].extend(meetings)
    elif settings.meeting_object == "Task":
        for (
            account_id,
            criteria_tasks_by_who_id,
        ) in criteria_tasks_by_who_id_by_account_id.items():
            meetings_by_account_id[account_id] = []
            for who_id, criteria_tasks in criteria_tasks_by_who_id.items():
                for task in criteria_tasks.get(settings.meetings_criteria.name, []):
                    if (
                        task["CreatedDate"] >= first_prospecting_activity
                        and task["OwnerId"] in salesforce_user_ids
                    ):
                        meetings_by_account_id[account_id].append(task)

    return meetings_by_account_id


def extract_contacts_from_account_criteria_task_map(
    criteria_tasks_by_who_id_by_account_id,
):
    contacts = []
    contact_ids = set()
    for account_tasks in criteria_tasks_by_who_id_by_account_id.values():
        for contact_id, criteria_tasks in account_tasks.items():
            if contact_id not in contact_ids:
                for tasks in criteria_tasks.values():
                    contact = tasks[0].get("Contact")
                    if contact and contact.id not in contact_ids:
                        contacts.append(contact)
                        contact_ids.add(contact.id)
                        break
    return contacts
