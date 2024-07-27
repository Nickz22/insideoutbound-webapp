from flask import session
from app.database.supabase_connection import get_supabase_client
from app.data_models import Activation, Settings
from datetime import date
from app.middleware import authenticate
from app.mapper.mapper import python_activation_to_supabase_dict


@authenticate
def upsert_activations(new_activations: list[Activation]):
    try:
        supabase = get_supabase_client()
        for activation in new_activations:
            activation_dict = python_activation_to_supabase_dict(activation)
            activation_dict["activated_by_id"] = session["supabase_user_id"]
            # Upsert the activation
            result = supabase.table("Activations").upsert(activation_dict).execute()

            if result.get("error"):
                raise Exception(f"Error upserting activation: {result['error']}")

        return True
    except Exception as e:
        print(f"An error occurred: {e}")
        return False


@authenticate
def save_settings(settings: Settings):
    supabase = get_supabase_client()

    settings_dict = settings.__dict__

    # Convert date objects to ISO format strings
    for key, value in settings_dict.items():
        if isinstance(value, date):
            settings_dict[key] = value.isoformat()

    result = supabase.table("settings").upsert(settings_dict).execute()

    if result.get("error"):
        raise Exception(f"Error saving settings: {result['error']}")

    return True
