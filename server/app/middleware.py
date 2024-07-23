import json
from flask import request, jsonify, session
from functools import wraps
from datetime import datetime
from app.models import User, SessionModel


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        session_id = session.get("session_id")
        if not session_id:
            return jsonify({"error": "Unauthorized"}), 401

        db_session = SessionModel.query.filter_by(session_id=session_id).first()
        if not db_session or db_session.expiry < datetime.utcnow():
            return jsonify({"error": "Invalid or expired session"}), 401

        session_data = json.loads(db_session.data)
        user_id = session_data.get("user_id")

        if not user_id:
            return jsonify({"error": "User not found in session"}), 404

        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        if datetime.now() > db_session.expiry:
            return jsonify({"error": "Token has expired", "code": "TOKEN_EXPIRED"}), 401

        return f(*args, **kwargs)

    return decorated
