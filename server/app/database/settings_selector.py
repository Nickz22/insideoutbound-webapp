from app.database.supabase_connection import (
    get_supabase_admin_client,
    get_session_state,
)
from app.data_models import Settings
from app.mapper.mapper import supabase_dict_to_python_settings
from typing import Optional
from app.database.supabase_retry import retry_on_temporary_unavailable
from app.utils import log_message

@retry_on_temporary_unavailable()
def load_settings() -> Optional[Settings]:
    try:
        supabase = get_supabase_admin_client()
        salesforce_id = get_session_state()["salesforce_id"]
        result = (
            supabase.table("Settings")
            .select("*")
            .eq("salesforce_user_id", salesforce_id)
            .execute()
        )

        if result.data:
            settings_data = result.data[0]
            return supabase_dict_to_python_settings(settings_data)
        else:
            log_message("No settings found in the database.")
            return None
    except Exception as e:
        error_msg = f"Error fetching Settings from Supabase: {e}"
        log_message(msg=error_msg, exc_info=e, log_type="exception")
        raise Exception(error_msg)
