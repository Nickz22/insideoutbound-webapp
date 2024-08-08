import os
from supabase import create_client, Client
from flask import g
from dotenv import load_dotenv
from server.app.data_models import AuthenticationError

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


def get_supabase_admin_client() -> Client:
    return supabase
