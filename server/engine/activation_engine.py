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

from constants import SESSION_EXPIRED, WHO_ID

from cache import save_settings

from models import ApiResponse
from cache import (
    load_settings,
    load_active_activations_order_by_first_prospecting_activity_asc,
    upsert_activations,
)
from utils import add_days, pluck, format_error_message
from datetime import datetime


def update_activation_states():
    api_response = ApiResponse(data=[], message="", success=False)

    try:
        settings = load_settings()

        activation_query_response = (
            load_active_activations_order_by_first_prospecting_activity_asc()
        )

        if not activation_query_response.success:
            api_response.message = activation_query_response.message
            return api_response

        active_activations = activation_query_response.data

        unresponsive_activations = []
        if len(active_activations) > 0:
            unresponsive_activations = find_unresponsive_activations(
                active_activations, settings
            )
            if not unresponsive_activations.success:
                api_response.message = unresponsive_activations.message
                return api_response

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

        account_contacts = fetch_contacts_by_account_ids(account_ids)

        if not account_contacts.success:
            api_response.message = account_contacts.message
            return api_response

        activated_account_contact_ids = pluck(account_contacts.data, "id")

        fetch_task_response = fetch_contact_tasks_by_criteria_from_date(
            settings["criteria"],
            f"{last_task_date_with_cooloff_buffer}T00:00:00Z",
            (
                f"WHERE WhoId NOT IN ('{','.join(activated_account_contact_ids)}')"
                if len(activated_account_contact_ids) > 0
                else None
            ),
        )

        if not fetch_task_response.success:
            api_response.message = fetch_task_response.message
            return api_response

        contact_ids = []
        for criteria_name in fetch_task_response.data:
            contact_ids.extend(pluck(fetch_task_response.data[criteria_name], WHO_ID))

        contacts = fetch_contacts_by_ids(contact_ids)

        if not contacts.success:
            api_response.message = contacts.message
            return api_response

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
            load_active_activations_order_by_first_prospecting_activity_asc().data
        )
        api_response.success = True
    except Exception as e:
        api_response.message = format_error_message(e)

    return api_response
