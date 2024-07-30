from flask import request, g
import json
from functools import wraps
from datetime import datetime, timezone
from app.data_models import AuthenticationError
from app.database.supabase_connection import (
    set_session_state,
)
from app.database.session_selector import fetch_supabase_session
from dateutil import parser


def authenticate(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        session_token = request.headers.get("X-Session-Token")
        if not session_token:
            raise AuthenticationError("missing session token, are you logged in?")

        session = fetch_supabase_session(session_token)
        session_state = json.loads(session["state"])
        set_session_state(session_state)

        now = datetime.now(timezone.utc).astimezone()

        if now > parser.isoparse(session["expiry"]):
            raise AuthenticationError("Session expired")

        return f(*args, **kwargs)

    return decorated
