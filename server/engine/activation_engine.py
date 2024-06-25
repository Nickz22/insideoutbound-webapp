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

        active_activations = (
            load_active_activations_order_by_first_prospecting_activity_asc().data
        )

        unresponsive_activations = None
        if len(active_activations) > 0:
            unresponsive_activations = find_unresponsive_activations(
                active_activations, settings
            ).data

        if unresponsive_activations and len(unresponsive_activations) > 0:
            upsert_activations(unresponsive_activations)

        active_activations = [
            a for a in active_activations if a.id not in unresponsive_activations
        ]

        if len(active_activations) > 0:
            activations = increment_existing_activations(
                active_activations, settings
            ).data
            upsert_activations(activations)

        last_task_date_with_cooloff_buffer = add_days(
            datetime.strptime(
                settings.latest_date_queried or datetime.now().strftime("%Y-%m-%d"),
                "%Y-%m-%d",
            ).date(),
            -(settings.cooloff_period + settings.tracking_period),
        )

        account_ids = pluck(active_activations, "account.id")

        account_contacts = (
            fetch_contacts_by_account_ids(account_ids).data
            if len(account_ids) > 0
            else ApiResponse(data=[], message="", success=True)
        )

        activated_account_contact_ids = pluck(account_contacts.data, "id")

        fetch_task_response = fetch_contact_tasks_by_criteria_from_date(
            settings.criteria,
            f"{last_task_date_with_cooloff_buffer}T00:00:00Z",
            (
                f"WHERE WhoId NOT IN ('{','.join(activated_account_contact_ids)}')"
                if len(activated_account_contact_ids) > 0
                else None
            ),
        ).data

        contact_ids = []
        for criteria_name in fetch_task_response:
            contact_ids.extend(pluck(fetch_task_response[criteria_name], WHO_ID))

        contacts = (
            fetch_contacts_by_ids(contact_ids).data
            if len(contact_ids) > 0
            else ApiResponse(data=[], message="", success=True)
        )

        new_activations = compute_activated_accounts(
            fetch_task_response, contacts, settings
        ).data

        upsert_activations(new_activations)

        today = datetime.now().date()
        settings.latest_date_queried = today.strftime("%Y-%m-%d")
        save_settings(settings)

        api_response.data = (
            load_active_activations_order_by_first_prospecting_activity_asc().data
        )
        api_response.success = True
    except Exception as e:
        raise Exception(format_error_message(e))

    return api_response
