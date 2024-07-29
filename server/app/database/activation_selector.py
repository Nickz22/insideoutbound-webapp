from typing import List
from app.data_models import Activation
from app.data_models import ApiResponse
from app.database.supabase_connection import get_supabase_user_client
from app.mapper.mapper import supabase_dict_to_python_activation


def load_active_activations_order_by_first_prospecting_activity_asc() -> ApiResponse:
    try:
        supabase_client = get_supabase_user_client()

        response = (
            supabase_client.table("Activations")
            .select("*")
            .neq("status", "Inactive")
            .order("first_prospecting_activity", desc=False)
            .execute()
        )

        activations: List[Activation] = []
        for row in response.data:
            activation = supabase_dict_to_python_activation(row)
            activations.append(activation)

        return ApiResponse(data=activations, success=True)
    except Exception as e:
        return ApiResponse(
            success=False, message=f"Failed to load activations: {str(e)}"
        )
