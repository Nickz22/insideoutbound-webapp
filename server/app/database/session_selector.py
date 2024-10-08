from app.database.supabase_connection import get_supabase_admin_client
from app.data_models import AuthenticationError, ApiResponse
import json
from app.database.supabase_retry import retry_on_temporary_unavailable


@retry_on_temporary_unavailable()
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


def fetch_session_by_salesforce_id(salesforce_id: str) -> ApiResponse:
    try:
        supabase = get_supabase_admin_client()

        # Query all sessions, ordered by expiry descending
        response = supabase.table("Session").select("*").order("expiry", desc=True).execute()

        if not response.data:
            return ApiResponse(success=False, message="No sessions found")

        # Filter sessions based on the salesforce_id in the state
        matching_session = next(
            (
                session
                for session in response.data
                if json.loads(session["state"]).get("salesforce_id") == salesforce_id
            ),
            None,
        )

        if matching_session:
            # Extract the state dict
            state_dict = json.loads(matching_session["state"])

            # Extract the refresh_token
            refresh_token = state_dict.get("refresh_token")

            return ApiResponse(
                success=True,
                data=[{"session": matching_session, "refresh_token": refresh_token}],
            )
        else:
            return ApiResponse(
                success=False,
                message=f"No session found for Salesforce ID: {salesforce_id}",
            )

    except Exception as e:
        return ApiResponse(success=False, message=f"Error fetching session: {str(e)}")
