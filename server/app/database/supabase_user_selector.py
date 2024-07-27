import os
from supabase import create_client, Client
from app.data_models import AuthenticationError

url: str = os.environ.get("SUPABASE_URL")


def fetch_supabase_user_id(salesforce_id: str):
    try:
        # Use the service role key for this operation
        service_supabase = create_client(url, os.environ.get("SUPABASE_KEY"))

        # Fetch all users
        response = service_supabase.auth.admin.list_users()

        # Find the user with matching salesforce_id in user metadata
        for user in response:
            if (
                user.user_metadata
                and user.user_metadata.get("salesforce_id") == salesforce_id
            ):
                return user.id

        raise AuthenticationError(
            f"Could not find Supabase user with Salesforce ID: {salesforce_id}"
        )
    except Exception as e:
        raise AuthenticationError(f"Failed to fetch Supabase user ID: {str(e)}")
