import os, json
from models import (
    Filter,
    FilterContainer,
    Account,
    ProspectingMetadata,
    Activation,
    Opportunity,
    ApiResponse,
)
from datetime import datetime

CODE_VERIFIER_FILE = "code_verifier.json"
TOKEN_FILE = "tokens.json"
SETTINGS_FILE = "settings.json"
ACTIVATIONS_FILE = "activations.json"


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
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            data = json.load(f)
            return data.get("access_token"), data.get("instance_url")
    return None, None


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


def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as file:
            settings = json.load(file, object_hook=custom_decoder)
            return settings
    return None


def save_settings(settings):
    with open(SETTINGS_FILE, "w") as file:
        json.dump(settings, file, indent=4, default=lambda x: x.__dict__)


def upsert_activations(new_activations):
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
        activation_data = {
            "id": activation.id,
            "account": {"id": activation.account.id, "name": activation.account.name},
            "activated_date": activation.activated_date.isoformat(),
            "active_contact_ids": activation.active_contact_ids,
            "first_prospecting_activity": (
                activation.first_prospecting_activity.isoformat()
                if activation.first_prospecting_activity
                else None
            ),
            "last_prospecting_activity": (
                activation.last_prospecting_activity.isoformat()
                if activation.last_prospecting_activity
                else None
            ),
            "prospecting_metadata": [
                meta.__dict__ for meta in (activation.prospecting_metadata or [])
            ],
            "days_activated": (
                activation.days_activated if activation.days_activated else 0
            ),
            "days_engaged": activation.days_engaged if activation.days_engaged else 0,
            "engaged_date": (
                activation.engaged_date.isoformat() if activation.engaged_date else None
            ),
            "last_outbound_engagement": (
                activation.last_outbound_engagement.isoformat()
                if activation.last_outbound_engagement
                else None
            ),
            "opportunity": (
                {"id": activation.opportunity.id, "name": activation.opportunity.name}
                if activation.opportunity
                else None
            ),
            "task_ids": activation.task_ids if activation.task_ids else None,
            "event_ids": activation.event_ids if activation.event_ids else None,
            "status": activation.status,
        }
        # Upsert the activation data
        activation_dict[activation.id] = activation_data

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


def load_active_activations_order_by_first_prospecting_activity_asc():
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
                prospecting_metadata = deserialize_prospecting_metadata(
                    entry.get("prospecting_metadata", [])
                )
                opportunity = deserialize_opportunity(entry.get("opportunity"))
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
        response.message = "Failed to load active activations"
        response.success = False
    return response
