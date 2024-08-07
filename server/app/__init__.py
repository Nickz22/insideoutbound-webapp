from flask import Flask
from flask_cors import CORS
from config import Config
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

import os

SERVER_URL = os.getenv("SERVER_URL", "http://localhost:8000")
REACT_APP_URL = os.getenv("REACT_APP_URL", "http://localhost:3000")


def create_app():
    app = Flask(__name__)

    sentry_sdk.init(
        integrations=[FlaskIntegration()],
        dsn="https://068431a7f1d4b25d48014f759db6d5ca@o4507733909766144.ingest.us.sentry.io/4507733911994368",
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        traces_sample_rate=1.0,
        # Set profiles_sample_rate to 1.0 to profile 100%
        # of sampled transactions.
        # We recommend adjusting this value in production.
        profiles_sample_rate=1.0,
        environment="development",
    )

    app.config.from_object(Config)

    CORS(
        app,
        resources={
            r"/*": {"origins": [app.config["SERVER_URL"], app.config["REACT_APP_URL"]]}
        },
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization", "x-session-token"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    )

    # Import and register blueprints
    from app.routes import bp

    app.register_blueprint(bp)

    @app.after_request
    def add_header(response):
        response.headers["Content-Security-Policy"] = (
            f"default-src 'self' {SERVER_URL} {REACT_APP_URL}; "
            f"script-src 'self' 'unsafe-inline' {SERVER_URL} {REACT_APP_URL}; "
            f"style-src 'self' 'unsafe-inline' {SERVER_URL} {REACT_APP_URL}"
        )
        return response

    return app
