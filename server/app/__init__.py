from flask import Flask
from flask_cors import CORS
from config import Config
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
import asyncio
import os
from app.salesforce_api import fetch_tasks_by_account_ids_from_date_not_in_ids

SERVER_URL = os.getenv("SERVER_URL", "http://localhost:8000")
REACT_APP_URL = os.getenv("REACT_APP_URL", "http://localhost:3000")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")


def create_app():
    app = Flask(__name__)

    if os.environ.get("FLASK_ENV") != "testing":
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
            environment=ENVIRONMENT,
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

    async def async_fetch_tasks_by_account_ids_from_date_not_in_ids(
        account_ids, start, criteria, already_counted_task_ids, salesforce_user_ids
    ):
        return await fetch_tasks_by_account_ids_from_date_not_in_ids(
            account_ids, start, criteria, already_counted_task_ids, salesforce_user_ids
        )

    def run_async_task_fetcher(*args):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            async_fetch_tasks_by_account_ids_from_date_not_in_ids(*args)
        )
        loop.close()
        return result

    app.async_fetch_tasks_by_account_ids_from_date_not_in_ids = run_async_task_fetcher

    return app
