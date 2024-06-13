from flask import Flask, jsonify, redirect, request, session, url_for, Response
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)
app.secret_key = os.urandom(24)  # Secure secret key for session management

CLIENT_ID = '3MVG9ZF4bs_.MKug8aF61l5hklOzKnQLJ47l7QqY0HZN_Jis82hhCslKFnc2otkBLkOZpjBsIVBaSYojRW.kZ'
CLIENT_SECRET = 'C3B5CD6936000FEFF40809F74D8260DC2BDA2B3446EF24A1454E39BB13C34BD8'
REDIRECT_URI = 'http://localhost:8000/oauth/callback'

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
        session['code_verifier'] = code_verifier
        return jsonify({'message': 'Code verifier stored successfully'}), 200
    else:
        return jsonify({'error': 'Code verifier not provided'}), 400

@app.route('/oauth/callback')
def oauth_callback():
    code = request.args.get('code')
    code_verifier = session.pop('code_verifier', None)  # Retrieve and remove the code verifier from the session

    if not code or not code_verifier:
        return jsonify({'error': 'Missing authorization code or verifier'}), 400

    token_url = 'https://login.salesforce.com/services/oauth2/token'
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
        session['access_token'] = token_data['access_token']
        session['instance_url'] = token_data['instance_url']
        return redirect('http://localhost:3000/app')
    else:
        error_details = {
            'error': 'Failed to retrieve access token',
            'status_code': response.status_code,
            'response_text': response.text
        }
        print(error_details)
        return jsonify(error_details), 500

@app.route('/home')
def home():
    access_token = session.get('access_token')
    instance_url = session.get('instance_url')

    if not access_token or not instance_url:
        return redirect(url_for('login'))

    headers = {'Authorization': f'Bearer {access_token}'}
    account_url = f"{instance_url}/services/data/v52.0/sobjects/Account/0011r00002xxxxxxx"  # Replace with a valid Account ID

    account_response = requests.get(account_url, headers=headers)
    if account_response.status_code != 200:
        return f"Error: {account_response.content}", 500

    account_data = account_response.json()

    return jsonify(account_data)

if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=8000)  # Updated to run on localhost
