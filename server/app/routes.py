import requests, json
from flask import Blueprint, jsonify, redirect, request
from urllib.parse import unquote
from uuid import uuid4
from app.middleware import authenticate
from app.utils import format_error_message
from server.app.database.activation_selector import (
    load_active_activations_order_by_first_prospecting_activity_asc,
)
from server.app.database.settings_selector import load_settings
from server.app.database.dml import save_settings, insert_supabase_user
from datetime import datetime, timedelta, timezone
from app.constants import SESSION_EXPIRED
from app.mapper.mapper import (
    convert_settings_model_to_settings,
    convert_settings_to_settings_model,
)
from app.helpers.activation_helper import generate_summary
from app.services.setting_service import define_criteria_from_events_or_tasks
from app.engine.activation_engine import update_activation_states
from server.app.salesforce_api import (
    fetch_criteria_fields,
    fetch_task_fields,
    fetch_event_fields,
    fetch_salesforce_users,
    fetch_tasks_by_user_ids,
    fetch_events_by_user_ids,
    fetch_logged_in_salesforce_user,
)
from config import Config
from app.database.supabase_connection import (
    get_supabase_client_with_token,
    set_supabase_user_client,
    get_supabase_admin_client,
    get_supabase_user_client,
    set_session_state,
)
from app.database.session_selector import fetch_supabase_session
from app.database.supabase_user_selector import fetch_supabase_user

bp = Blueprint("main", __name__)


@bp.route("/oauth/callback", methods=["GET"])
def oauth_callback():
    try:
        code = request.args.get("code")
        state = request.args.get("state")

        if not code or not state:
            return jsonify({"error": "Missing authorization code or state"}), 400

        try:
            state_data = json.loads(unquote(state))
            code_verifier = state_data["codeVerifier"]
            is_sandbox = state_data["isSandbox"]
        except (json.JSONDecodeError, KeyError):
            return jsonify({"error": "Invalid state parameter"}), 400

        base_sf_domain = "test" if is_sandbox else "login"
        token_url = f"https://{base_sf_domain}.salesforce.com/services/oauth2/token"

        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": Config.REDIRECT_URI,
            "client_id": Config.CLIENT_ID,
            "client_secret": Config.CLIENT_SECRET,
            "code_verifier": code_verifier,
        }

        response = requests.post(token_url, data=payload)
        if response.status_code == 200:
            token_data = response.json()
            session_token = create_session(token_data, is_sandbox)

            settings = load_settings()
            if not settings:
                return redirect(
                    f"{Config.REACT_APP_URL}/onboard?session_token={session_token}"
                )
            else:
                return redirect(
                    f"{Config.REACT_APP_URL}/app/prospecting?session_token={session_token}"
                )
        else:
            error_details = {
                "error": "Failed to retrieve access token",
                "status_code": response.status_code,
                "response_text": response.text,
            }
            return jsonify(error_details), 500
    except Exception as e:
        error_msg = format_error_message(e)
        print(error_msg)
        return jsonify({"error": f"Failed to retrieve access token: {error_msg}"}), 500


@bp.route("/logout", methods=["POST"])
@authenticate
def logout():
    from app.data_models import ApiResponse

    api_response = ApiResponse(data=[], message="", success=False)
    admin_supabase = get_supabase_admin_client()
    user_subabase = get_supabase_user_client()
    admin_supabase.auth.sign_out()
    user_subabase.auth.sign_out()

    api_response.success = True
    api_response.message = "Logged out successfully"
    return jsonify(api_response.to_dict()), 200


@bp.route("/refresh_token", methods=["POST"])
def refresh_token():
    from app.data_models import ApiResponse

    response = ApiResponse(data=[], message="", success=False)
    session_token = request.headers.get("X-Session-Token")
    session = fetch_supabase_session(session_token)
    session_state = json.loads(session["state"])

    if "refresh_token" not in session_state:
        response.message = "No refresh token found, please login."
        response.type = "AuthenticationError"
        return jsonify(response.to_dict()), 200

    base_sf_domain = "test" if session_state.get("is_sandbox") else "login"
    token_url = f"https://{base_sf_domain}.salesforce.com/services/oauth2/token"
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": session_state["refresh_token"],
        "client_id": Config.CLIENT_ID,
        "client_secret": Config.CLIENT_SECRET,
    }

    try:
        response_sf = requests.post(token_url, data=payload)
        response_sf.raise_for_status()
        token_data = response_sf.json()
        token_data["refresh_token"] = session_state["refresh_token"]

        session_token = create_session(token_data, session_state["is_sandbox"])
        response.data = [{"session_token": session_token}]
        response.success = True
        response.message = "Token refreshed successfully"
    except requests.exceptions.RequestException as e:
        response.message = f"Failed to refresh token: {str(e)}"
        response.type = "AuthenticationError"

    return jsonify(response.to_dict()), 200


@bp.route("/get_criteria_fields", methods=["GET"])
@authenticate
def get_criteria_fields():
    from app.data_models import ApiResponse

    try:
        response = ApiResponse(data=[], message="", success=False)
        object_type = request.args.get("object")
        criteria_fields = fetch_criteria_fields(sobject_type=object_type)

        if not criteria_fields.success:
            response.message = criteria_fields.message
        else:
            response.data = criteria_fields.data
            response.success = True
    except Exception as e:
        response.success = False
        error_msg = format_error_message(e)
        print(error_msg)
        response.message = f"Failed to retrieve event criteria fields: {error_msg}"

    return (
        jsonify(response.to_dict()),
        get_status_code(response),
    )


@bp.route("/generate_filters", methods=["POST"])
@authenticate
def generate_filters():
    from app.data_models import ApiResponse, TableColumn

    response = ApiResponse(data=[], message="", success=True)
    final_response = None
    try:
        data = request.json
        records = data.get("tasksOrEvents")
        columns = [TableColumn(**column) for column in data.get("selectedColumns")]
        if not records or len(records) == 0:
            response.success = False
            response.message = "No tasks provided"
        else:
            response.data = [
                define_criteria_from_events_or_tasks(
                    records,
                    columns,
                    fetch_criteria_fields(
                        "Task" if records[0]["Id"].startswith("00T") else "Event"
                    ).data,
                )
            ]

        final_response = jsonify(response.to_dict()), 200 if response.success else 400
    except Exception as e:
        response.success = False
        response.message = f"Failed to generate filters: {format_error_message(e)}"
        print(response.message)
        final_response = jsonify(response.to_dict()), 500

    return final_response


@bp.route("/get_prospecting_activities", methods=["GET"])
@authenticate
def get_prospecting_activities():
    from app.data_models import ApiResponse

    response = ApiResponse(data=[], message="", success=False)
    try:
        activations = (
            load_active_activations_order_by_first_prospecting_activity_asc().data
        )
        response.data = [
            {
                "summary": generate_summary(activations),
                "raw_data": [activation.to_dict() for activation in activations],
            }
        ]
        response.success = True
    except Exception as e:
        error_msg = format_error_message(e)
        print(f"Failed to retrieve prospecting activities: {error_msg}")
        response.message = f"Failed to retrieve prospecting activities: {error_msg}"
        response.type = "UnexpectedError"

    return jsonify(response.to_dict()), 200


@bp.route("/get_prospecting_activities_filtered_by_ids", methods=["GET"])
@authenticate
def get_prospecting_activities_filtered_by_ids():
    from app.data_models import ApiResponse

    response = ApiResponse(data=[], message="", success=False)
    try:
        activation_ids = request.args.getlist("activation_ids[]")
        if not activation_ids:
            response.message = "No activation IDs provided"
        else:
            activations = (
                load_active_activations_order_by_first_prospecting_activity_asc().data
            )
            filtered_activations = [
                activation
                for activation in activations
                if activation.id in activation_ids
            ]
            response.data = {
                "summary": generate_summary(filtered_activations),
                "raw_data": filtered_activations,
            }
            response.success = True
    except Exception as e:
        response.message = (
            f"Failed to retrieve prospecting activities: {format_error_message(e)}"
        )

    return jsonify(response.to_dict()), get_status_code(response)


@bp.route("/fetch_prospecting_activity", methods=["POST"])
@authenticate
def fetch_prospecting_activity():
    from app.data_models import ApiResponse

    api_response = ApiResponse(data=[], message="", success=False)
    try:
        response = update_activation_states()

        if response.success:
            activations = response.data

            api_response.data = [
                {
                    "summary": generate_summary(activations),
                    "raw_data": [activation.to_dict() for activation in activations],
                }
            ]
            api_response.success = True
            api_response.message = "Prospecting activity data loaded successfully"
        else:
            api_response.message = response.message

        status_code = get_status_code(api_response)
    except Exception as e:
        api_response.message = (
            f"Failed to load prospecting activities data: {format_error_message(e)}"
        )
        print(api_response.message)
        status_code = get_status_code(api_response)

    return jsonify(api_response.to_dict()), status_code


@bp.route("/save_settings", methods=["POST"])
@authenticate
def commit_settings():
    from app.data_models import SettingsModel, ApiResponse

    api_response = ApiResponse(data=[], message="", success=False)
    try:
        data = request.json
        settings = convert_settings_model_to_settings(SettingsModel(**data))
        save_settings(settings)
        api_response.success = True
        api_response.message = "Settings saved successfully"
    except Exception as e:
        error_msg = format_error_message(e)
        print(error_msg)
        api_response.message = f"Failed to save settings: {error_msg}"

    return jsonify(api_response.to_dict()), 200 if api_response.success else 400


@bp.route("/get_settings", methods=["GET"])
@authenticate
def get_settings():
    from app.data_models import SettingsModel, ApiResponse

    api_response = ApiResponse(data=[], message="", success=False)

    try:
        settings = load_settings()
        settings_model: SettingsModel = convert_settings_to_settings_model(settings)
        api_response.data = [settings_model.to_dict()]
        api_response.success = True
        return jsonify(api_response.to_dict()), 200
    except Exception as e:
        print(f"Failed to retrieve settings: {str(e)}")
        api_response.message = f"Failed to retrieve settings: {str(e)}"

    return api_response


@bp.route("/get_salesforce_users", methods=["GET"])
@authenticate
def get_salesforce_users():
    from app.data_models import ApiResponse

    response = ApiResponse(data=[], message="", success=False)
    try:
        response.data = fetch_salesforce_users().data
        response.success = True
    except Exception as e:
        error_message = format_error_message(e)
        print(error_message)
        response.message = f"Failed to retrieve Salesforce users: {error_message}"

    return jsonify(response.to_dict()), get_status_code(response)


@bp.route("/get_salesforce_tasks_by_user_ids", methods=["GET"])
@authenticate
def get_salesforce_tasks_by_user_ids():
    from app.data_models import ApiResponse

    response = ApiResponse(data=[], message="", success=False)
    try:
        user_ids = request.args.getlist("user_ids[]")

        if not user_ids:
            response.message = "No user IDs provided"
        else:
            response.data = fetch_tasks_by_user_ids(user_ids).data
            response.success = True
    except Exception as e:
        error_msg = format_error_message(e)
        print(error_msg)
        response.message = (
            f"Failed to retrieve Salesforce tasks by user IDs: {error_msg}"
        )

    return jsonify(response.to_dict()), get_status_code(response)


@bp.route("/get_salesforce_events_by_user_ids", methods=["GET"])
@authenticate
def get_salesforce_events_by_user_ids():
    from app.data_models import ApiResponse

    response = ApiResponse(data=[], message="", success=False)
    try:
        user_ids = request.args.getlist("user_ids[]")

        if not user_ids:
            response.message = "No user IDs provided"
        else:
            response.data = fetch_events_by_user_ids(user_ids).data
            response.success = True
    except Exception as e:
        response.message = f"Failed to retrieve Salesforce events by user IDs: {format_error_message(e)}"

    return jsonify(response.__dict__), get_status_code(response)


@bp.route("/get_salesforce_user", methods=["GET"])
@authenticate
def get_salesforce_user():
    from app.data_models import ApiResponse

    response = ApiResponse(data=[], message="", success=False)
    try:
        response.data = [fetch_logged_in_salesforce_user().data]
        response.success = True
    except Exception as e:
        response.message = (
            f"Failed to retrieve Salesforce users: {format_error_message(e)}"
        )
        print(response.message)

    return jsonify(response.to_dict()), get_status_code(response)


@bp.route("/get_task_fields", methods=["GET"])
@authenticate
def get_task_fields():
    from app.data_models import ApiResponse

    response = ApiResponse(data=[], message="", success=False)
    try:
        response.data = fetch_task_fields().data
        response.success = True
    except Exception as e:
        error_msg = format_error_message(e)
        print(error_msg)
        response.message = f"Failed to retrieve task fields: {error_msg}"

    return jsonify(response.to_dict()), get_status_code(response)


@bp.route("/get_event_fields", methods=["GET"])
@authenticate
def get_event_fields():
    from app.data_models import ApiResponse

    response = ApiResponse(data=[], message="", success=False)
    try:
        response = fetch_event_fields()
    except Exception as e:
        response.message = f"Failed to retrieve event fields: {format_error_message(e)}"

    return jsonify(response.__dict__), get_status_code(response)


@bp.app_errorhandler(Exception)
def handle_exception(e):
    from app.data_models import AuthenticationError

    error_msg = format_error_message(e)
    print(error_msg)
    if isinstance(e, AuthenticationError):
        return jsonify({"error": str(e), "type": "AuthenticationError"}), 200
    return (
        jsonify({"error": error_msg, "type": type(e).__name__}),
        500,
    )


# helpers
def get_status_code(response):
    return (
        200 if response.success else 400 if SESSION_EXPIRED in response.message else 503
    )


def create_session(token_data, is_sandbox):
    session_token = str(uuid4())
    salesforce_id = token_data.get("id").split("/")[-1]
    # set to enable query of salesforce user
    set_session_state(
        {
            "access_token": token_data["access_token"],
            "instance_url": token_data["instance_url"],
        }
    )
    salesforce_user = fetch_salesforce_users([salesforce_id]).data[0]
    org_id = token_data.get("org_id")
    supabase_user = fetch_supabase_user(salesforce_id)
    if supabase_user is None:
        insert_supabase_user(
            salesforce_id=salesforce_id,
            email=salesforce_user.email,
            org_id=org_id,
            is_sandbox=is_sandbox,
        )
        supabase_user = fetch_supabase_user(salesforce_id)
    supabase_user_id = supabase_user.id
    email = supabase_user.email
    refresh_token = token_data.get("refresh_token")
    session_state = {
        "salesforce_id": salesforce_id,
        "access_token": token_data["access_token"],
        "refresh_token": refresh_token,
        "instance_url": token_data["instance_url"],
        "email": email,
        "org_id": org_id,
        "is_sandbox": is_sandbox,
        "supabase_user_id": supabase_user_id,
    }

    response = get_supabase_client_with_token(
        email=email,
        refresh_token=refresh_token,
        supabase_user_id=supabase_user_id,
    )
    session_state["jwt_token"] = response["jwt_token"]
    supabase = response["client"]
    set_supabase_user_client(supabase)
    # Store session data in Supabase
    now = datetime.now(timezone.utc).astimezone()
    session_data = {
        "id": session_token,
        "expiry": (now + timedelta(hours=1)).isoformat(),
        "state": json.dumps(session_state),
    }
    supabase.table("Session").insert(session_data).execute()
    return session_token