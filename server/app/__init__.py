from flask import Flask
from flask_cors import CORS
from config import Config

import os

SERVER_URL = os.getenv("SERVER_URL", "http://localhost:8000")
REACT_APP_URL = os.getenv("REACT_APP_URL", "http://localhost:3000")


def create_app():
    app = Flask(__name__)
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
