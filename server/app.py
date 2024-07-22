from flask import Flask, jsonify, redirect, request
from flask_cors import CORS
import requests, os

from dotenv import load_dotenv

load_dotenv()

BASE_SERVER_URL = (
    os.getenv("FLASK_NGROK_URL")
    if os.getenv("FLASK_NGROK_URL") != None
    else "http://localhost:8000"
)

REACT_APP_URL = (
    os.getenv("REACT_APP_URL")
    if os.getenv("REACT_APP_URL") != None
    else "http://localhost:3000"
)

from server.engine.activation_engine import update_activation_states
from server.services.setting_service import define_criteria_from_events_or_tasks
from server.helpers.activation_helper import generate_summary
from server.api.salesforce import (
    fetch_criteria_fields,
    fetch_task_fields,
    fetch_event_fields,
    fetch_salesforce_users,
    fetch_tasks_by_user_ids,
    fetch_events_by_user_ids,
    fetch_logged_in_salesforce_user_id,
)
from server.cache import (
    save_code_verifier,
    load_code_verifier,
    save_tokens,
    load_settings,
    save_settings,
    load_active_activations_order_by_first_prospecting_activity_asc,
)
from server.constants import SESSION_EXPIRED
from server.models import ApiResponse, SettingsModel, TableColumn, Activation
from server.mapper.mapper import convert_settings_model_to_settings
from server.utils import format_error_message

app = Flask(__name__)
CORS(
    app,
    resources={r"/*": {"origins": [BASE_SERVER_URL, REACT_APP_URL]}},
    supports_credentials=True,
    allow_headers=["Content-Type", "Authorization"],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
)
app.secret_key = os.urandom(24)  # Secure secret key for session management

CLIENT_ID = "3MVG9ZF4bs_.MKug8aF61l5hklOzKnQLJ47l7QqY0HZN_Jis82hhCslKFnc2otkBLkOZpjBsIVBaSYojRW.kZ"
CLIENT_SECRET = "C3B5CD6936000FEFF40809F74D8260DC2BDA2B3446EF24A1454E39BB13C34BD8"
REDIRECT_URI = f"{BASE_SERVER_URL}/oauth/callback"


@app.after_request
def add_header(response):
    response.headers["Content-Security-Policy"] = (
        "default-src 'self' https://*.ngrok-free.app; "
        "script-src 'self' 'unsafe-inline' https://*.ngrok-free.app; "
        "style-src 'self' 'unsafe-inline' https://*.ngrok-free.app"
    )
    return response


@app.route("/store_code_verifier", methods=["POST"])
def store_code_verifier():
    data = request.json
    code_verifier = data.get("code_verifier")
    if code_verifier:
        save_code_verifier(code_verifier)
        return jsonify({"message": "Code verifier stored successfully"}), 200
    else:
        return jsonify({"error": "Code verifier not provided"}), 400


@app.route("/oauth/callback")
def oauth_callback():
    code = request.args.get("code")
    code_verifier = load_code_verifier()  # Retrieve the code verifier from the file

    if not code or not code_verifier:
        return jsonify({"error": "Missing authorization code or verifier"}), 400

    is_sandbox = "test" in request.referrer or "scratch" in request.referrer
    base_sf_domain = "test" if is_sandbox else "login"
    token_url = f"https://{base_sf_domain}.salesforce.com/services/oauth2/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code_verifier": code_verifier,
    }

    response = requests.post(token_url, headers=headers, data=payload)
    if response.status_code == 200:
        token_data = response.json()
        save_tokens(token_data["access_token"], token_data["instance_url"])
        settings = load_settings()
        redirect_url = (
            f"{REACT_APP_URL}/onboard"
            if not settings
            else f"{REACT_APP_URL}/app/prospecting"
        )
        return redirect(redirect_url)
    else:
        error_details = {
            "error": "Failed to retrieve access token",
            "status_code": response.status_code,
            "response_text": response.text,
        }

        return jsonify(error_details), 500


@app.route("/get_criteria_fields", methods=["GET"])
def get_criteria_fields():
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
        response.message = (
            f"Failed to retrieve event criteria fields: {format_error_message(e)}"
        )

    return (
        jsonify(response.__dict__),
        get_status_code(response),
    )


@app.route("/generate_filters", methods=["POST"])
def generate_filters():
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
        final_response = jsonify(response.__dict__), 500

    return final_response


@app.route("/get_prospecting_activities", methods=["GET"])
def get_prospecting_activities():
    response = ApiResponse(data=[], message="", success=False)
    try:
        activations = (
            load_active_activations_order_by_first_prospecting_activity_asc().data
        )
        response.data = {
            "summary": generate_summary(activations),
            "raw_data": activations,
        }
        response.success = True
    except Exception as e:
        error_msg = format_error_message(e)
        print(f"Failed to retrieve prospecting activities: {error_msg}")
        response.message = f"Failed to retrieve prospecting activities: {error_msg}"

    return jsonify(response.__dict__), get_status_code(response)


@app.route("/get_prospecting_activities_filtered_by_ids", methods=["GET"])
def get_prospecting_activities_filtered_by_ids():
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

    return jsonify(response.__dict__), get_status_code(response)


@app.route("/fetch_prospecting_activity", methods=["GET"])
def fetch_prospecting_activity():
    api_response = ApiResponse(data={}, message="", success=False)
    try:
        response = update_activation_states()

        if response.success:
            activations = response.data

            api_response.data = {
                "summary": generate_summary(activations),
                "raw_data": activations,
            }
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

    return jsonify(api_response.__dict__), status_code


@app.route("/save_settings", methods=["POST"])
def commit_settings():
    try:
        data = request.json
        settings = convert_settings_model_to_settings(SettingsModel(**data))
        save_settings(settings)
        return jsonify({"message": "Settings saved successfully"}), 200
    except Exception as e:
        print(f"Failed to save settings: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/get_settings", methods=["GET"])
def get_settings():
    try:
        settings_model = SettingsModel(settings=load_settings())
        return jsonify(settings_model.to_dict()), 200
    except Exception as e:
        print(f"Failed to retrieve settings: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/get_salesforce_users", methods=["GET"])
def get_salesforce_users():
    response = ApiResponse(data=[], message="", success=False)
    try:
        response.data = fetch_salesforce_users().data
        response.success = True
    except Exception as e:
        response.message = (
            f"Failed to retrieve Salesforce users: {format_error_message(e)}"
        )

    return jsonify(response.__dict__), get_status_code(response)


@app.route("/get_salesforce_tasks_by_user_ids", methods=["GET"])
def get_salesforce_tasks_by_user_ids():
    response = ApiResponse(data=[], message="", success=False)
    try:
        user_ids = request.args.getlist("user_ids[]")

        if not user_ids:
            response.message = "No user IDs provided"
        else:
            response.data = fetch_tasks_by_user_ids(user_ids).data
            response.success = True
    except Exception as e:
        response.message = f"Failed to retrieve Salesforce tasks by user IDs: {format_error_message(e)}"

    return jsonify(response.__dict__), get_status_code(response)


@app.route("/get_salesforce_events_by_user_ids", methods=["GET"])
def get_salesforce_events_by_user_ids():
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


@app.route("/get_salesforce_user_id", methods=["GET"])
def get_salesforce_user_id():
    response = ApiResponse(data=[], message="", success=False)
    try:
        response.data = fetch_logged_in_salesforce_user_id().data
        response.success = True
    except Exception as e:
        response.message = (
            f"Failed to retrieve Salesforce users: {format_error_message(e)}"
        )
        print(response.message)

    return jsonify(response.__dict__), get_status_code(response)


if __name__ == "__main__":
    app.run(debug=True, host="localhost", port=8000)  # Updated to run on localhost


@app.route("/get_task_fields", methods=["GET"])
def get_task_fields():
    response = ApiResponse(data=[], message="", success=False)
    try:
        response.data = fetch_task_fields().data
        response.success = True
    except Exception as e:
        error_msg = format_error_message(e)
        print(error_msg)
        response.message = f"Failed to retrieve task fields: {error_msg}"

    return jsonify(response.__dict__), get_status_code(response)


@app.route("/get_event_fields", methods=["GET"])
def get_event_fields():
    response = ApiResponse(data=[], message="", success=False)
    try:
        response = fetch_event_fields()
    except Exception as e:
        response.message = f"Failed to retrieve event fields: {format_error_message(e)}"

    return jsonify(response.__dict__), get_status_code(response)


# helpers
def get_status_code(response):
    return (
        200 if response.success else 400 if SESSION_EXPIRED in response.message else 503
    )
