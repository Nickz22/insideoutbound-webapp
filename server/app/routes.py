from flask import Blueprint, jsonify, redirect, request, session, current_app
from app.middleware import authenticate
from app.utils import format_error_message
from server.app.database.activation_selector import (
    load_active_activations_order_by_first_prospecting_activity_asc,
)
from server.app.database.settings_selector import load_settings
from server.app.database.dml import save_settings
from datetime import datetime, timedelta
from app.constants import SESSION_EXPIRED
from app.mapper.mapper import convert_settings_model_to_settings
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
import requests
from config import Config

bp = Blueprint("main", __name__)


@bp.route("/store_code_verifier", methods=["POST"])
def store_code_verifier():
    data = request.json
    code_verifier = data.get("code_verifier")
    is_sandbox = data.get("is_sandbox", False)

    if not code_verifier:
        return jsonify({"error": "Code verifier not provided"}), 400

    session["code_verifier"] = code_verifier
    session["is_sandbox"] = is_sandbox
    session["is_temporary"] = True
    session["created_at"] = datetime.now().isoformat()

    return jsonify({"message": "Code verifier stored successfully"}), 200


@bp.route("/oauth/callback", methods=["GET"])
def oauth_callback():

    try:
        code = request.args.get("code")

        if not code or "code_verifier" not in session:
            return jsonify({"error": "Missing authorization code or session data"}), 400

        code_verifier = session.get("code_verifier")
        is_sandbox = session.get("is_sandbox", False)

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

            # Store token data in session
            session.clear()  # Clear temporary data
            session["access_token"] = token_data["access_token"]
            session["refresh_token"] = token_data["refresh_token"]
            session["instance_url"] = token_data["instance_url"]
            session["token_expires_at"] = (
                datetime.now() + timedelta(hours=1)
            ).isoformat()
            session["salesforce_id"] = token_data.get("id").split("/")[-1]
            session["email"] = token_data.get("email")
            session["org_id"] = token_data.get("org_id")
            session["is_sandbox"] = is_sandbox
            session.permanent = True

            # Generate Supabase JWT
            # supabase_jwt = generate_supabase_jwt(
            #     session["salesforce_id"], session["email"]
            # )
            # session["supabase_jwt"] = supabase_jwt

            settings = load_settings()
            if not settings:
                return redirect(f"{Config.REACT_APP_URL}/onboard")
            else:
                return redirect(f"{Config.REACT_APP_URL}/app/prospecting")
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


@bp.route("/logout")
def logout():
    session.clear()
    return jsonify({"message": "Logged out successfully"}), 200


@bp.route("/refresh_token", methods=["POST"])
def refresh_token():
    from app.data_models import UserModel, ApiResponse

    response = ApiResponse(data=[], message="", success=False)

    if "refresh_token" not in session:
        response.message = "No refresh token found"
        response.type = "AuthenticationError"
        return jsonify(response.to_dict()), 200

    base_sf_domain = "test" if session.get("is_sandbox") else "login"
    token_url = f"https://{base_sf_domain}.salesforce.com/services/oauth2/token"

    payload = {
        "grant_type": "refresh_token",
        "refresh_token": session["refresh_token"],
        "client_id": Config.CLIENT_ID,
        "client_secret": Config.CLIENT_SECRET,
    }

    try:
        response_sf = requests.post(token_url, data=payload)
        response_sf.raise_for_status()
        token_data = response_sf.json()

        # Update session with new token data
        session["access_token"] = token_data["access_token"]
        session["salesforce_id"] = token_data.get("id").split("/")[-1]

        user: UserModel = fetch_logged_in_salesforce_user().data

        session["email"] = user.email
        session["org_id"] = token_data.get("org_id")
        session.permanent = True
        session["token_expires_at"] = (datetime.now() + timedelta(hours=1)).isoformat()

        # Clear the existing Supabase JWT to force regeneration on next request
        session.pop("supabase_jwt", None)

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
    from app.data_models import ApiResponse, SettingsModel

    try:
        data = request.json
        settings = convert_settings_model_to_settings(SettingsModel(**data))
        save_settings(settings)
        return jsonify({"message": "Settings saved successfully"}), 200
    except Exception as e:
        print(f"Failed to save settings: {str(e)}")
        return jsonify({"error": str(e)}), 500


@bp.route("/get_settings", methods=["GET"])
@authenticate
def get_settings():
    from app.data_models import SettingsModel

    try:
        settings_model = SettingsModel(settings=load_settings())
        return jsonify(settings_model.to_dict()), 200
    except Exception as e:
        print(f"Failed to retrieve settings: {str(e)}")
        return jsonify({"error": str(e)}), 500


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
