from functools import wraps
from flask import jsonify, session
from datetime import datetime

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'access_token' not in session:
            return jsonify({"error": "Unauthorized"}), 401

        # Check if token is expired
        if 'token_expires_at' not in session or datetime.now() > datetime.fromisoformat(session['token_expires_at']):
            return jsonify({"error": "Token has expired", "code": "TOKEN_EXPIRED"}), 401

        if 'salesforce_id' not in session:
            return jsonify({"error": "User not found in session"}), 404

        return f(*args, **kwargs)

    return decorated