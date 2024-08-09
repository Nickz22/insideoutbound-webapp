from app.database.supabase_connection import get_supabase_admin_client
from app.data_models import AuthenticationError


def fetch_supabase_session(session_id: str):
    try:
        service_supabase = get_supabase_admin_client()

        # Query the Session table
        response = (
            service_supabase.table("Session").select("*").eq("id", session_id).execute()
        )

        # Check if a session was found
        if not response.data or len(response.data) == 0:
            raise AuthenticationError("Session not found")

        # Return the first (and should be only) session found
        return response.data[0]

    except Exception as e:
        # If it's already an AuthenticationError, re-raise it
        if isinstance(e, AuthenticationError):
            raise
        # For any other exception, wrap it in an AuthenticationError
        raise AuthenticationError(f"Error fetching session: {str(e)}")
