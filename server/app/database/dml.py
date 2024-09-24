import json
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from os import environ
from app.database.supabase_connection import (
    get_supabase_admin_client,
    get_session_state,
    set_session_state,
)
from app.data_models import (
    Activation,
    ApiResponse,
    Settings,
    UserModel,
    TokenData,
)
from app.mapper.mapper import (
    python_activation_to_supabase_dict,
    python_settings_to_supabase_dict,
    python_user_to_supabase_dict,
)
from app.utils import get_salesforce_team_ids, format_error_message
from app.database.settings_selector import load_settings

SUPABASE_ALL_USERS_PASSWORD = environ.get("SUPABASE_ALL_USERS_PASSWORD")
from datetime import datetime


def upsert_supabase_user(user: UserModel, is_sandbox: bool) -> str:
    try:
        salesforce_id = user.id
        supabase = get_supabase_admin_client()
        current_time = datetime.now().isoformat()

        # Query the User table to check if the row exists
        existing_user = (
            supabase.table("User")
            .select("*")  # Select all columns to get existing data
            .eq("salesforce_id", salesforce_id)
            .execute()
        )

        user_data = python_user_to_supabase_dict(user)
        user_data["is_sandbox"] = is_sandbox
        user_data["updated_at"] = current_time

        if not existing_user.data:
            # If the row does not exist, insert the new record
            user_id = str(uuid4())
            user_data["id"] = user_id
            user_data["created_at"] = current_time
            supabase.table("User").insert(user_data).execute()
        else:
            # If the row exists, update only non-null fields
            user_id = existing_user.data[0]["id"]
            existing_data = existing_user.data[0]

            # Merge existing data with new data, preferring non-null new values
            merged_data = {
                **existing_data,
                **{k: v for k, v in user_data.items() if v is not None and v is not ""},
            }

            # Ensure these fields are always updated
            merged_data["id"] = user_id
            merged_data["is_sandbox"] = is_sandbox
            merged_data["updated_at"] = current_time

            supabase.table("User").update(merged_data).eq("id", user_id).execute()

        return user_id

    except Exception as e:
        raise Exception(f"An error occurred upserting user: {e}")


def upsert_activations(new_activations: list[Activation]):
    api_response = ApiResponse(data=[], message="", success=False)
    supabase = get_supabase_admin_client()
    
    CHUNK_SIZE = 100
    
    for i in range(0, len(new_activations), CHUNK_SIZE):
        chunk = new_activations[i:i + CHUNK_SIZE]
        supabase_activations = [
            python_activation_to_supabase_dict(activation)
            for activation in chunk
        ]

        try:
            supabase.table("Activations").upsert(supabase_activations).execute()
        except Exception as e:
            api_response.message = f"Error upserting chunk {i//CHUNK_SIZE}: {str(e)}"
            return api_response

    api_response.success = True
    api_response.message = f"Successfully upserted {len(new_activations)} activations"
    return api_response


def delete_all_activations():
    try:
        team_member_ids = get_salesforce_team_ids(load_settings())
        supabase = get_supabase_admin_client()
        BATCH_SIZE = 100

        while True:
            # Fetch a batch of activation IDs to delete
            activations = supabase.table("Activations") \
                .select("id") \
                .in_("activated_by_id", team_member_ids) \
                .limit(BATCH_SIZE) \
                .execute()

            activation_ids = [activation['id'] for activation in activations.data]

            if not activation_ids:
                break  # No more activations to delete

            # Delete the fetched batch of activations
            supabase.table("Activations") \
                .delete() \
                .in_("id", activation_ids) \
                .execute()

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


def delete_session(session_token: str):
    supabase = get_supabase_admin_client()
    supabase.table("Session").delete().eq("id", session_token).execute()
    return True


def save_session(token_data: TokenData, is_sandbox: bool):
    ## TODO: change the invokers of save_session to provide a token_data every time
    if isinstance(token_data, dict):
        token_dict = token_data
    else:
        token_dict = token_data.to_dict()
    session_token = str(uuid4())
    salesforce_id = token_dict.get("id").split("/")[-1]
    org_id = token_dict.get("org_id")
    refresh_token = token_dict.get("refresh_token")
    session_state = {
        "salesforce_id": salesforce_id,
        "access_token": token_dict["access_token"],
        "refresh_token": refresh_token,
        "instance_url": token_dict["instance_url"],
        "org_id": org_id,
        "is_sandbox": is_sandbox,
    }
    set_session_state(session_state)
    # Store session data in Supabase
    now = datetime.now(timezone.utc).astimezone()
    session_data = {
        "id": session_token,
        "expiry": (now + timedelta(days=1)).isoformat(),
        "state": json.dumps(session_state),
    }
    supabase = get_supabase_admin_client()
    supabase.table("Session").insert(session_data).execute()
    return session_token
