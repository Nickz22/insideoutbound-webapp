import os
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or os.urandom(24)

    SUPABASE_PROJECT_ID = os.getenv("SUPABASE_PROJECT_ID")
    SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")

    SERVER_URL = os.getenv("SERVER_URL", "http://localhost:8000")
    REACT_APP_URL = os.getenv("REACT_APP_URL", "http://localhost:3000")

    CLIENT_ID = os.getenv("CLIENT_ID")
    CLIENT_SECRET = os.getenv("CLIENT_SECRET")
    REDIRECT_URI = f"{SERVER_URL}/oauth/callback"

    # Session configuration
    SESSION_TYPE = "filesystem"  # You can change this to "redis" if you prefer
    SESSION_FILE_DIR = os.getenv("SESSION_FILE_DIR", "./flask_session")
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = (
        os.getenv("FLASK_ENV") == "production"
    )  # Only use secure cookies in production
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_DOMAIN = None  # Allow the cookie to be valid for all subdomains
    STRIPE_PRICE_ID = "price_1PnKvQEldv3lVQeQ8sfDVHBG"
    STRIPE_SECRET_KEY = "sk_test_51Pn71vEldv3lVQeQipdKnrCEaH3wPhplvxhUDjE3KMPFb1L1cJjj1hu1tkfFgbzakx4UmAmo0bzY6nkZpR8a597h00k1IA4yBL"
    PAPERTRIAL_HOST = os.getenv("PAPERTRIAL_HOST")
    PAPERTRIAL_PORT = os.getenv("PAPERTRIAL_PORT")
