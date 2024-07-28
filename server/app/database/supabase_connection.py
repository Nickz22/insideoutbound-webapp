import jwt, os, time, uuid
from supabase import create_client, Client
from flask import g
from dotenv import load_dotenv
from app.data_models import AuthenticationError

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
admin_key: str = os.environ.get("SUPABASE_KEY")
jwt_secret: str = os.environ.get("SUPABASE_JWT_SECRET")
project_id: str = os.environ.get("SUPABASE_PROJECT_ID")

supabase: Client = create_client(url, admin_key)


def set_session_state(session_state):
    g.session_state = session_state


def get_session_state():
    if "session_state" not in g:
        raise AuthenticationError("Session state not set")
    return g.session_state


def set_supabase_user_client(client):
    g.supabase_user_client = client


def set_supabase_user_client_with_token(jwt_token, refresh_token):
    supabase_user_client = create_client(url, admin_key)
    supabase_user_client.auth.set_session(jwt_token, refresh_token)
    g.supabase_user_client = supabase


def get_supabase_user_client():
    if "supabase_user_client" not in g:
        raise AuthenticationError("Supabase user client not set")
    return g.supabase_user_client


def generate_supabase_jwt(email: str, supabase_user_id: str) -> str:

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


def get_supabase_admin_client() -> Client:
    return supabase


def get_supabase_client_with_token(
    email: str, refresh_token: str, supabase_user_id: str
) -> Client:

    try:
        jwt_token = generate_supabase_jwt(email, supabase_user_id)
        supabase_user_client = create_client(url, admin_key)
        supabase_user_client.auth.set_session(jwt_token, refresh_token)
        return {"client": supabase, "jwt_token": jwt_token}
    except AuthenticationError as e:
        print(str(e))
        raise e
    except Exception as e:
        raise AuthenticationError(f"Failed to authenticate with Supabase: {str(e)}")
