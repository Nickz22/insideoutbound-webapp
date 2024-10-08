from app.data_models import (
    Account,
    Contact,
    Settings,
    FilterContainer,
    Filter,
    FilterContainerModel,
    FilterModel,
    SettingsModel,
    Opportunity,
    Activation,
    ProspectingMetadata,
    ProspectingEffort,
    UserModel,
)
from typing import Dict
from dateutil import parser
from datetime import datetime, date
import json
from uuid import UUID
from app.utils import (
    surround_numbers_with_underscores,
    remove_underscores_from_numbers,
)
import pytz


def convert_dict_to_opportunity(opportunity_dict: Dict) -> Opportunity:
    id = opportunity_dict.get("Id")
    name = opportunity_dict.get("Name")
    amount = float(opportunity_dict.get("Amount") or 0.0)
    close_date_str = opportunity_dict.get("CloseDate")
    close_date = date.fromisoformat(close_date_str) if close_date_str else None
    stage = opportunity_dict.get("StageName")
    created_date_str = opportunity_dict.get("CreatedDate")
    created_date = datetime.strptime(created_date_str, "%Y-%m-%dT%H:%M:%S.%f%z").date() if created_date_str else None

    return Opportunity(
        id=id, name=name, amount=amount, close_date=close_date, stage=stage, created_date=created_date
    )


def convert_dict_to_filter(f: Dict) -> Filter:
    # Convert camelCase to snake_case for data_type
    f["data_type"] = f.pop("data_type")
    # Convert options to string if it exists
    if "options" in f and f["options"] is not None:
        f["options"] = json.dumps(f["options"])
    return Filter(**f)


def convert_dict_to_filter_container(fc: Dict) -> FilterContainer:
    # Convert camelCase to snake_case for filter_logic
    fc["filter_logic"] = fc.pop("filter_logic")
    # Convert each filter in the filters list
    fc["filters"] = [convert_dict_to_filter(f) for f in fc["filters"]]
    fc["direction"] = fc.get("direction", None)
    return FilterContainer(**fc)


def supabase_dict_to_python_settings(row: Dict) -> Settings:
    # Convert JSON strings back to Python objects
    if "criteria" in row and row["criteria"]:
        criteria_list = json.loads(row["criteria"])
        row["criteria"] = [convert_dict_to_filter_container(fc) for fc in criteria_list]

    # Handle other fields similarly
    for field in [
        "meetings_criteria",
        "skip_account_criteria",
        "skip_opportunity_criteria",
    ]:
        if field in row and row[field]:
            fc = json.loads(row[field])
            row[field] = convert_dict_to_filter_container(fc)

    # Convert ISO format string to datetime and apply user's time zone
    if "latest_date_queried" in row and row["latest_date_queried"]:
        utc_time = parser.isoparse(row["latest_date_queried"])
        if "user_time_zone" in row and row["user_time_zone"]:
            user_tz = pytz.timezone(row["user_time_zone"])
            row["latest_date_queried"] = utc_time.replace(tzinfo=pytz.UTC).astimezone(
                user_tz
            )
        else:
            row["latest_date_queried"] = utc_time

    # Convert team_member_ids from JSON string to list if it's not None
    if "team_member_ids" in row and row["team_member_ids"]:
        if isinstance(row["team_member_ids"], str):
            row["team_member_ids"] = json.loads(row["team_member_ids"])

    row["skip_account_criteria"] = (
        None if row["skip_account_criteria"] == "" else row["skip_account_criteria"]
    )
    row["skip_opportunity_criteria"] = (
        None
        if row["skip_opportunity_criteria"] == ""
        else row["skip_opportunity_criteria"]
    )

    return Settings(**row)


def convert_filter_to_dict(f: Filter) -> Dict:
    f_dict = f.to_dict()
    f_dict["dataType"] = f_dict.pop("data_type")
    if "options" in f_dict and f_dict["options"] is not None:
        f_dict["options"] = json.loads(f_dict["options"])
    return f_dict


def convert_filter_container_to_dict(fc: FilterContainer) -> Dict:
    fc_dict = fc.to_dict()
    fc_dict["filterLogic"] = fc_dict.pop("filter_logic")
    fc_dict["filters"] = [convert_filter_to_dict(f) for f in fc_dict["filters"]]
    return fc_dict


def python_settings_to_supabase_dict(settings: Settings) -> Dict:
    settings_dict = settings.to_dict()

    # Convert FilterContainer objects to JSON strings
    if "criteria" in settings_dict:
        settings_dict["criteria"] = json.dumps(
            settings_dict["criteria"] if settings_dict["criteria"] else []
        )

    # Handle other fields similarly
    for field in [
        "meetings_criteria",
        "skip_account_criteria",
        "skip_opportunity_criteria",
    ]:
        if field in settings_dict and settings_dict[field]:
            settings_dict[field] = json.dumps(
                settings_dict[field] if settings_dict[field] else {}
            )

    # Convert datetime to UTC ISO format string
    if "latest_date_queried" in settings_dict and isinstance(
        settings_dict["latest_date_queried"], datetime
    ):
        utc_time = settings_dict["latest_date_queried"].astimezone(pytz.UTC)
        settings_dict["latest_date_queried"] = utc_time.isoformat()

    # Convert team_member_ids to JSON string if it's not None

    return settings_dict


def supabase_dict_to_python_activation(row: Dict) -> Activation:

    row["account"] = Account(**row["account"])

    # Convert JSON strings back to Python objects
    if "prospecting_metadata" in row and row["prospecting_metadata"]:
        row["prospecting_metadata"] = [
            ProspectingMetadata(**item)
            for item in row["prospecting_metadata"]
        ]

    if "prospecting_effort" in row and row["prospecting_effort"]:
        row["prospecting_effort"] = [
            ProspectingEffort(**item) for item in row["prospecting_effort"]
        ]

    if "active_contacts" in row and row["active_contacts"]:
        row["active_contacts"] = [
            Contact(**item) for item in row["active_contacts"]
        ]

    if "tasks" in row and row["tasks"]:
        row["tasks"] = row["tasks"]

    # Convert array fields to sets
    for field in ["active_contact_ids", "task_ids", "event_ids"]:
        if field in row and row[field]:
            row[field] = set(row[field])

    # Convert date strings to date objects
    date_fields = [
        "activated_date",
        "engaged_date",
        "first_prospecting_activity",
        "last_prospecting_activity",
        "last_outbound_engagement",
    ]
    for field in date_fields:
        if field in row and row[field]:
            row[field] = datetime.fromisoformat(row[field]).date()

    return Activation(**row)


def python_activation_to_supabase_dict(activation: Activation) -> Dict:
    activation_dict = activation.to_dict()

    activation_dict["account_id"] = activation_dict["account"]["id"]
    activation_dict["account"] = json.dumps(activation_dict["account"])
    activation_dict["created_at"] = datetime.now().isoformat()

    if "active_contact_ids" in activation_dict:
        activation_dict["active_contact_ids"] = list(
            activation_dict["active_contact_ids"]
        )

    if "active_contacts" in activation_dict:
        activation_dict["active_contacts"] = json.dumps(
            activation_dict["active_contacts"]
        )

    if "tasks" in activation_dict:
        activation_dict["tasks"] = json.dumps(activation_dict["tasks"])

    if "task_ids" in activation_dict:
        activation_dict["task_ids"] = list(activation_dict["task_ids"])

    if "event_ids" in activation_dict:
        activation_dict["event_ids"] = (
            list(activation_dict["event_ids"]) if activation_dict["event_ids"] else None
        )

    if "prospecting_metadata" in activation_dict:
        activation_dict["prospecting_metadata"] = (
            json.dumps(activation_dict["prospecting_metadata"])
            if activation_dict["prospecting_metadata"]
            else None
        )

    if "prospecting_effort" in activation_dict:
        activation_dict["prospecting_effort"] = (
            json.dumps(activation_dict["prospecting_effort"])
            if activation_dict["prospecting_effort"]
            else None
        )

    # Convert datetime, date, and UUID objects to strings
    for key, value in activation_dict.items():
        if isinstance(value, (datetime, date)):
            activation_dict[key] = value.isoformat()
        elif isinstance(value, UUID):
            activation_dict[key] = str(value)

    # Ensure only Supabase schema fields are included
    supabase_fields = [
        "id",
        "created_at",
        "account_id",
        "account",
        "activated_by_id",
        "activated_by",
        "active_contact_ids",
        "active_contacts",
        "task_ids",
        "tasks",
        "activated_date",
        "first_prospecting_activity",
        "last_prospecting_activity",
        "event_ids",
        "prospecting_metadata",
        "prospecting_effort",
        "days_activated",
        "days_engaged",
        "engaged_date",
        "last_outbound_engagement",
        "opportunity",
        "status",
    ]
    return {k: v for k, v in activation_dict.items() if k in supabase_fields}


def convert_filter_model_to_filter(fm: FilterModel) -> Filter:
    return Filter(
        field=fm.field,
        operator=fm.operator,
        value=fm.value,
        data_type=fm.dataType,
    )


def convert_filter_to_filter_model(f: dict) -> FilterModel:
    return FilterModel(
        field=f.field,
        operator=f.operator,
        value=f.value,
        dataType=f.data_type,
    )


def convert_filter_container_model_to_filter_container(
    fcm: FilterContainerModel,
) -> FilterContainer:
    if fcm is None or (isinstance(fcm, dict) and not fcm):
        return FilterContainer(name="", filters=[], filter_logic="")

    return FilterContainer(
        name=fcm.name,
        filters=[convert_filter_model_to_filter(f) for f in fcm.filters],
        filter_logic=surround_numbers_with_underscores(fcm.filterLogic),
        direction=fcm.direction,
    )


def convert_filter_container_to_filter_container_model(
    fc: dict,
) -> FilterContainerModel:
    return FilterContainerModel(
        name=fc.name,
        filters=[convert_filter_to_filter_model(f) for f in fc.filters],
        filterLogic=remove_underscores_from_numbers(fc.filter_logic),
        direction=fc.direction,
    )


def convert_settings_model_to_settings(sm: SettingsModel) -> Settings:
    return Settings(
        inactivity_threshold=sm.inactivityThreshold,
        criteria=(
            [
                convert_filter_container_model_to_filter_container(criteria)
                for criteria in sm.criteria
            ]
            if len(sm.criteria) > 0
            else [FilterContainer(name="", filters=[], filter_logic="")]
        ),
        meeting_object=sm.meetingObject,
        meetings_criteria=(
            convert_filter_container_model_to_filter_container(sm.meetingsCriteria)
            if sm.meetingsCriteria is not None
            else FilterContainer(name="", filters=[], filter_logic="")
        ),
        activities_per_contact=sm.activitiesPerContact,
        contacts_per_account=sm.contactsPerAccount,
        tracking_period=sm.trackingPeriod,
        activate_by_meeting=sm.activateByMeeting,
        activate_by_opportunity=sm.activateByOpportunity,
        team_member_ids=sm.teamMemberIds,
        salesforce_user_id=sm.salesforceUserId,
        latest_date_queried=sm.latestDateQueried,
        user_time_zone=sm.userTimeZone,
    )


def convert_settings_to_settings_model(s: Settings) -> SettingsModel:
    return SettingsModel(
        inactivityThreshold=s.inactivity_threshold,
        criteria=[
            convert_filter_container_to_filter_container_model(fc) for fc in s.criteria
        ],
        meetingObject=s.meeting_object,
        meetingsCriteria=(
            convert_filter_container_to_filter_container_model(s.meetings_criteria)
            if s.meetings_criteria is not None
            else FilterContainerModel(name="", filters=[], filterLogic="")
        ),
        activitiesPerContact=s.activities_per_contact,
        contactsPerAccount=s.contacts_per_account,
        trackingPeriod=s.tracking_period,
        activateByMeeting=s.activate_by_meeting,
        activateByOpportunity=s.activate_by_opportunity,
        teamMemberIds=s.team_member_ids,
        salesforceUserId=s.salesforce_user_id,
        latestDateQueried=s.latest_date_queried,
        userTimeZone=s.user_time_zone,
    )


def python_user_to_supabase_dict(user: UserModel) -> Dict:
    supabase_user = {
        "id": user.id,
        "salesforce_id": user.id,  # Assuming the id in UserModel is the Salesforce ID
        "email": user.email if user.email else "",
        "org_id": user.orgId if user.orgId else "",
        "is_sandbox": None,  # This information is not present in UserModel
        "photo_url": user.photoUrl if user.photoUrl else "",
        "status": user.status or "not paid",
    }

    # Remove None values
    return {k: v for k, v in supabase_user.items() if v is not None}


def supabase_user_to_python_user(row: Dict) -> UserModel:
    return UserModel(
        id=row["salesforce_id"],
        email=row["email"],
        orgId=row["org_id"],
        photoUrl=row["photo_url"],
        status=row["status"],
        created_at=(
            datetime.fromisoformat(row["created_at"]) if row["created_at"] else None
        ),
    )
