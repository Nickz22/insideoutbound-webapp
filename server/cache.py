import os, json
from server.constants import SESSION_EXPIRED
from datetime import datetime, date

APP_ENV = "production"
if "APP_ENV" in os.environ:
    APP_ENV = os.environ["APP_ENV"]
from server.models import (
    Filter,
    FilterContainer,
    Account,
    ProspectingMetadata,
    Activation,
    Opportunity,
    ApiResponse,
    Settings,
)
from datetime import datetime
from server.utils import format_error_message

CODE_VERIFIER_FILE = (
    "code_verifier.json" if APP_ENV != "test" else "test_code_verifier.json"
)
TOKEN_FILE = "tokens.json" if APP_ENV != "test" else "test_tokens.json"
SETTINGS_FILE = "settings.json" if APP_ENV != "test" else "test_settings.json"
ACTIVATIONS_FILE = "activations.json" if APP_ENV != "test" else "test_activations.json"


def save_code_verifier(code_verifier):
    with open(CODE_VERIFIER_FILE, "w") as f:
        json.dump({"code_verifier": code_verifier}, f)


def load_code_verifier():
    if os.path.exists(CODE_VERIFIER_FILE):
        with open(CODE_VERIFIER_FILE, "r") as f:
            data = json.load(f)
            return data.get("code_verifier")
    return None


def save_tokens(access_token, instance_url):
    with open(TOKEN_FILE, "w") as f:
        json.dump({"access_token": access_token, "instance_url": instance_url}, f)


def load_tokens():
    response = None, None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            data = json.load(f)
            response = data.get("access_token"), data.get("instance_url")
    return response


def custom_decoder(obj):
    if "filters" in obj and "name" in obj and "filter_logic" in obj:
        return FilterContainer(
            name=obj["name"], filters=obj["filters"], filter_logic=obj["filter_logic"]
        )
    if "field" in obj and "data_type" in obj and "operator" in obj and "value" in obj:
        return Filter(
            field=obj["field"],
            data_type=obj["data_type"],
            operator=obj["operator"],
            value=obj["value"],
        )
    return obj


def load_settings() -> Settings:
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as file:
            settings = json.load(file, object_hook=custom_decoder)
            settings = Settings(**settings)
            return settings
    return None


def save_settings(settings):
    def default_converter(o):
        if isinstance(o, date):
            return o.isoformat()
        return o.__dict__

    with open(SETTINGS_FILE, "w") as file:
        json.dump(settings, file, indent=4, default=default_converter)


def upsert_activations(new_activations: list[Activation]):
    # Load existing activations from the file if it exists
    if os.path.exists(ACTIVATIONS_FILE):
        with open(ACTIVATIONS_FILE, "r") as file:
            try:
                activations = json.load(file)
            except json.JSONDecodeError:
                activations = []
    else:
        activations = []

    # Convert list of dictionaries to dictionary of dictionaries indexed by 'id'
    activation_dict = {act["id"]: act for act in activations}

    # Update existing or add new activations
    for activation in new_activations:
        activation_dict[activation.id] = activation.to_dict()

    # Write updated/ new data back to the file
    with open(ACTIVATIONS_FILE, "w") as file:
        json.dump(list(activation_dict.values()), file, indent=4)


def deserialize_account(data):
    return Account(id=data["id"], name=data["name"])


def deserialize_prospecting_metadata(data):
    return [ProspectingMetadata(**meta) for meta in data]


def deserialize_opportunity(data):
    if data:
        return Opportunity(id=data["id"], name=data["name"])
    return None


def load_inactive_activations() -> ApiResponse:
    response = ApiResponse(data=[], message="", success=False)
    try:
        file_path = ACTIVATIONS_FILE
        with open(file_path, "r") as file:
            data = json.load(file)
            activations = []
            for entry in data:
                if entry.get("status") == "Unresponsive":
                    account = deserialize_account(entry["account"])
                    prospecting_metadata = None
                    if entry.get("prospecting_metadata"):
                        prospecting_metadata = deserialize_prospecting_metadata(
                            entry.get("prospecting_metadata", [])
                        )

                    activation = Activation(
                        id=entry["id"],
                        account=account,
                        activated_date=datetime.fromisoformat(entry["activated_date"]),
                        active_contact_ids=entry["active_contact_ids"],
                        prospecting_metadata=prospecting_metadata,
                        days_activated=entry.get("days_activated"),
                        days_engaged=entry.get("days_engaged"),
                        engaged_date=(
                            datetime.fromisoformat(entry["engaged_date"])
                            if entry.get("engaged_date")
                            else None
                        ),
                        last_outbound_engagement=(
                            datetime.fromisoformat(entry["last_outbound_engagement"])
                            if entry.get("last_outbound_engagement")
                            else None
                        ),
                        first_prospecting_activity=(
                            datetime.fromisoformat(entry["first_prospecting_activity"])
                            if "first_prospecting_activity" in entry
                            else None
                        ),
                        last_prospecting_activity=datetime.fromisoformat(
                            entry["last_prospecting_activity"]
                        ),
                        task_ids=(entry["task_ids"] if "task_ids" in entry else None),
                        event_ids=(
                            entry.get("event_ids") if "event_ids" in entry else None
                        ),
                        opportunity=(
                            entry.get("opportunity") if "opportunity" in entry else None
                        ),
                        status=entry.get("status", "Activated"),
                    )
                    activations.append(activation)
            response.data = activations
            response.success = True
    except Exception as e:
        raise Exception(format_error_message(e))
    return response


def load_active_activations_order_by_first_prospecting_activity_asc() -> ApiResponse:
    """
    Loads active activations from a JSON file, orders them by the date of the first prospecting activity in ascending order,
    and returns them as a list of Activation objects wrapped in an ApiResponse object.

    Signature:
        None -> ApiResponse

    Returns:
        ApiResponse: An object containing a list of Activation objects (data), a message, and a success flag.
                     The success flag is True if the data was loaded and processed successfully, False otherwise.

    Throws:
        Exception: Raises an exception with a formatted error message if any error occurs during file reading,
                   JSON parsing, or data processing.
    """
    response = ApiResponse(data=[], message="", success=False)
    try:

        file_path = ACTIVATIONS_FILE
        with open(file_path, "r") as file:
            data = json.load(file)
            activations = []
            for entry in data:
                if entry.get("status") == "Unresponsive":
                    continue

                account = deserialize_account(entry["account"])
                prospecting_metadata = None
                if entry.get("prospecting_metadata"):
                    prospecting_metadata = deserialize_prospecting_metadata(
                        entry.get("prospecting_metadata", [])
                    )

                activation = Activation(
                    id=entry["id"],
                    account=account,
                    activated_date=datetime.fromisoformat(entry["activated_date"]),
                    active_contact_ids=entry["active_contact_ids"],
                    prospecting_metadata=prospecting_metadata,
                    days_activated=entry.get("days_activated"),
                    days_engaged=entry.get("days_engaged"),
                    engaged_date=(
                        datetime.fromisoformat(entry["engaged_date"])
                        if entry.get("engaged_date")
                        else None
                    ),
                    last_outbound_engagement=(
                        datetime.fromisoformat(entry["last_outbound_engagement"])
                        if entry.get("last_outbound_engagement")
                        else None
                    ),
                    first_prospecting_activity=(
                        datetime.fromisoformat(entry["first_prospecting_activity"])
                        if "first_prospecting_activity" in entry
                        else None
                    ),
                    last_prospecting_activity=datetime.fromisoformat(
                        entry["last_prospecting_activity"]
                    ),
                    task_ids=(entry["task_ids"] if "task_ids" in entry else None),
                    event_ids=(
                        entry.get("event_ids") if "event_ids" in entry else None
                    ),
                    opportunity=(
                        entry.get("opportunity") if "opportunity" in entry else None
                    ),
                    status=entry.get("status", "Activated"),
                )
                activations.append(activation)

            # Order activations by first_prospecting_activity ascending
            activations.sort(key=lambda x: x.first_prospecting_activity)
            response.data = activations
            response.success = True

    except Exception as e:
        raise Exception(format_error_message(e))
    return response
