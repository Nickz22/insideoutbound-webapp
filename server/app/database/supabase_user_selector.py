from app.database.supabase_connection import get_supabase_admin_client
from app.data_models import AuthenticationError, UserModel
from app.mapper.mapper import supabase_user_to_python_user


def fetch_supabase_user(salesforce_id: str) -> UserModel:
    try:
        service_supabase = get_supabase_admin_client()

        # Query the User table for the specific salesforce_id
        response = (
            service_supabase.table("User")
            .select("*")
            .eq("salesforce_id", salesforce_id)
            .execute()
        )

        if response.data and len(response.data) > 0:
            supabase_user = response.data[0]
            return supabase_user_to_python_user(supabase_user)
        else:
            return None

    except Exception as e:
        raise AuthenticationError(f"Failed to fetch Supabase user: {str(e)}")
