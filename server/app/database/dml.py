from flask import session
from app.database.supabase_connection import get_supabase_client
from app.data_models import Activation, Settings
from app.middleware import authenticate
from app.mapper.mapper import (
    python_activation_to_supabase_dict,
    python_settings_to_supabase_dict,
)


@authenticate
def upsert_activations(new_activations: list[Activation]):
    try:
        supabase = get_supabase_client()
        supabase_activations = [
            {
                **python_activation_to_supabase_dict(activation),
                "activated_by_id": session["supabase_user_id"],
            }
            for activation in new_activations
        ]

        supabase.table("Activations").upsert(supabase_activations).execute()

        return True
    except Exception as e:
        print(f"An error occurred: {e}")
        return False


def save_settings(settings: Settings):
    supabase = get_supabase_client()

    settings_dict = python_settings_to_supabase_dict(settings)
    settings_dict["id"] = session["supabase_user_id"]
    supabase.table("Settings").upsert(settings_dict).execute()

    return True
