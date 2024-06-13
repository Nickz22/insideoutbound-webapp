from flask import Flask, jsonify, redirect, request, session, url_for
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
app.secret_key = os.urandom(24)  # Secure secret key for session management

CLIENT_ID = '3MVG9ZF4bs_.MKug8aF61l5hklOzKnQLJ47l7QqY0HZN_Jis82hhCslKFnc2otkBLkOZpjBsIVBaSYojRW.kZ'
CLIENT_SECRET = 'C3B5CD6936000FEFF40809F74D8260DC2BDA2B3446EF24A1454E39BB13C34BD8'
REDIRECT_URI = 'http://localhost:5000/oauth/callback'

@app.route('/')
def hello_world():
    return jsonify(message="Hello, World!")

@app.route('/oauth/callback')
def oauth_callback():
    code = request.args.get('code')
    if not code:
        return 'Authorization code not found', 400

    token_url = 'https://test.salesforce.com/services/oauth2/token'
    payload = {
        'grant_type': 'authorization_code',
        'code': code,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'redirect_uri': 'http://localhost:5000/oauth/callback'
    }
    response = requests.post(token_url, data=payload)
    data = response.json()
    session['access_token'] = data['access_token']
    session['instance_url'] = data['instance_url']

    return redirect('http://localhost:3000/app')  # Redirect back to React app

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
    app.run(debug=True, host='localhost', port=5000)  # Updated to run on localhost
