from flask import Flask
from flask_cors import CORS
from config import Config


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(
        app,
        resources={
            r"/*": {
                "origins": [app.config["BASE_SERVER_URL"], app.config["REACT_APP_URL"]]
            }
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
            "default-src 'self' https://*.ngrok-free.app; "
            "script-src 'self' 'unsafe-inline' https://*.ngrok-free.app; "
            "style-src 'self' 'unsafe-inline' https://*.ngrok-free.app"
        )
        return response

    return app
