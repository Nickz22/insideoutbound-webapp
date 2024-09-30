import time
from datetime import datetime
from typing import List
import pytz

from app.services.activation_service import (
    compute_activated_accounts,
    increment_existing_activations,
    find_unresponsive_activations,
)
from app.salesforce_api import (
    fetch_prospecting_tasks_by_account_ids_from_date_not_in_ids,
)
from app.database.activation_selector import (
    load_active_activations_order_by_first_prospecting_activity_asc,
)
from app.database.settings_selector import load_settings
from app.database.dml import save_settings, upsert_activations_async  # Note the new import
from app.data_models import ApiResponse, FilterContainer, Settings
from app.utils import (
    add_days,
    get_team_member_salesforce_ids,
)
import asyncio


async def update_activation_states(user_timezone):
    api_response = ApiResponse(data=[], message="", success=False)

    settings = load_settings()
    salesforce_user_ids = get_team_member_salesforce_ids(settings)

    active_activations = (
        load_active_activations_order_by_first_prospecting_activity_asc().data
    )

    task_ids_to_exclude = []
    for activation in active_activations:
        task_ids_to_exclude.extend(activation.task_ids)

    unresponsive_activations = None
    if len(active_activations) > 0:
        async_response = await find_unresponsive_activations(
            active_activations, settings
        )
        unresponsive_activations = async_response.data

    if unresponsive_activations and len(unresponsive_activations) > 0:
        await upsert_activations_async(unresponsive_activations)

    active_activations = [
        a
        for a in active_activations
        if a.id not in [u.id for u in unresponsive_activations]
    ]

    relevant_task_criteria: List[FilterContainer] = settings.criteria
    if settings.meeting_object == "Task":
        relevant_task_criteria = settings.criteria + [settings.meetings_criteria]

    if len(active_activations) > 0:
        print("incrementing existing activations")
        async_response = await increment_existing_activations(
            active_activations, settings, relevant_task_criteria
        )
        incremented_activations = async_response.data
        print(f"upserting {len(incremented_activations)} incremented activations")
        await upsert_activations_async(incremented_activations)

    async_response = await fetch_prospecting_tasks_by_account_ids_from_date_not_in_ids(
        f"{get_threshold_date_for_activatable_tasks(settings)}T00:00:00Z",
        relevant_task_criteria,
        task_ids_to_exclude,
        salesforce_user_ids,
    )

    print("Tasks fetched and organized successfully")

    prospecting_tasks_by_criteria_name_by_account_id = async_response.data

    print("Computing activated accounts")
    async_response = await compute_activated_accounts(
        prospecting_tasks_by_criteria_name_by_account_id, settings
    )
    new_activations = async_response.data

    print(f" {len(new_activations)} new activations computed")

    if len(new_activations) > 0:
        print(f"Upserting {len(new_activations)} new activations")
        upsert_response = await upsert_activations_async(new_activations)
        if not upsert_response.success:
            print(f"Error upserting new activations: {upsert_response.message}")
            api_response.success = False
            api_response.message = f"Error upserting new activations: {upsert_response.message}"
            return api_response
        print("New activations upserted successfully")

    user_tz = pytz.timezone(user_timezone)
    settings.latest_date_queried = datetime.now(user_tz).strftime("%Y-%m-%d %H:%M:%S%z")
    save_settings(settings)

    api_response.success = True

    return api_response


# helpers


def get_threshold_date_for_activatable_tasks(settings: Settings):
    """
    Returns the threshold date for activatable tasks which is the last date
    we checked for activatable tasks minus the cooloff period and tracking period.

    i.e. Given an inactivity threshold of 30 days, and a tracking period of 10 days,
    if we check for Tasks today the Tasks that could activate our Account have to be created within the last 10 days...
    and any of those Tasks have to  be at least 30 days away from the last Task under the Account.
    So querying for the last 40 days of Tasks will enable our algorithm to find a Task created 29 days ago, determine that
    that single Task isn't sufficient to activate the Account, and then bump the activation window 30 days so that the `compute_activated_accounts` algorithm
    only activates based on Tasks created 30 days after the Task that was created 29 days ago.

    """
    return add_days(
        (settings.latest_date_queried or datetime.now()).date(),
        -(settings.inactivity_threshold + settings.tracking_period),
    )
