from flask import Flask, jsonify, redirect, request, url_for
from flask_cors import CORS
import requests
import os, json
from models import Filter, FilterContainer

from api.salesforce import fetch_tasks_by_criteria

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}}, supports_credentials=True)
app.secret_key = os.urandom(24)  # Secure secret key for session management

CLIENT_ID = '3MVG9ZF4bs_.MKug8aF61l5hklOzKnQLJ47l7QqY0HZN_Jis82hhCslKFnc2otkBLkOZpjBsIVBaSYojRW.kZ'
CLIENT_SECRET = 'C3B5CD6936000FEFF40809F74D8260DC2BDA2B3446EF24A1454E39BB13C34BD8'
REDIRECT_URI = 'http://localhost:8000/oauth/callback'
CODE_VERIFIER_FILE = 'code_verifier.json'
TOKEN_FILE = 'tokens.json'

def save_code_verifier(code_verifier):
    with open(CODE_VERIFIER_FILE, 'w') as f:
        json.dump({'code_verifier': code_verifier}, f)

def load_code_verifier():
    if os.path.exists(CODE_VERIFIER_FILE):
        with open(CODE_VERIFIER_FILE, 'r') as f:
            data = json.load(f)
            return data.get('code_verifier')
    return None

def save_tokens(access_token, instance_url):
    with open(TOKEN_FILE, 'w') as f:
        json.dump({'access_token': access_token, 'instance_url': instance_url}, f)

def load_tokens():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'r') as f:
            data = json.load(f)
            return data.get('access_token'), data.get('instance_url')
    return None, None

@app.before_request
def before_request():
    print("before_request")
    headers = {'Access-Control-Allow-Origin': '*',
               'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
               'Access-Control-Allow-Headers': 'Content-Type'}
    if request.method.lower() == 'options':
        return jsonify(headers), 200

@app.route('/')
def hello_world():
    return jsonify(message="Hello, World!")

@app.route('/store_code_verifier', methods=['POST'])
def store_code_verifier():
    data = request.json
    code_verifier = data.get('code_verifier')
    if code_verifier:
        save_code_verifier(code_verifier)
        print("Stored code_verifier:", code_verifier)  # Debug log
        return jsonify({'message': 'Code verifier stored successfully'}), 200
    else:
        return jsonify({'error': 'Code verifier not provided'}), 400

@app.route('/oauth/callback')
def oauth_callback():
    code = request.args.get('code')
    code_verifier = load_code_verifier()  # Retrieve the code verifier from the file

    if not code or not code_verifier:
        print("Missing code or code_verifier")  # Debug log
        return jsonify({'error': 'Missing authorization code or verifier'}), 400

    print("Retrieved code_verifier:", code_verifier)  # Debug log

    is_sandbox = "test" in request.referrer or "scratch" in request.referrer
    base_sf_domain = "test" if is_sandbox else "login"
    token_url = f'https://{base_sf_domain}.salesforce.com/services/oauth2/token'
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    payload = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code_verifier': code_verifier
    }

    response = requests.post(token_url, headers=headers, data=payload)
    if response.status_code == 200:
        token_data = response.json()
        save_tokens(token_data['access_token'], token_data['instance_url'])  # Save tokens to file
        return redirect('http://localhost:3000/app')
    else:
        error_details = {
            'error': 'Failed to retrieve access token',
            'status_code': response.status_code,
            'response_text': response.text
        }
        print(error_details)
        return jsonify(error_details), 500

criteria = [
    FilterContainer(
        filters=[
            Filter(field="Subject", data_type="string", operator="contains", value="[Disposition 1a]"),
            Filter(field="Subject", data_type="string", operator="contains", value="[Disposition 2a]"),
            Filter(field="Subject", data_type="string", operator="contains", value="[Disposition 3a]"),
            Filter(field="Subject", data_type="string", operator="contains", value="[Disposition 4a]"),
            Filter(field="Subject", data_type="string", operator="contains", value="[Disposition 5a]")
        ],
        filterLogic="((1 OR 2 OR 3) AND 4 AND 5)"
    ),
    FilterContainer(
        filters=[
            Filter(field="Priority", data_type="string", operator="equals", value="High"),
            Filter(field="Status", data_type="string", operator="not equals", value="Completed"),
            Filter(field="CreatedDate", data_type="date",  operator="last n days", value="30")
        ],
        filterLogic="1 AND 2 AND 3"
    ),
    FilterContainer(
        filters=[
            Filter(field="OwnerId", data_type="string", operator="equals", value="0051t000000TXXXXXX"),
            Filter(field="ActivityDate", data_type="date", operator="on or after", value="2022-01-01"),
            Filter(field="ActivityDate", data_type="date", operator="on or before", value="2022-12-31")
        ],
        filterLogic="1 AND (2 OR 3)"
    )
]

@app.route('/load_prospecting_activities')
def load_prospecting_activities():
    access_token, instance_url = load_tokens()  # Load tokens from file

    if not access_token or not instance_url:
        return redirect(url_for('login'))
    
    fetch_tasks_by_criteria(criteria, instance_url, access_token)
    
    return ""

if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=8000)  # Updated to run on localhost
