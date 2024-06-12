from flask import Flask, jsonify, redirect, request, session, url_for
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
app.secret_key = os.urandom(24)  # Secure secret key for session management

# Replace these with your Salesforce connected app details
CLIENT_ID = '3MVG9ZF4bs_.MKug8aF61l5hklOzKnQLJ47l7QqY0HZN_Jis82hhCslKFnc2otkBLkOZpjBsIVBaSYojRW.kZ'
CLIENT_SECRET = 'C3B5CD6936000FEFF40809F74D8260DC2BDA2B3446EF24A1454E39BB13C34BD8'
REDIRECT_URI = 'http://localhost:3000/oauth/callback'

@app.route('/')
def hello_world():
    return jsonify(message="Hello, World!")

@app.route('/oauth/callback')
def oauth_callback():
    code = request.args.get('code')
    if not code:
        return 'Error: Authorization code not found', 400

    verifier = request.args.get('code_verifier')  # Retrieve the code verifier from a secure place

    token_url = 'https://login.salesforce.com/services/oauth2/token'
    payload = {
        'grant_type': 'authorization_code',
        'code': code,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'redirect_uri': REDIRECT_URI,
        'code_verifier': verifier  # Include the verifier in the token request
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    response = requests.post(token_url, data=payload, headers=headers)
    if response.status_code != 200:
        return f"Error: {response.content}", 500

    token_data = response.json()
    session['access_token'] = token_data['access_token']
    session['instance_url'] = token_data['instance_url']

    return redirect('http://localhost:3000/app')


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
    app.run(debug=True)
