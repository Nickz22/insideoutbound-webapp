from datetime import datetime

from app.services.activation_service import (
    compute_activated_accounts,
    increment_existing_activations,
    find_unresponsive_activations,
)
from server.app.salesforce_api import (
    fetch_criteria_tasks_by_account_ids_from_date,
    fetch_accounts_not_in_ids,
    fetch_contacts_by_ids_and_non_null_accounts,
)
from app.constants import WHO_ID
from server.app.database.activation_selector import (
    load_active_activations_order_by_first_prospecting_activity_asc,
)
from app.middleware import authenticate
from server.app.database.settings_selector import load_settings
from server.app.database.dml import upsert_activations, save_settings
from app.data_models import ApiResponse, Settings
from app.utils import (
    add_days,
    pluck,
    format_error_message,
    get_team_member_salesforce_ids,
)


@authenticate
def update_activation_states():
    api_response = ApiResponse(data=[], message="", success=False)

    try:

        settings = load_settings()
        salesforce_user_ids = get_team_member_salesforce_ids(settings)

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
            incremented_activations = increment_existing_activations(
                active_activations, settings
            ).data
            upsert_activations(incremented_activations)

        active_account_ids = list(pluck(active_activations, "account.id"))
        activatable_account_ids = list(
            pluck(fetch_accounts_not_in_ids(active_account_ids).data, "id")
        )

        tasks_by_filter_name = fetch_criteria_tasks_by_account_ids_from_date(
            activatable_account_ids,
            f"{get_threshold_date_for_activatable_tasks(settings)}T00:00:00Z",
            settings.criteria,
            salesforce_user_ids,
        ).data

        contact_ids = set()
        for criteria_name in tasks_by_filter_name:
            contact_ids.update(pluck(tasks_by_filter_name[criteria_name], WHO_ID))

        contacts = (
            fetch_contacts_by_ids_and_non_null_accounts(list(contact_ids)).data
            if len(contact_ids) > 0
            else []
        )

        new_activations = compute_activated_accounts(
            tasks_by_filter_name, contacts, settings
        ).data

        upsert_activations(new_activations)

        today = datetime.now().date()
        settings.latest_date_queried = datetime.strptime(
            today.strftime("%Y-%m-%d"), "%Y-%m-%d"
        ).date()
        save_settings(settings)

        api_response.data = (
            load_active_activations_order_by_first_prospecting_activity_asc().data
        )
        api_response.success = True
    except Exception as e:
        raise Exception(format_error_message(e))

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
