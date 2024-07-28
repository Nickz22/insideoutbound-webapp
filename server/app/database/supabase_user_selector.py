from app.database.supabase_connection import get_supabase_admin_client
from app.data_models import AuthenticationError


def fetch_supabase_user(salesforce_id: str):
    try:
        service_supabase = get_supabase_admin_client()

        # Fetch all users
        response = service_supabase.auth.admin.list_users()

        # Find the user with matching salesforce_id in user metadata
        for user in response:
            if (
                user.user_metadata
                and user.user_metadata.get("salesforce_id") == salesforce_id
            ):
                return user

        raise AuthenticationError(
            f"Could not find Supabase user with Salesforce ID: {salesforce_id}"
        )
    except Exception as e:
        raise AuthenticationError(f"Failed to fetch Supabase user ID: {str(e)}")
