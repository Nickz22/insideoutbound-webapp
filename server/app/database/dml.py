from flask import session
from app.database.supabase_connection import (
    get_supabase_user_client,
    get_supabase_admin_client,
    get_session_state,
)
from app.data_models import Activation, Settings
from app.middleware import authenticate
from app.mapper.mapper import (
    python_activation_to_supabase_dict,
    python_settings_to_supabase_dict,
)
from uuid import uuid4
from datetime import datetime

from os import environ

SUPABASE_ALL_USERS_PASSWORD = environ.get("SUPABASE_ALL_USERS_PASSWORD")

from supabase import create_client
from uuid import uuid4
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
        supabase = get_supabase_user_client()
        session_state = get_session_state()
        supabase_activations = [
            {
                **python_activation_to_supabase_dict(activation),
                "activated_by_id": session_state["supabase_user_id"],
            }
            for activation in new_activations
        ]

        supabase.table("Activations").upsert(supabase_activations).execute()

        return True
    except Exception as e:
        print(f"An error occurred: {e}")
        return False


def save_settings(settings: Settings):
    supabase = get_supabase_user_client()

    settings_dict = python_settings_to_supabase_dict(settings)
    session_state = get_session_state()

    settings_dict["id"] = session_state["supabase_user_id"]
    supabase.table("Settings").upsert(settings_dict).execute()

    return True
