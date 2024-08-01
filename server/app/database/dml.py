from app.database.supabase_connection import (
    get_supabase_admin_client,
    get_session_state,
)
from app.data_models import Activation, ApiResponse, Settings
from app.mapper.mapper import (
    python_activation_to_supabase_dict,
    python_settings_to_supabase_dict,
)
from datetime import datetime
from uuid import uuid4
from os import environ
from app.utils import get_salesforce_team_ids, format_error_message
from app.database.settings_selector import load_settings

SUPABASE_ALL_USERS_PASSWORD = environ.get("SUPABASE_ALL_USERS_PASSWORD")
from datetime import datetime


def insert_supabase_user(salesforce_id: str, email: str, org_id: str, is_sandbox: bool):
    # Initialize Supabase client with admin rights
    supabase = get_supabase_admin_client()

    try:
        # First, create the user in Supabase Auth
        user_response = supabase.auth.admin.create_user(
            {
                "email": email,
                "password": SUPABASE_ALL_USERS_PASSWORD,
                "email_confirm": True,  # This automatically confirms the email
                "user_metadata": {
                    "salesforce_id": salesforce_id,
                    "org_id": org_id,
                    "is_sandbox": is_sandbox,
                },
            }
        )

        user = user_response.user
        # If user creation is successful, add additional info to your custom Users table
        if user and user.id:
            supabase.table("User").insert(
                {
                    "id": user.id,  # Use the Supabase Auth user id
                    "salesforce_id": salesforce_id,
                    "email": email,
                    "org_id": org_id,
                    "is_sandbox": is_sandbox,
                    "created_at": datetime.now().isoformat(),
                }
            ).execute()

            print(f"User created successfully with id: {user.id}")
            return user.id
        else:
            raise Exception("User creation failed")

    except Exception as e:
        print(f"Error creating user: {str(e)}")
        return None


def upsert_activations(new_activations: list[Activation]):
    try:
        api_response = ApiResponse(data=[], message="", success=False)
        supabase = get_supabase_admin_client()
        session_state = get_session_state()
        supabase_activations = [
            {
                **python_activation_to_supabase_dict(activation),
                "activated_by_id": session_state["salesforce_id"],
            }
            for activation in new_activations
        ]

        supabase.table("Activations").upsert(supabase_activations).execute()
        api_response.success = True
    except Exception as e:
        error_msg = format_error_message(e)
        api_response.message = error_msg
        api_response.success = False
        print(f"An error occurred upserting activations: {error_msg}")
    return api_response


def delete_all_activations():
    try:
        team_member_ids = get_salesforce_team_ids(load_settings())
        supabase = get_supabase_admin_client()
        supabase.table("Activations").delete().in_(
            "activated_by_id", team_member_ids
        ).execute()
        return True
    except Exception as e:
        print(f"An error occurred: {e}")
        return False


def save_settings(settings: Settings):
    supabase = get_supabase_admin_client()

    settings_dict = python_settings_to_supabase_dict(settings)
    session_state = get_session_state()
    settings_dict["salesforce_user_id"] = session_state["salesforce_id"]

    if "id" not in settings_dict:
        settings_dict["id"] = str(uuid4())

    supabase.table("Settings").upsert(
        settings_dict, on_conflict=["salesforce_user_id"]
    ).execute()

    return True
