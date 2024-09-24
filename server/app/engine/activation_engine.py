import time
from datetime import datetime

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
from app.database.dml import upsert_activations, save_settings
from app.data_models import ApiResponse, Settings
from app.utils import (
    add_days,
    get_team_member_salesforce_ids,
)
import asyncio


async def update_activation_states():
    api_response = ApiResponse(data=[], message="", success=False)

    settings = load_settings()
    salesforce_user_ids = get_team_member_salesforce_ids(settings)

    active_activations = (
        load_active_activations_order_by_first_prospecting_activity_asc().data
    )

    unresponsive_activations = None
    if len(active_activations) > 0:
        async_response = await find_unresponsive_activations(
            active_activations, settings
        )
        unresponsive_activations = async_response.data

    if unresponsive_activations and len(unresponsive_activations) > 0:
        upsert_activations(unresponsive_activations)

    active_activations = [
        a
        for a in active_activations
        if a.id not in [u.id for u in unresponsive_activations]
    ]

    if len(active_activations) > 0:
        async_response = await increment_existing_activations(
            active_activations, settings
        )
        incremented_activations = async_response.data
        upsert_activations(incremented_activations)

    relevant_task_criteria = settings.criteria
    if settings.meeting_object == "Task":
        relevant_task_criteria = settings.criteria + [settings.meetings_criteria]
    async_response = await fetch_prospecting_tasks_by_account_ids_from_date_not_in_ids(
        f"{get_threshold_date_for_activatable_tasks(settings)}T00:00:00Z",
        relevant_task_criteria,
        [],
        salesforce_user_ids,
    )

    print("Tasks fetched and organized successfully")

    prospecting_tasks_by_criteria_name_by_account_id = async_response.data

    print("Computing activated accounts")
    async_response = await compute_activated_accounts(
        prospecting_tasks_by_criteria_name_by_account_id, settings
    )
    new_activations = async_response.data

    print("New activations computed")

    if len(new_activations) > 0:
        upsert_activations(new_activations)

    print("New activations upserted")

    settings.latest_date_queried = time.strftime("%Y-%m-%d %H:%M:%S%z", time.gmtime())
    save_settings(settings)

    api_response.data = (
        load_active_activations_order_by_first_prospecting_activity_asc().data
    )
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
