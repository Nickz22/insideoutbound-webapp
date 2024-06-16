import os, sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from server.api.salesforce import (
    fetch_tasks_by_account_ids_from_date_not_in_ids,
    fetch_opportunities_by_account_ids_from_date,
    fetch_events_by_account_ids_from_date,
)
from server.models import ProcessResponse, Activation, Account
from server.utils import (
    generate_unique_id,
    add_days,
    is_model_created_within_period,
    group_by,
    pluck,
)
from datetime import datetime


def find_unresponsive_activations(activations, settings):
    first_prospecting_activity = activations[0].first_prospecting_activity
    activations.sort(key=lambda x: x.last_prospecting_activity, reverse=True)

    # find activations where last_prospecting_activity + settings["account_inactivity_threshold"] < today
    today = datetime.now().date()
    unresponsive_activation_candidates = [
        activation
        for activation in activations
        if add_days(
            activation.last_prospecting_activity,
            settings["account_inactivity_threshold"],
        )
        < today
    ]

    latest_task_to_be_evaluated = add_days(
        unresponsive_activation_candidates[0].last_prospecting_activity,
        settings["account_inactivity_threshold"],
    )
    account_ids = pluck(unresponsive_activation_candidates, "account.id")
    already_counted_task_ids = [
        task_id
        for activation in unresponsive_activation_candidates
        for task_id in activation.task_ids
    ]
    criteria_group_tasks_by_account_id = (
        fetch_tasks_by_account_ids_from_date_not_in_ids(
            account_ids,
            first_prospecting_activity,
            settings["criteria"],
            already_counted_task_ids,
        )
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
                criteria_name_by_task_id[task.id] = criteria
                all_tasks.append(task)

        found_prospecting_activity = False
        for task in all_tasks:
            is_task_within_inactivity_threshold = is_model_created_within_period(
                task,
                activation.last_prospecting_activity,
                settings["account_inactivity_threshold"],
            )
            if is_task_within_inactivity_threshold:
                found_prospecting_activity = True
                break

        if not found_prospecting_activity:
            activation.status = "Unresponsive"
            activations_by_account_id[account_id] = activation

    return activations_by_account_id.values()


def increment_existing_activations(activations, settings):
    """
    expects activations sorted by first_prospecting_activity
    """
    first_prospecting_activity = activations[0].first_prospecting_activity
    activations.sort(key=lambda x: x.last_prospecting_activity, reverse=True)
    account_ids = pluck(activations, "account.id")
    already_counted_task_ids = [
        task_id for activation in activations for task_id in activation.task_ids
    ]
    criteria_group_tasks_by_account_id = (
        fetch_tasks_by_account_ids_from_date_not_in_ids(
            account_ids,
            first_prospecting_activity,
            settings["criteria"],
            already_counted_task_ids,
        )
    )
    opportunities = fetch_opportunities_by_account_ids_from_date(
        account_ids, first_prospecting_activity
    )
    events_by_account_id = fetch_events_by_account_ids_from_date(
        account_ids, first_prospecting_activity
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
                criteria_name_by_task_id[task.id] = criteria
                all_tasks.append(task)

        # opportunity for merge sort implementation
        all_tasks = sorted(all_tasks, key=lambda x: x.created_date)
        for task in all_tasks:
            is_task_within_inactivity_threshold = is_model_created_within_period(
                task,
                activation.last_prospecting_activity,
                settings["account_inactivity_threshold"],
            )
            if not is_task_within_inactivity_threshold:
                break
            activation.task_ids.add(task.id)
            activation.last_prospecting_activity = task.created_date
            activation.active_contact_ids.add(task.who_id)
            activations_by_account_id[account_id] = activation
            # rollup prospecting metadata via criteria_name_by_task_id

    opportunities_by_account_id = group_by(opportunities, "account_id")

    for account_id in activations_by_account_id:
        activation = activations_by_account_id[account_id]
        opportunities = opportunities_by_account_id.get(account_id, [])
        events = events_by_account_id.get(account_id, [])

        if events:
            for event in events:
                if (
                    is_model_created_within_period(
                        event,
                        activation.first_prospecting_activity,
                        settings["account_inactivity_threshold"],
                    )
                    and activation.status == "Activated"
                ):
                    activation.status = "Meeting Set"
                    break

        if opportunities:
            for opportunity in opportunities:
                if is_model_created_within_period(
                    opportunity,
                    activation.first_prospecting_activity,
                    settings["account_inactivity_threshold"],
                ) and activation.status in ["Activated", "Meeting Set"]:
                    activation.opportunity = opportunities[0]
                    activation.status = "Opportunity Created"
                    break

        activations_by_account_id[account_id] = activation

    return activations_by_account_id.values()


def compute_activated_accounts(tasks_by_criteria, contacts, settings):
    response = ProcessResponse(data=[], message="", success=True)
    activities_per_contact = settings["activities_per_contact"]
    contacts_per_account = settings["contacts_per_account"]
    tracking_period = settings["tracking_period"]
    cooloff_period = settings["cooloff_period"]

    tasks_by_account = {}
    contact_by_id = {contact.id: contact for contact in contacts}
    first_prospecting_activity = None
    for criteria_key, tasks in tasks_by_criteria.items():
        for task in tasks:
            first_prospecting_activity = (
                task.created_date
                if not first_prospecting_activity
                else min(first_prospecting_activity, task.created_date)
            )
            contact = contact_by_id.get(task.who_id)
            if not contact:
                response.message += f"Contact with id {task.who_id} for Task with id {task.id} not found. \n"
                continue
            account_id = contact.account_id
            if account_id not in tasks_by_account:
                tasks_by_account[account_id] = {}
            if task.who_id not in tasks_by_account[account_id]:
                tasks_by_account[account_id][task.who_id] = {}
            if criteria_key not in tasks_by_account[account_id][task.who_id]:
                tasks_by_account[account_id][task.who_id][criteria_key] = []
            tasks_by_account[account_id][task.who_id][criteria_key].append(task)

    opportunity_by_account_id = group_by(
        fetch_opportunities_by_account_ids_from_date(
            tasks_by_account.keys(), first_prospecting_activity
        ),
        "account_id",
    )
    events_by_account_id = fetch_events_by_account_ids_from_date(
        tasks_by_account.keys(), first_prospecting_activity
    )
    for account_id, tasks_by_criteria_by_who_id in tasks_by_account.items():
        all_tasks_under_account = []
        task_ids_by_criteria_name = {}
        activations = []

        for contact_id, tasks_by_criteria in tasks_by_criteria_by_who_id.items():
            for criteria, tasks in tasks_by_criteria.items():
                if criteria not in task_ids_by_criteria_name:
                    task_ids_by_criteria_name[criteria] = set()
                all_tasks_under_account.extend(tasks)
                task_ids_by_criteria_name[criteria].update([task.id for task in tasks])

        if len(all_tasks_under_account) == 0:
            continue

        # refactor Activation creation to use a helper
        # if Activating via activities, set the status,opp,meeting accordingly if one exists within the tracking period
        # if deferring activity activation, check if there is an opp,meeting within the tracking period, activate if so

        # although the Task API query is sorted already, grouping them potentially breaks a perfect sort
        ## so we'll sort again here to be safe...opportunity for optimization
        all_tasks_under_account = sorted(
            all_tasks_under_account, key=lambda x: x.created_date
        )

        start_tracking_period = all_tasks_under_account[0].created_date

        qualifying_event = None
        for event in events_by_account_id.get(account_id, []):
            if is_model_created_within_period(
                event, start_tracking_period, tracking_period
            ):
                qualifying_event = event
                break

        qualifying_opportunity = None
        for opportunity in opportunity_by_account_id.get(account_id, []):
            if is_model_created_within_period(
                opportunity, start_tracking_period, tracking_period
            ):
                qualifying_opportunity = opportunity
                break

        valid_task_ids_by_who_id = {}
        task_ids = []

        # track first prospecting activity for the current tracking period
        first_prospecting_activity = None
        for task in all_tasks_under_account:

            if not is_model_created_within_period(
                task, start_tracking_period, tracking_period
            ):
                active_contact_ids = []
                for who_id, valid_task_ids in valid_task_ids_by_who_id.items():
                    is_contact_active = len(valid_task_ids) >= activities_per_contact
                    if is_contact_active:
                        active_contact_ids.append(who_id)

                is_account_active_for_tracking_period = (
                    len(active_contact_ids) >= contacts_per_account
                    or qualifying_event
                    or qualifying_opportunity
                )
                if not is_account_active_for_tracking_period:
                    start_tracking_period = add_days(
                        start_tracking_period, tracking_period + cooloff_period
                    )
                    valid_task_ids_by_who_id = {}
                    first_prospecting_activity = None
                    task_ids = []
                    if is_model_created_within_period(
                        task, start_tracking_period, tracking_period
                    ):
                        valid_task_ids_by_who_id[task.who_id] = [task.id]
                        first_prospecting_activity = task.created_date
                        task_ids = [task.id]
                    continue

                # Can add Prospecting Metadata by
                # finding Task Ids within task_ids_by_criteria_name
                activations.append(
                    Activation(
                        id=generate_unique_id(),
                        account=Account(
                            name=contacts[active_contact_ids[0]].account.name,
                            id=account_id,
                        ),
                        activated_date=first_prospecting_activity,
                        active_contact_ids=set(active_contact_ids),
                        last_prospecting_activity=task.created_date,
                        first_prospecting_activity=first_prospecting_activity,
                        task_ids=task_ids,
                        opportunity=qualifying_opportunity,
                        event_ids=(
                            set(qualifying_event.id) if qualifying_event else None
                        ),
                        status=(
                            "Opportunity Created"
                            if qualifying_opportunity
                            else "Meeting Set" if qualifying_event else "Activated"
                        ),
                    )
                )
                # ensure that no Task within account_inactivity_threshold before incrementing start_tracking_period to the next period

            if task.who_id not in valid_task_ids_by_who_id:
                valid_task_ids_by_who_id[task.who_id] = []
                first_prospecting_activity = task.created_date
            valid_task_ids_by_who_id[task.who_id].append(task.id)
            task_ids.append(task.id)

        # this account's tasks have ended, check for activation
        active_contact_ids = []
        for who_id, valid_task_ids in valid_task_ids_by_who_id.items():
            is_contact_active = len(valid_task_ids) >= activities_per_contact
            if is_contact_active:
                active_contact_ids.append(who_id)
        is_account_active_for_tracking_period = (
            len(active_contact_ids) >= contacts_per_account
        )
        if not is_account_active_for_tracking_period:
            continue

        # Can add Prospecting Metadata by
        activations.append(
            Activation(
                id=generate_unique_id(),
                account=Account(
                    name=contact_by_id.get(active_contact_ids[0]).account.name,
                    id=account_id,
                ),
                activated_date=first_prospecting_activity,
                active_contact_ids=set(active_contact_ids),
                last_prospecting_activity=task.created_date,
                opportunity=qualifying_opportunity,
                event_ids=(set(qualifying_event.id) if qualifying_event else None),
                status=(
                    "Opportunity Created"
                    if qualifying_opportunity
                    else "Meeting Set" if qualifying_event else "Activated"
                ),
            )
        )

        response.data.extend(activations)

    return response
