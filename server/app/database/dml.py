import json
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from os import environ
from app.database.supabase_connection import (
    get_supabase_admin_client,
    get_session_state,
    get_supabase_key,
    set_session_state,
    get_supabase_url
)
from app.data_models import (
    Activation,
    ApiResponse,
    SessionState,
    Settings,
    UserModel,
    TokenData,
)
from app.mapper.mapper import (
    python_activation_to_supabase_dict,
    python_settings_to_supabase_dict,
    python_user_to_supabase_dict,
)
from app.utils import get_salesforce_team_ids, log_error
from app.database.settings_selector import load_settings
import asyncio
import aiohttp
from typing import List

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
    

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

async def upsert_activations_async(new_activations: List[Activation]):
    api_response = ApiResponse(data=[], message="", success=False)
    CHUNK_SIZE = 50
    MAX_CONCURRENT_REQUESTS = 5
    MAX_RETRIES = 3

    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError))
    )
    async def upsert_chunk(session, chunk):
        if not chunk:  # Skip empty chunks
            return None
        
        ## we need clean JSON in Supabase so that we can filter jsonb fields
        def parse_json_fields(activation):
            json_fields = ['account', 'active_contacts', 'tasks', 'prospecting_metadata', 'prospecting_effort']
            for field in json_fields:
                if field in activation and isinstance(activation[field], str):
                    try:
                        activation[field] = json.loads(activation[field])
                    except json.JSONDecodeError:
                        print(f"Warning: Failed to parse JSON for field {field}")
            return activation

        supabase_activations = [parse_json_fields(python_activation_to_supabase_dict(activation)) for activation in chunk]
        
        url = f"{get_supabase_url()}/rest/v1/Activations"
        headers = {
            "apikey": get_supabase_key(),
            "Authorization": f"Bearer {get_supabase_key()}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates"
        }
        async with session.post(url, json=supabase_activations, headers=headers, timeout=30) as response:
            if response.status != 201 and response.status != 200:
                raise aiohttp.ClientResponseError(
                    response.request_info,
                    response.history,
                    status=response.status,
                    message=f"Error upserting chunk: {await response.text()}"
                )
        return None

    async with aiohttp.ClientSession() as session:
        chunks = [new_activations[i:i+CHUNK_SIZE] for i in range(0, len(new_activations), CHUNK_SIZE)]
        
        for i in range(0, len(chunks), MAX_CONCURRENT_REQUESTS):
            batch = chunks[i:i+MAX_CONCURRENT_REQUESTS]
            try:
                results = await asyncio.gather(*[upsert_chunk(session, chunk) for chunk in batch])
                errors = [r for r in results if r is not None]
                if errors:
                    api_response.message = "\n".join(errors)
                    log_error(Exception(api_response.message))
                    return api_response
            except Exception as e:
                api_response.message = f"Error processing batch: {str(e)}"
                log_error(e)
                return api_response

    api_response.success = True
    api_response.message = f"Successfully upserted {len(new_activations)} activations"
    return api_response


async def delete_all_activations_async():
    try:
        team_member_ids = get_salesforce_team_ids(load_settings())
        supabase = get_supabase_admin_client()
        BATCH_SIZE = 100
        MAX_CONCURRENT_REQUESTS = 10

        # Fetch all matching activation IDs
        all_activations = supabase.table("Activations") \
            .select("id") \
            .in_("activated_by_id", team_member_ids) \
            .execute()

        all_activation_ids = [activation['id'] for activation in all_activations.data]

        if not all_activation_ids:
            return True  # No activations to delete

        async def delete_batch(session: aiohttp.ClientSession, batch: List[str]):
            url = f"{get_supabase_url()}/rest/v1/Activations"
            headers = {
                "apikey": get_supabase_key(),
                "Authorization": f"Bearer {get_supabase_key()}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal"
            }
            params = {"id": f"in.({','.join(batch)})"}
            async with session.delete(url, headers=headers, params=params) as response:
                if response.status != 200 and response.status != 204:
                    return f"Error deleting batch with status {response.status}: {await response.text()}"
            return None

        async with aiohttp.ClientSession() as session:
            batches = [all_activation_ids[i:i+BATCH_SIZE] for i in range(0, len(all_activation_ids), BATCH_SIZE)]
            
            for i in range(0, len(batches), MAX_CONCURRENT_REQUESTS):
                batch_group = batches[i:i+MAX_CONCURRENT_REQUESTS]
                results = await asyncio.gather(*[delete_batch(session, batch) for batch in batch_group])
                errors = [r for r in results if r is not None]
                if errors:
                    raise Exception("\n".join(errors))

        return True

    except Exception as e:
        log_error(e)  # Assuming you have a log_error function
        return False

# Don't forget to update the original function to run the async version
def delete_all_activations():
    return asyncio.run(delete_all_activations_async())


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


def save_session(token_data: TokenData, is_sandbox: bool, extra_state: dict = {}):
    ## TODO: change the invokers of save_session to provide a token_data every time
    if isinstance(token_data, dict):
        token_dict = token_data
    else:
        token_dict = token_data.to_dict()
    session_token = str(uuid4())
    salesforce_id = token_dict.get("id").split("/")[-1]
    org_id = token_dict.get("id").split("/")[-2]
    refresh_token = token_dict.get("refresh_token")
    session_state = SessionState(
        salesforce_id=salesforce_id,
        access_token=token_dict["access_token"],
        refresh_token=refresh_token,
        instance_url=token_dict["instance_url"],
        org_id=org_id,
        is_sandbox=is_sandbox,
        **extra_state,
    ).to_dict()
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
