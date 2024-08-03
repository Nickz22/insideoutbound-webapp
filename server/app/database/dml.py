from app.database.supabase_connection import (
    get_supabase_admin_client,
    get_session_state,
)
from app.data_models import Activation, ApiResponse, Settings, UserModel
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


def upsert_supabase_user(user: UserModel, org_id: str, is_sandbox: bool):

    try:
        salesforce_id = user.id
        email = user.email
        supabase = get_supabase_admin_client()
        user_id = str(uuid4())
        current_time = datetime.now().isoformat()

        # Query the User table to check if the row exists
        existing_user = (
            supabase.table("User")
            .select("id")
            .eq("salesforce_id", salesforce_id)
            .execute()
        )

        if not existing_user.data:
            # If the row does not exist, insert the new record
            supabase.table("User").insert(
                {
                    "id": user_id,
                    "salesforce_id": salesforce_id,
                    "email": email,
                    "photo_url": user.photoUrl,
                    "org_id": org_id,
                    "is_sandbox": is_sandbox,
                    "created_at": current_time,
                }
            ).execute()
        else:
            user_id = existing_user.data[0]["id"]

        return user_id

    except Exception as e:
        raise Exception(f"An error occurred upserting user: {e}")


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
