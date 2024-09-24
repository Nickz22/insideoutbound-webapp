from typing import List
from app.data_models import Activation
from app.data_models import ApiResponse
from app.database.supabase_connection import get_supabase_admin_client
from app.mapper.mapper import supabase_dict_to_python_activation
from app.database.settings_selector import load_settings
from app.utils import get_salesforce_team_ids, format_error_message

from app.database.supabase_retry import retry_on_temporary_unavailable

@retry_on_temporary_unavailable()
def load_active_activations_order_by_first_prospecting_activity_asc() -> ApiResponse:
    supabase_client = get_supabase_admin_client()
    team_member_ids = get_salesforce_team_ids(load_settings())

    page_size = 100  # Changed from 1000 to 100
    current_page = 0
    all_activations = []

    while True:
        response = (
            supabase_client.table("Activations")
            .select("*")
            .neq("status", "Unresponsive")
            .in_("activated_by_id", team_member_ids)
            .order("first_prospecting_activity", desc=False)
            .range(current_page * page_size, (current_page + 1) * page_size - 1)
            .execute()
        )

        if not response.data:
            break

        all_activations.extend(supabase_dict_to_python_activation(row) for row in response.data)
        current_page += 1

        if len(response.data) < page_size:
            break

    return ApiResponse(data=all_activations, success=True)


@retry_on_temporary_unavailable()
def load_inactive_activations() -> ApiResponse:
    try:
        supabase_client = get_supabase_admin_client()
        team_member_ids = get_salesforce_team_ids(load_settings())

        response = (
            supabase_client.table("Activations")
            .select("*")
            .eq("status", "Unresponsive")
            .in_("activated_by_id", team_member_ids)
            .execute()
        )

        activations: List[Activation] = []
        for row in response.data:
            activation = supabase_dict_to_python_activation(row)
            activations.append(activation)

        return ApiResponse(data=activations if activations else [], success=True)
    except Exception as e:
        error_msg = format_error_message(e)
        return ApiResponse(
            success=False, message=f"Failed to load activations: {str(error_msg)}"
        )
