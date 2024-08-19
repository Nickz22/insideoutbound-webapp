import requests, json
from flask import Blueprint, jsonify, redirect, request
from urllib.parse import unquote
from app.middleware import authenticate
from app.utils import format_error_message, log_error
from app.database.activation_selector import (
    load_active_activations_order_by_first_prospecting_activity_asc,
)
from app.database.settings_selector import load_settings
from app.database.supabase_user_selector import fetch_supabase_user
from app.database.dml import (
    save_settings,
    save_session,
    delete_all_activations,
    upsert_supabase_user,
)
from app.constants import SESSION_EXPIRED
from app.mapper.mapper import (
    convert_filter_container_model_to_filter_container,
    convert_settings_model_to_settings,
    convert_settings_to_settings_model,
)
from app.helpers.activation_helper import generate_summary
from app.services.setting_service import define_criteria_from_events_or_tasks
from app.engine.activation_engine import update_activation_states
from app.salesforce_api import (
    fetch_criteria_fields,
    fetch_task_fields,
    fetch_event_fields,
    fetch_salesforce_users,
    fetch_tasks_by_user_ids,
    fetch_events_by_user_ids,
    fetch_logged_in_salesforce_user,
    get_task_query_count,
)
from config import Config
from app.database.supabase_connection import (
    get_supabase_admin_client,
    get_session_state,
)
from app.database.session_selector import fetch_supabase_session
import stripe

stripe.api_key = Config.STRIPE_SECRET_KEY

bp = Blueprint("main", __name__)


@bp.route("/oauth/callback", methods=["GET"])
def oauth_callback():
    from app.data_models import UserModel

    try:
        code = request.args.get("code")
        state = request.args.get("state")

        if not code or not state:
            return jsonify({"error": "Missing authorization code or state"}), 400

        try:
            state_data = json.loads(unquote(state))
            code_verifier = state_data["codeVerifier"]
            is_sandbox = state_data["isSandbox"]
        except (json.JSONDecodeError, KeyError):
            return jsonify({"error": "Invalid state parameter"}), 400

        base_sf_domain = "test" if is_sandbox else "login"
        token_url = f"https://{base_sf_domain}.salesforce.com/services/oauth2/token"

        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": Config.REDIRECT_URI,
            "client_id": Config.CLIENT_ID,
            "client_secret": Config.CLIENT_SECRET,
            "code_verifier": code_verifier,
        }

        response = requests.post(token_url, data=payload)
        if response.status_code == 200:
            token_data = response.json()
            session_token = save_session(token_data, is_sandbox)
            user: UserModel = fetch_logged_in_salesforce_user().data
            settings = load_settings()
            if not settings:
                upsert_supabase_user(user=user, is_sandbox=is_sandbox)
                return redirect(
                    f"{Config.REACT_APP_URL}/onboard?session_token={session_token}"
                )
            else:
                return redirect(
                    f"{Config.REACT_APP_URL}/app/prospecting?session_token={session_token}"
                )
        else:
            error_details = {
                "error": "Failed to retrieve access token",
                "status_code": response.status_code,
                "response_text": response.text,
            }
            return jsonify(error_details), 500
    except Exception as e:
        log_error(e)
        error_msg = f"Failed to retrieve access token: {format_error_message(e)}"
        return jsonify({"error": error_msg}), 500


@bp.route("/logout", methods=["POST"])
@authenticate
def logout():
    from app.data_models import ApiResponse

    api_response = ApiResponse(data=[], message="", success=False)
    admin_supabase = get_supabase_admin_client()
    admin_supabase.auth.sign_out()

    api_response.success = True
    api_response.message = "Logged out successfully"
    return jsonify(api_response.to_dict()), 200


@bp.route("/refresh_token", methods=["POST"])
def refresh_token():
    from app.data_models import ApiResponse

    response = ApiResponse(data=[], message="", success=False)
    session_token = request.headers.get("X-Session-Token")
    session = fetch_supabase_session(session_token)
    session_state = json.loads(session["state"])

    if "refresh_token" not in session_state:
        response.message = "No refresh token found, please login."
        response.type = "AuthenticationError"
        return jsonify(response.to_dict()), 200

    base_sf_domain = "test" if session_state.get("is_sandbox") else "login"
    token_url = f"https://{base_sf_domain}.salesforce.com/services/oauth2/token"
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": session_state["refresh_token"],
        "client_id": Config.CLIENT_ID,
        "client_secret": Config.CLIENT_SECRET,
    }

    try:
        response_sf = requests.post(token_url, data=payload)
        response_sf.raise_for_status()
        token_data = response_sf.json()
        token_data["refresh_token"] = session_state["refresh_token"]

        session_token = save_session(token_data, session_state["is_sandbox"])
        response.data = [{"session_token": session_token}]
        response.success = True
        response.message = "Token refreshed successfully"
    except requests.exceptions.RequestException as e:
        log_error(e)
        error_msg = format_error_message(e)
        response.message = f"Failed to refresh token: {str(error_msg)}"
        response.type = "AuthenticationError"

    return jsonify(response.to_dict()), 200


@bp.route("/get_criteria_fields", methods=["GET"])
@authenticate
def get_criteria_fields():
    from app.data_models import ApiResponse

    try:
        response = ApiResponse(data=[], message="", success=False)
        object_type = request.args.get("object")
        criteria_fields = fetch_criteria_fields(sobject_type=object_type)

        if not criteria_fields.success:
            response.message = criteria_fields.message
        else:
            response.data = criteria_fields.data
            response.success = True
    except Exception as e:
        log_error(e)
        response.success = False
        response.message = (
            f"Failed to retrieve event criteria fields: {format_error_message(e)}"
        )

    return (
        jsonify(response.to_dict()),
        get_status_code(response),
    )


@bp.route("/generate_filters", methods=["POST"])
@authenticate
def generate_filters():
    from app.data_models import ApiResponse, TableColumn

    response = ApiResponse(data=[], message="", success=True)
    final_response = None
    try:
        data = request.json
        records = data.get("tasksOrEvents")
        columns = [TableColumn(**column) for column in data.get("selectedColumns")]
        if not records or len(records) == 0:
            response.success = False
            response.message = "No tasks provided"
        else:
            response.data = [
                define_criteria_from_events_or_tasks(
                    records,
                    columns,
                    fetch_criteria_fields(
                        "Task" if records[0]["Id"].startswith("00T") else "Event"
                    ).data,
                )
            ]

        final_response = jsonify(response.to_dict()), 200 if response.success else 400
    except Exception as e:
        log_error(e)
        response.success = False
        response.message = f"Failed to generate filters: {format_error_message(e)}"
        final_response = jsonify(response.to_dict()), 500

    return final_response


# get_instance_url
@bp.route("/get_instance_url", methods=["GET"])
@authenticate
def get_instance_url():
    from app.data_models import ApiResponse

    response = ApiResponse(data=[], message="", success=False)
    try:
        response.data = [get_session_state().get("instance_url")]
        response.success = True
    except Exception as e:
        log_error(e)
        response.message = f"Failed to retrieve instance URL: {format_error_message(e)}"

    return jsonify(response.to_dict()), get_status_code(response)


@bp.route("/get_prospecting_activities", methods=["GET"])
@authenticate
def get_prospecting_activities():
    from app.data_models import ApiResponse

    response = ApiResponse(data=[], message="", success=False)
    try:
        query_response = (
            load_active_activations_order_by_first_prospecting_activity_asc()
        )
        if not query_response.success:
            raise Exception(query_response.message)
        response.data = [
            {
                "summary": generate_summary(query_response.data),
                "raw_data": [
                    activation.to_dict() for activation in query_response.data
                ],
            }
        ]
        response.success = True
    except Exception as e:
        log_error(e)
        response.message = (
            f"Failed to retrieve prospecting activities: {format_error_message(e)}"
        )
        response.type = "UnexpectedError"

    return jsonify(response.to_dict()), 200


@bp.route("/get_prospecting_activities_filtered_by_ids", methods=["GET"])
@authenticate
def get_prospecting_activities_filtered_by_ids():
    from app.data_models import ApiResponse

    response = ApiResponse(data=[], message="", success=False)
    try:
        activation_ids = request.args.getlist("activation_ids[]")
        if not activation_ids:
            response.data = {
                "total_activations": len(activations),
                "activations_today": 0,
                "total_tasks": 0,
                "total_events": 0,
                "total_contacts": 0,
                "total_accounts": 0,
                "total_deals": 0,
                "total_pipeline_value": 0,
            }
            response.success = True
        else:
            activations = (
                load_active_activations_order_by_first_prospecting_activity_asc().data
            )
            filtered_activations = [
                activation
                for activation in activations
                if activation.id in activation_ids
            ]
            response.data = [
                {
                    "summary": generate_summary(filtered_activations),
                    "raw_data": [
                        activation.to_dict() for activation in filtered_activations
                    ],
                }
            ]
            response.success = True
    except Exception as e:
        log_error(e)
        response.message = (
            f"Failed to retrieve prospecting activities: {format_error_message(e)}"
        )

    return jsonify(response.to_dict()), get_status_code(response)


@bp.route("/fetch_prospecting_activity", methods=["POST"])
@authenticate
def fetch_prospecting_activity():
    from app.data_models import ApiResponse

    api_response = ApiResponse(data=[], message="", success=False)
    try:
        response = update_activation_states()

        if response.success:
            activations = response.data

            api_response.data = [
                {
                    "summary": generate_summary(activations),
                    "raw_data": [activation.to_dict() for activation in activations],
                }
            ]
            api_response.success = True
            api_response.message = "Prospecting activity data loaded successfully"
        else:
            api_response.message = response.message

        status_code = get_status_code(api_response)
    except Exception as e:
        log_error(e)
        api_response.message = (
            f"Failed to load prospecting activities data: {format_error_message(e)}"
        )
        status_code = get_status_code(api_response)

    return jsonify(api_response.to_dict()), status_code


@bp.route("/delete_all_prospecting_activity", methods=["POST"])
@authenticate
def delete_all_prospecting_activity():
    from app.data_models import ApiResponse

    response = ApiResponse(data=[], message="", success=False)
    try:
        delete_all_activations()
        response.success = True
    except Exception as e:
        log_error(e)
        response.message = (
            f"Failed to delete prospecting activity: {format_error_message(e)}"
        )

    return jsonify(response.to_dict()), get_status_code(response)


@bp.route("/save_settings", methods=["POST"])
@authenticate
def commit_settings():
    from app.data_models import SettingsModel, ApiResponse

    api_response = ApiResponse(data=[], message="", success=False)
    try:
        data = request.json
        settings = convert_settings_model_to_settings(SettingsModel(**data))
        save_settings(settings)
        api_response.success = True
        api_response.message = "Settings saved successfully"
    except Exception as e:
        log_error(e)
        error_msg = format_error_message(e)
        api_response.message = f"Failed to save settings: {error_msg}"

    return jsonify(api_response.to_dict()), 200


@bp.route("/get_settings", methods=["GET"])
@authenticate
def get_settings():
    from app.data_models import SettingsModel, ApiResponse

    api_response = ApiResponse(data=[], message="", success=False)

    try:
        settings = load_settings()
        settings_model: SettingsModel = convert_settings_to_settings_model(settings)
        api_response.data = [settings_model.to_dict()]
        api_response.success = True
        return jsonify(api_response.to_dict()), 200
    except Exception as e:
        log_error(e)
        api_response.message = f"Failed to retrieve settings: {str(e)}"

    return api_response


@bp.route("/get_salesforce_users", methods=["GET"])
@authenticate
def get_salesforce_users():
    from app.data_models import ApiResponse

    response = ApiResponse(data=[], message="", success=False)
    try:
        response.data = fetch_salesforce_users().data
        response.success = True
    except Exception as e:
        log_error(e)
        error_message = format_error_message(e)
        response.message = f"Failed to retrieve Salesforce users: {error_message}"

    return jsonify(response.to_dict()), get_status_code(response)


@bp.route("/get_salesforce_tasks_by_user_ids", methods=["GET"])
@authenticate
def get_salesforce_tasks_by_user_ids():
    from app.data_models import ApiResponse

    response = ApiResponse(data=[], message="", success=False)
    try:
        user_ids = request.args.getlist("user_ids[]")

        if not user_ids:
            response.message = "No user IDs provided"
        else:
            response.data = fetch_tasks_by_user_ids(user_ids, 1000).data
            response.success = True
    except Exception as e:
        log_error(e)
        error_msg = format_error_message(e)
        response.message = (
            f"Failed to retrieve Salesforce tasks by user IDs: {error_msg}"
        )

    return jsonify(response.to_dict()), get_status_code(response)


@bp.route("/get_salesforce_events_by_user_ids", methods=["GET"])
@authenticate
def get_salesforce_events_by_user_ids():
    from app.data_models import ApiResponse

    response = ApiResponse(data=[], message="", success=False)
    try:
        user_ids = request.args.getlist("user_ids[]")

        if not user_ids:
            response.message = "No user IDs provided"
        else:
            response.data = fetch_events_by_user_ids(user_ids, 1000).data
            response.success = True
    except Exception as e:
        log_error(e)
        response.message = f"Failed to retrieve Salesforce events by user IDs: {format_error_message(e)}"

    return jsonify(response.__dict__), get_status_code(response)


@bp.route("/get_salesforce_user", methods=["GET"])
@authenticate
def get_salesforce_user():
    from app.data_models import ApiResponse, UserModel

    response = ApiResponse(data=[], message="", success=False)
    try:
        user: UserModel = fetch_logged_in_salesforce_user().data
        supabase_user: UserModel = fetch_supabase_user(user.id)
        user.status = supabase_user.status
        response.data = [user.to_dict()]
        response.success = True
    except Exception as e:
        log_error(e)
        response.message = (
            f"Failed to retrieve Salesforce users: {format_error_message(e)}"
        )

    return jsonify(response.to_dict()), get_status_code(response)


@bp.route("/pause_stripe_payment_schedule", methods=["POST"])
@authenticate
def pause_stripe_payment_schedule():
    from app.data_models import ApiResponse, UserModel

    api_response = ApiResponse(data=[], message="", success=False)

    try:
        user_email = request.json.get("email")
        user_id = request.json.get("userId")

        if not user_email:
            api_response.message = "User email is required"
            return jsonify(api_response.to_dict()), 400

        # Find the Stripe customer by email
        customers = stripe.Customer.list(email=user_email, limit=1)

        if not customers.data:
            api_response.message = "Stripe customer not found"
            return jsonify(api_response.to_dict()), 404

        stripe_customer = customers.data[0]

        # Fetch the customer's subscriptions
        subscriptions = stripe.Subscription.list(customer=stripe_customer.id)

        if not subscriptions.data:
            api_response.message = "No active subscriptions found"
            return jsonify(api_response.to_dict()), 404

        # Pause the first active subscription
        subscription = subscriptions.data[0]
        updated_subscription = stripe.Subscription.modify(
            subscription.id,
            pause_collection={
                "behavior": "void",
            },
        )

        # Update the user's status in your database
        upsert_supabase_user(
            UserModel(id=user_id, status="paused"),
            is_sandbox=get_session_state()["is_sandbox"],
        )

        api_response.success = True
        api_response.message = "Subscription paused successfully"
        api_response.data = [{"subscription_id": updated_subscription.id}]
        return jsonify(api_response.to_dict()), 200

    except stripe.error.StripeError as e:
        log_error(e)
        api_response.message = f"Stripe error: {str(e)}"
        return jsonify(api_response.to_dict()), 400
    except Exception as e:
        log_error(e)
        api_response.message = f"An error occurred: {format_error_message(e)}"
        return jsonify(api_response.to_dict()), 500


@bp.route("/get_task_fields", methods=["GET"])
@authenticate
def get_task_fields():
    from app.data_models import ApiResponse

    response = ApiResponse(data=[], message="", success=False)
    try:
        response.data = fetch_task_fields().data
        response.success = True
    except Exception as e:
        log_error(e)
        error_msg = format_error_message(e)
        response.message = f"Failed to retrieve task fields: {error_msg}"

    return jsonify(response.to_dict()), get_status_code(response)


@bp.route("/get_event_fields", methods=["GET"])
@authenticate
def get_event_fields():
    from app.data_models import ApiResponse

    response = ApiResponse(data=[], message="", success=False)
    try:
        response = fetch_event_fields()
    except Exception as e:
        log_error(e)
        response.message = f"Failed to retrieve event fields: {format_error_message(e)}"

    return jsonify(response.__dict__), get_status_code(response)


@bp.route("/get_task_query_count", methods=["POST"])
@authenticate
def task_query_count():
    from app.data_models import ApiResponse, FilterContainerModel

    api_response = ApiResponse(data=[], message="", success=False)
    try:
        data = request.json
        criteria = convert_filter_container_model_to_filter_container(
            FilterContainerModel(**data.get("criteria"))
        )
        salesforce_user_ids = data.get("salesforce_user_ids", [])

        api_response = get_task_query_count(criteria, salesforce_user_ids)
        api_response.success = True

    except Exception as e:
        log_error(e)
        api_response.message = (
            f"Failed to retrieve task query count: {format_error_message(e)}"
        )

    return jsonify(api_response.to_dict()), get_status_code(api_response)


@bp.route("/create-payment-intent", methods=["POST"])
@authenticate
def create_payment_intent():
    from app.data_models import ApiResponse

    try:
        api_response = ApiResponse(data=[], message="", success=False)
        intent = stripe.PaymentIntent.create(
            amount=2000,  # Amount in cents
            currency="usd",
            automatic_payment_methods={"enabled": True},
        )
        api_response.success = True
        api_response.data = [{"clientSecret": intent.client_secret}]
        return jsonify(api_response.to_dict()), 200
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 400


@bp.route("/start_stripe_payment_schedule", methods=["POST"])
@authenticate
def start_stripe_payment_schedule():
    from app.data_models import ApiResponse

    api_response = ApiResponse(data=[], message="", success=False)

    try:
        # Get the current user's email
        user_email = request.get_json().get("userEmail")

        # Check if customer already exists
        existing_customers = stripe.Customer.list(email=user_email, limit=1)

        if existing_customers.data:
            # Use existing customer
            customer = existing_customers.data[0]
        else:
            # Create a new customer in Stripe
            customer = stripe.Customer.create(email=user_email)

        # Check if customer already has an active subscription
        existing_subscriptions = stripe.Subscription.list(
            customer=customer.id, status="active", limit=1
        )

        if existing_subscriptions.data:
            api_response.message = "Customer already has an active subscription"
            api_response.success = True
            api_response.data = [
                {
                    "subscriptionId": existing_subscriptions.data[0].id,
                    "alreadySubscribed": True,
                }
            ]
        else:
            # Create a subscription
            subscription = stripe.Subscription.create(
                customer=customer.id,
                items=[
                    {"price": Config.STRIPE_PRICE_ID},
                ],
                payment_behavior="default_incomplete",
                expand=["latest_invoice.payment_intent"],
            )

            api_response.success = True
            api_response.message = "Subscription created successfully"
            api_response.data = [
                {
                    "subscriptionId": subscription.id,
                    "clientSecret": subscription.latest_invoice.payment_intent.client_secret,
                    "alreadySubscribed": False,
                }
            ]

    except stripe.error.StripeError as e:
        log_error(e)
        api_response.message = f"Stripe error: {str(e)}"
        return jsonify(api_response.to_dict()), 400

    except Exception as e:
        log_error(e)
        api_response.message = f"Unexpected error: {format_error_message(e)}"
        return jsonify(api_response.to_dict()), 500

    return jsonify(api_response.to_dict()), 200


@bp.route("/set_supabase_user_status_to_paid", methods=["POST"])
@authenticate
def set_supabase_user_status_to_paid():
    from app.data_models import ApiResponse, UserModel

    api_response = ApiResponse(data=[], message="", success=False)

    try:
        session_state = get_session_state()
        user_id = request.get_json().get("userId")
        user_model = UserModel(id=user_id, status="paid")
        upsert_supabase_user(user=user_model, is_sandbox=session_state["is_sandbox"])
        api_response.success = True
    except Exception as e:
        log_error(e)
        api_response.message = (
            f"Failed to set user status to paid: {format_error_message(e)}"
        )

    return jsonify(api_response.to_dict()), get_status_code(api_response)


@bp.app_errorhandler(Exception)
def handle_exception(e):
    from app.data_models import AuthenticationError

    error_msg = format_error_message(e)
    print(error_msg)
    if isinstance(e, AuthenticationError):
        return jsonify({"error": str(e), "type": "AuthenticationError"}), 200
    return (
        jsonify({"error": error_msg, "type": type(e).__name__}),
        500,
    )


@bp.app_errorhandler(404)
def not_found_error(error):
    return jsonify({"error": f"Not Found {error}"}), 404


@bp.app_errorhandler(500)
def internal_error(error):
    return jsonify({"error": f"Internal Server Error {error}"}), 500


# helpers
def get_status_code(response):
    return (
        200 if response.success else 400 if SESSION_EXPIRED in response.message else 503
    )
