from services.activation_service import (
    compute_activated_accounts,
    increment_existing_activations,
    find_unresponsive_activations,
)

from api.salesforce import (
    fetch_contact_tasks_by_criteria_from_date,
    fetch_contacts_by_account_ids,
    fetch_contacts_by_ids,
)

from constants import MISSING_ACCESS_TOKEN, WHO_ID

from cache import save_settings

from models import ApiResponse
from cache import (
    load_settings,
    load_active_activations_order_by_first_prospecting_activity_asc,
    upsert_activations,
)
from utils import add_days, pluck
from datetime import datetime


def update_activation_states():
    api_response = ApiResponse(data=[], message="", success=False)
    settings = load_settings()
    active_activations = (
        load_active_activations_order_by_first_prospecting_activity_asc()
    )

    unresponsive_activations = []
    if len(active_activations) > 0:
        unresponsive_activations = find_unresponsive_activations(
            active_activations, settings
        )

    if len(unresponsive_activations) > 0:
        upsert_activations(unresponsive_activations)

    active_activations = [
        a for a in active_activations if a.id not in unresponsive_activations
    ]
    
    if len(active_activations) > 0:
        activations = increment_existing_activations(active_activations, settings)
        upsert_activations(activations)

    last_task_date_with_cooloff_buffer = add_days(
        datetime.strptime(settings["latest_date_queried"], "%Y-%m-%d").date(),
        -(settings["cooloff_period"] + settings["tracking_period"]),
    )

    account_ids = pluck(active_activations, "account.id")
    activated_account_contact_ids = pluck(
        fetch_contacts_by_account_ids(account_ids).data, "id"
    )

    fetch_task_response = fetch_contact_tasks_by_criteria_from_date(
        settings["criteria"],
        f"{last_task_date_with_cooloff_buffer}T00:00:00Z",
        f"WHERE WhoId NOT IN ('{','.join(activated_account_contact_ids)}')" if len(activated_account_contact_ids) > 0 else None,
    )

    if (
        fetch_task_response.message == MISSING_ACCESS_TOKEN
        or "session expired" in fetch_task_response.message.lower()
    ):
        api_response.message = MISSING_ACCESS_TOKEN
        return api_response

    if not fetch_task_response.success:
        return fetch_task_response

    contact_ids = []
    for criteria_name in fetch_task_response.data:
        contact_ids.extend(pluck(fetch_task_response.data[criteria_name], WHO_ID))

    contacts = fetch_contacts_by_ids(contact_ids)
    activation_response = compute_activated_accounts(
        fetch_task_response.data, contacts.data, settings
    )

    if not activation_response.success:
        api_response.message = activation_response.message
        return api_response

    upsert_activations(activation_response.data)

    today = datetime.now().date()
    settings["latest_date_queried"] = today.strftime("%Y-%m-%d")
    save_settings(settings)

    api_response.data = (
        load_active_activations_order_by_first_prospecting_activity_asc()
    )
    api_response.success = True
    return api_response
