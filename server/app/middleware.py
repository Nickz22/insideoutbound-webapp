from functools import wraps
from flask import session
from datetime import datetime
from app.data_models import AuthenticationError
from app.database.supabase_connection import get_supabase_client


def authenticate(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Salesforce authentication check
        if "access_token" not in session:
            raise AuthenticationError("Session expired")
            # return (
            #     jsonify({"error": "session expired", "type": "AuthenticationError"}),
            #     401,
            # )

        if "token_expires_at" not in session or datetime.now() > datetime.fromisoformat(
            session["token_expires_at"]
        ):
            raise AuthenticationError("Session expired")
            # return (
            #     jsonify(
            #         {
            #             "error": "session expired",
            #             "code": "TOKEN_EXPIRED",
            #             "type": "AuthenticationError",
            #         }
            #     ),
            #     401,
            # )

        if "salesforce_id" not in session:
            raise AuthenticationError("Session expired")
            # return (
            #     jsonify(
            #         {
            #             "error": "session expired",
            #             "type": "AuthenticationError",
            #         }
            #     ),
            #     404,
            # )

        # Supabase authentication check
        get_supabase_client()

        return f(*args, **kwargs)

    return decorated
