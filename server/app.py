from flask import Flask, jsonify, redirect, request
from flask_cors import CORS
import requests, os

from server.engine.activation_engine import update_activation_states
from server.services.setting_service import define_criteria_from_tasks
from server.api.salesforce import get_criteria_fields
from server.cache import (
    save_code_verifier,
    load_code_verifier,
    save_tokens,
    load_settings,
    save_settings,
)
from server.constants import SESSION_EXPIRED, FILTER_TASK_FIELDS, FILTER_EVENT_FIELDS
from server.models import ApiResponse, SettingsModel, TaskSObject
from server.mapper.mapper import convert_settings_model_to_settings
from server.utils import format_error_message

app = Flask(__name__)
CORS(
    app,
    resources={r"/*": {"origins": "http://localhost:3000"}},
    supports_credentials=True,
)
app.secret_key = os.urandom(24)  # Secure secret key for session management

CLIENT_ID = "3MVG9ZF4bs_.MKug8aF61l5hklOzKnQLJ47l7QqY0HZN_Jis82hhCslKFnc2otkBLkOZpjBsIVBaSYojRW.kZ"
CLIENT_SECRET = "C3B5CD6936000FEFF40809F74D8260DC2BDA2B3446EF24A1454E39BB13C34BD8"
REDIRECT_URI = "http://localhost:8000/oauth/callback"


@app.before_request
def before_request():
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
    }
    if request.method.lower() == "options":
        return jsonify(headers), 200


@app.route("/store_code_verifier", methods=["POST"])
def store_code_verifier():
    data = request.json
    code_verifier = data.get("code_verifier")
    if code_verifier:
        save_code_verifier(code_verifier)
        return jsonify({"message": "Code verifier stored successfully"}), 200
    else:
        return jsonify({"error": "Code verifier not provided"}), 400


@app.route("/get_task_criteria_fields", methods=["GET"])
def get_task_criteria_fields():
    response = ApiResponse(data=[], message="", success=False)
    criteria_fields = get_criteria_fields(sobject_type="Task")

    if not criteria_fields.success:
        response.message = criteria_fields.message
    else:
        response.data = [
            field for field in criteria_fields.data if field.name in FILTER_TASK_FIELDS
        ]
        response.success = True

    return (
        jsonify(response.__dict__),
        get_status_code(response),
    )


@app.route("/get_event_criteria_fields", methods=["GET"])
def get_event_criteria_fields():
    try:
        response = ApiResponse(data=[], message="", success=False)
        criteria_fields = get_criteria_fields(sobject_type="Event")

        if not criteria_fields.success:
            response.message = criteria_fields.message
        else:
            response.data = [
                field
                for field in criteria_fields.data
                if field.name in FILTER_EVENT_FIELDS
            ]
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
        tasks = [TaskSObject(**task) for task in data.get("tasks")]
        if not tasks or len(tasks) == 0:
            response.success = False
            response.message = "No tasks provided"
        else:
            response.data = define_criteria_from_tasks(tasks)

        final_response = jsonify(response.to_dict()), 200 if response.success else 400
    except Exception as e:
        response.success = False
        response.message = f"Failed to generate filters: {format_error_message(e)}"
        final_response = jsonify(response.__dict__), 500

    return final_response


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

        redirect_url = (
            "http://localhost:3000/onboard"
            if len(load_settings().criteria) == 0
            else "http://localhost:3000/app/prospecting"
        )
        return redirect(redirect_url)
    else:
        error_details = {
            "error": "Failed to retrieve access token",
            "status_code": response.status_code,
            "response_text": response.text,
        }

        return jsonify(error_details), 500


@app.route("/load_prospecting_activities", methods=["GET"])
def load_prospecting_activities():
    api_response = ApiResponse(data=[], message="", success=False)
    try:

        response = update_activation_states()

        api_response.success = response.success
        api_response.message = response.message
        api_response.data = response.data

        status_code = get_status_code(api_response)
    except Exception as e:
        api_response.message = f"Failed to load prospecting activities: {str(e)}"
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
        return jsonify({"error": str(e)}), 500


@app.route("/get_settings", methods=["GET"])
def get_settings():
    try:
        settings_model = SettingsModel(settings=load_settings())
        return jsonify(settings_model.to_dict()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, host="localhost", port=8000)  # Updated to run on localhost


# helpers
def get_status_code(response):
    return (
        200 if response.success else 400 if SESSION_EXPIRED in response.message else 503
    )
