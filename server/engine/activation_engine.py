import os, sys
from datetime import timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from server.models import ProcessResponse, Activation, Task, Account
from server.utils import generate_unique_id


def compute_activated_accounts(tasks_by_criteria, contacts, settings):
    response = ProcessResponse(data=[], message="", success=True)
    activities_per_contact = settings["activities_per_contact"]
    contacts_per_account = settings["contacts_per_account"]
    tracking_period = settings["tracking_period"]
    cooloff_period = settings["cooloff_period"]
    account_inactivity_threshold = settings["account_inactivity_threshold"]

    tasks_by_account = {}
    for criteria_key, tasks in tasks_by_criteria.items():
        for task in tasks:
            contact = contacts.get(task["who_id"])
            if not contact:
                response.message += f"Contact with id {task['who_id']} for Task with id {task['id']} not found. \n"
                continue
            account_id = contact["account_id"]
            if account_id not in tasks_by_account:
                tasks_by_account[account_id] = {}
            if task["who_id"] not in tasks_by_account[account_id]:
                tasks_by_account[account_id][task["who_id"]] = {}
            if criteria_key not in tasks_by_account[account_id][task["who_id"]]:
                tasks_by_account[account_id][task["who_id"]][criteria_key] = []
            tasks_by_account[account_id][task["who_id"]][criteria_key].append(task)

    for account_id, tasks_by_criteria_by_who_id in tasks_by_account.items():
        all_tasks_under_account = []
        task_ids_by_criteria_name = {}
        activations = []
        for contact_id, tasks_by_criteria in tasks_by_criteria_by_who_id.items():
            for criteria, tasks in tasks_by_criteria.items():
                if criteria not in task_ids_by_criteria_name:
                    task_ids_by_criteria_name[criteria] = set()
                all_tasks_under_account.extend(tasks)
                task_ids_by_criteria_name[criteria].update(
                    [task["id"] for task in tasks]
                )

        if len(all_tasks_under_account) < (
            activities_per_contact * contacts_per_account
        ):
            continue

        # although the Task API query is sorted already, grouping them potentially breaks a perfect sort
        ## so we'll sort again here to be safe...opportunity for optimization
        all_tasks_under_account = sorted(
            all_tasks_under_account, key=lambda x: x["created_date"]
        )

        start_tracking_period = all_tasks_under_account[0]["created_date"]
        valid_task_ids_by_who_id = {}
        for task in all_tasks_under_account:
            if not is_within_period(task, start_tracking_period, tracking_period):
                active_contact_ids = []
                for who_id, valid_task_ids in valid_task_ids_by_who_id.items():
                    is_contact_active = len(valid_task_ids) >= activities_per_contact
                    if is_contact_active:
                        active_contact_ids.append(who_id)
                is_account_active_for_tracking_period = (
                    len(active_contact_ids) >= contacts_per_account
                )
                if not is_account_active_for_tracking_period:
                    start_tracking_period = add_days(
                        start_tracking_period, tracking_period + cooloff_period
                    )
                    valid_task_ids_by_who_id = {}
                    if is_within_period(task, start_tracking_period, tracking_period):
                        valid_task_ids_by_who_id[task["who_id"]] = [task["id"]]
                    continue

                # Can add Prospecting Metadata by
                # finding Task Ids within task_ids_by_criteria_name
                activations.append(
                    Activation(
                        id=generate_unique_id(),
                        account=Account(
                            name=contacts[active_contact_ids[0]]["account"]["name"],
                            id=account_id,
                        ),
                        activated_date=task["created_date"],
                        active_contacts=len(active_contact_ids),
                        last_prospecting_activity=task["created_date"],
                    )
                )
                # ensure that no Task within account_inactivity_threshold before incrementing start_tracking_period to the next period

            if task["who_id"] not in valid_task_ids_by_who_id:
                valid_task_ids_by_who_id[task["who_id"]] = []
            valid_task_ids_by_who_id[task["who_id"]].append(task["id"])

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
                    name=contacts[active_contact_ids[0]]["account"]["name"],
                    id=account_id,
                ),
                activated_date=task["created_date"],
                active_contacts=len(active_contact_ids),
                last_prospecting_activity=task["created_date"],
            )
        )

        response.data.extend(activations)

    return response


# helpers
def filter_tasks_within_period(tasks, start_date, period_days):
    end_date = start_date + timedelta(days=period_days)
    return [task for task in tasks if start_date <= Task["created_date"] <= end_date]


def add_days(date, days):
    return date + timedelta(days=days)


def is_within_period(task, start_date, period_days):
    end_date = start_date + timedelta(days=period_days)
    return start_date <= task["created_date"] <= end_date


def filter_tasks_outside_cooloff(tasks, reference_date, cooloff_days):
    cooloff_date = reference_date - timedelta(days=cooloff_days)
    return [
        task
        for task in tasks
        if Task["created_date"] < cooloff_date or Task["created_date"] > reference_date
    ]
