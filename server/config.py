import os
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or os.urandom(24)
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    BASE_SERVER_URL = os.getenv("FLASK_NGROK_URL", "http://localhost:8000")
    REACT_APP_URL = os.getenv("REACT_APP_URL", "http://localhost:3000")

    CLIENT_ID = os.getenv("CLIENT_ID")
    CLIENT_SECRET = os.getenv("CLIENT_SECRET")
    REDIRECT_URI = f"{BASE_SERVER_URL}/oauth/callback"

    # Session configuration
    SESSION_TYPE = "sqlalchemy"
    SESSION_SQLALCHEMY = None  # This will be set in create_app
    SESSION_SQLALCHEMY_TABLE = "sessions"
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = True  # for HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
