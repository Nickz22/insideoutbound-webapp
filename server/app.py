from flask import Flask, jsonify, redirect, request, url_for
from flask_cors import CORS
import requests
import os
from settings import settings
from engine.activation_engine import compute_activated_accounts
from api.salesforce import fetch_tasks_by_criteria
from cache import save_code_verifier, load_code_verifier, save_tokens,
from constants import c

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


@app.route("/oauth/callback")
def oauth_callback():
    code = request.args.get("code")
    code_verifier = load_code_verifier()  # Retrieve the code verifier from the file

    if not code or not code_verifier:
        print("Missing code or code_verifier")  # Debug log
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
        save_tokens(
            token_data["access_token"], token_data["instance_url"]
        )  # Save tokens to file
        return redirect("http://localhost:3000/app")
    else:
        error_details = {
            "error": "Failed to retrieve access token",
            "status_code": response.status_code,
            "response_text": response.text,
        }
        print(error_details)
        return jsonify(error_details), 500


@app.route("/load_prospecting_activities")
def load_prospecting_activities():

    api_response = fetch_tasks_by_criteria(
        settings.criteria
    )
    
    if api_response.message == c.MISSING_ACCESS_TOKEN:
        return redirect(url_for("login"))
    
    activated_accounts = compute_activated_accounts(tasks_by_criteria, settings)

    return tasks, 200


if __name__ == "__main__":
    app.run(debug=True, host="localhost", port=8000)  # Updated to run on localhost
