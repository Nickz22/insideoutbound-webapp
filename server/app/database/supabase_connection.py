import jwt, os, time, uuid
from supabase import create_client, Client
from flask import session as flask_session, jsonify
from dotenv import load_dotenv
from functools import wraps
from app.data_models import AuthenticationError
from app.database.supabase_user_selector import fetch_supabase_user_id

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
jwt_secret: str = os.environ.get("SUPABASE_JWT_SECRET")
project_id: str = os.environ.get("SUPABASE_PROJECT_ID")

supabase: Client = create_client(url, key)


def generate_supabase_jwt(salesforce_id: str, email: str) -> str:
    supabase_user_id = fetch_supabase_user_id(salesforce_id)
    flask_session["supabase_user_id"] = supabase_user_id
    if not supabase_user_id:
        raise AuthenticationError(
            f"No Supabase user found for Salesforce ID: {salesforce_id}"
        )

    payload = {
        "aud": "authenticated",
        "exp": int(time.time()) + 3600,  # Token expires in 1 hour
        "sub": supabase_user_id,  # Use the Supabase user ID as the subject
        "email": email,
        "role": "authenticated",
        "iss": f"https://{project_id}.supabase.co",
        "iat": int(time.time()),
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, jwt_secret, algorithm="HS256")


def get_supabase_client() -> Client:
    if "salesforce_id" not in flask_session or "email" not in flask_session:
        raise AuthenticationError("Session expired")

    try:
        if "supabase_jwt" not in flask_session:
            jwt_token = generate_supabase_jwt(
                flask_session["salesforce_id"], flask_session["email"]
            )
            flask_session["supabase_jwt"] = jwt_token

        # Set the session using the JWT token
        supabase.auth.set_session(
            flask_session["supabase_jwt"], flask_session.get("refresh_token")
        )
        return supabase
    except AuthenticationError as e:
        print(str(e))
        flask_session.pop("supabase_jwt", None)
        raise e
    except Exception as e:
        flask_session.pop("supabase_jwt", None)
        raise AuthenticationError(f"Failed to authenticate with Supabase: {str(e)}")
