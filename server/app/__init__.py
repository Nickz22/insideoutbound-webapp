from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from config import Config

db = SQLAlchemy()
server_session = Session()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize SQLAlchemy
    db.init_app(app)

    # Configure and initialize Flask-Session
    app.config["SESSION_TYPE"] = "sqlalchemy"
    app.config["SESSION_SQLALCHEMY"] = db
    server_session.init_app(app)

    CORS(
        app,
        resources={
            r"/*": {
                "origins": [app.config["BASE_SERVER_URL"], app.config["REACT_APP_URL"]]
            }
        },
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    )

    with app.app_context():
        # Import models
        from app import models

        # Create all tables
        db.create_all()

    # Import and register blueprints
    from app.routes import bp

    app.register_blueprint(bp)

    @app.after_request
    def add_header(response):
        response.headers["Content-Security-Policy"] = (
            "default-src 'self' https://*.ngrok-free.app; "
            "script-src 'self' 'unsafe-inline' https://*.ngrok-free.app; "
            "style-src 'self' 'unsafe-inline' https://*.ngrok-free.app"
        )
        return response

    return app
