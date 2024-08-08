from server.app.database.supabase_connection import get_supabase_admin_client
from server.app.data_models import AuthenticationError


def fetch_supabase_user(salesforce_id: str):
    try:
        service_supabase = get_supabase_admin_client()

        # Fetch all users
        response = service_supabase.auth.admin.list_users()
        supabase_user = None
        # Find the user with matching salesforce_id in user metadata
        for user in response:
            if (
                user.user_metadata
                and user.user_metadata.get("salesforce_id") == salesforce_id
            ):
                supabase_user = user

        return supabase_user
    except Exception as e:
        raise AuthenticationError(f"Failed to fetch Supabase user ID: {str(e)}")
