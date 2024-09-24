from pydantic import BaseModel, Field
from typing import List, Optional, Set, Any, Union, Dict
from datetime import date, datetime
from enum import Enum
import re


def serialize_complex_types(obj: Any) -> Any:
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    elif isinstance(obj, set):
        return list(obj)
    elif isinstance(obj, SerializableModel):
        return obj.to_dict()
    elif isinstance(obj, list):
        return [serialize_complex_types(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: serialize_complex_types(value) for key, value in obj.items()}
    else:
        return obj


class SerializableModel(BaseModel):
    def to_dict(self) -> dict:
        return {
            key: serialize_complex_types(value)
            for key, value in self.model_dump().items()
        }


class UserSObject(SerializableModel):
    Id: str
    Email: Optional[str] = None
    Username: Optional[str] = None
    LastName: Optional[str] = None
    FullPhotoUrl: Optional[str] = None
    FirstName: Optional[str] = None
    Role: Optional[str] = None


class UserModel(SerializableModel):
    id: str
    email: Optional[str] = None
    username: Optional[str] = None
    lastName: Optional[str] = None
    photoUrl: Optional[str] = None
    orgId: Optional[str] = None
    firstName: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = "not paid"
    created_at: Optional[datetime] = None

    @classmethod
    def from_sobject(cls, sobject: UserSObject):
        return cls(
            id=sobject.Id,
            email=sobject.Email,
            username=sobject.Username,
            firstName=sobject.FirstName,
            lastName=sobject.LastName,
            photoUrl=sobject.FullPhotoUrl,
            role=sobject.Role,
        )


class ApiResponse:
    def __init__(self, data=None, message="", success=False, status_code=None):
        self.data = data
        self.message = message
        self.success = success
        self.status_code: Optional[int] = 200

    def to_dict(self):
        d = {
            "data": (
                [
                    entry.to_dict() if hasattr(entry, "to_dict") else entry
                    for entry in self.data
                ]
                if self.data
                else []
            ),
            "message": self.message,
            "success": self.success,
            "status_code": self.status_code,
        }
        return d


class CriteriaField(SerializableModel):
    name: str
    type: str
    options: List[dict]


class Account(SerializableModel):
    id: str
    name: Optional[str] = None
    owner_id: Optional[str] = None
    industry: Optional[str] = None
    annual_revenue: Optional[float] = None
    number_of_employees: Optional[int] = None
    created_date: Optional[datetime] = None
    owner: Optional[UserModel] = None


class Contact(SerializableModel):
    id: str
    first_name: str
    last_name: str
    account_id: str
    account: Account
    owner_id: Optional[str] = None


class Task(SerializableModel):
    id: str
    created_date: datetime
    owner_id: str
    who_id: str
    subject: str
    status: str
    contact: Optional[Contact] = None
    account: Optional[Account] = None
    task_subtype: Optional[str] = None


class TaskSObject(SerializableModel):
    Id: str
    CreatedDate: Union[date, str]
    WhoId: str
    Subject: str
    Status: str
    TaskSubtype: Optional[str] = None


class TaskModel(SerializableModel):
    id: str
    createdDate: datetime
    whoId: str
    subject: str
    status: str
    taskSubtype: Optional[str] = None

    @classmethod
    def from_sobject(cls, sobject: TaskSObject):
        return cls(
            id=sobject.Id,
            createdDate=sobject.CreatedDate,
            whoId=sobject.WhoId,
            subject=sobject.Subject,
            status=sobject.Status,
            taskSubtype=sobject.TaskSubtype,
        )


class Event(SerializableModel):
    id: str
    created_date: date
    who_id: str
    subject: str
    start_datetime: datetime
    end_datetime: datetime


class StatusEnum(str, Enum):
    activated = "Activated"
    unresponsive = "Unresponsive"
    engaged = "Engaged"
    meeting_set = "Meeting Set"
    meeting_held = "Meeting Held"
    opportunity_created = "Opportunity Created"


class Opportunity(SerializableModel):
    id: str
    name: str
    amount: float
    close_date: date
    stage: str


class ProspectingMetadata(SerializableModel):
    name: str
    total: int
    first_occurrence: Optional[date] = None
    last_occurrence: Optional[date] = None
    task_ids: List[str] = []  # Change this line


class ProspectingEffort(SerializableModel):
    activation_id: str
    prospecting_metadata: List[ProspectingMetadata]
    status: str
    date_entered: date
    task_ids: Set[str]


class Activation(SerializableModel):
    id: str
    account: Account
    activated_by: UserModel
    active_contact_ids: Set[str]
    active_contacts: List[Contact]
    task_ids: Set[str]
    tasks: List[Dict]  # Add this line
    activated_by_id: Optional[str] = None
    active_contact_count: Optional[int] = None
    activated_date: Optional[date] = None
    first_prospecting_activity: Optional[date] = None
    last_prospecting_activity: Optional[date] = None
    event_ids: Optional[Set[str]] = None
    prospecting_metadata: Optional[List[ProspectingMetadata]] = None
    prospecting_effort: Optional[List[ProspectingEffort]] = None
    days_activated: Optional[int] = None
    days_engaged: Optional[int] = None
    engaged_date: Optional[date] = None
    last_outbound_engagement: Optional[date] = None
    opportunity: Optional[Opportunity] = None
    status: StatusEnum = Field(default=StatusEnum.activated)

    def __init__(self, **data):
        if "activated_by" in data and isinstance(data["activated_by"], UserModel):
            data["activated_by_id"] = data["activated_by"].id
        if "active_contacts" in data:
            data["active_contact_count"] = len(data["active_contacts"])
        super().__init__(**data)


class Filter(SerializableModel):
    field: str
    operator: str
    value: str
    data_type: str
    options: Optional[str] = None

    def matches(self, task: Dict) -> bool:
        task_value = task.get(self.field)
        if task_value is None:
            return False
        if self.data_type == "string":
            return self._match_string(str(task_value))
        elif self.data_type == "number":
            return self._match_number(float(task_value))
        elif self.data_type == "date":
            return self._match_date(task_value)
        return False

    def _match_string(self, task_value: str) -> bool:
        task_value = task_value.lower()
        value = self.value.lower()
        if self.operator == "equals":
            return task_value == value
        elif self.operator == "not_equal":
            return task_value != value
        elif self.operator == "contains":
            return value in task_value
        elif self.operator == "does_not_contain":
            return value not in task_value
        return False

    def _match_number(self, task_value: float) -> bool:
        value = float(self.value)
        if self.operator == "equals":
            return task_value == value
        elif self.operator == "not_equal":
            return task_value != value
        elif self.operator == "greater_than":
            return task_value > value
        elif self.operator == "less_than":
            return task_value < value
        elif self.operator == "greater_or_equal":
            return task_value >= value
        elif self.operator == "less_or_equal":
            return task_value <= value
        return False

    def _match_date(self, task_value: str) -> bool:
        # Parse the task_value, which is in the format 'YYYY-MM-DD'
        task_date = datetime.strptime(task_value, "%Y-%m-%d").date()

        if self.operator == "equals":
            return task_date == datetime.strptime(self.value, "%Y-%m-%d").date()
        elif self.operator == "not_equal":
            return task_date != datetime.strptime(self.value, "%Y-%m-%d").date()
        elif self.operator == "greater_than":
            return task_date > datetime.strptime(self.value, "%Y-%m-%d").date()
        elif self.operator == "less_than":
            return task_date < datetime.strptime(self.value, "%Y-%m-%d").date()
        return False


class FilterContainer(SerializableModel):
    name: str
    filters: List[Filter]
    filter_logic: str
    direction: Optional[str] = None

    def matches(self, task: Dict) -> bool:
        conditions = [f.matches(task) for f in self.filters]
        condition_map = {str(i + 1): c for i, c in enumerate(conditions)}

        # Replace logical operators
        logic = self.filter_logic.replace(" AND ", " and ").replace(" OR ", " or ")

        # Evaluate the logical expression
        try:
            # Replace condition numbers with their boolean values
            for i, condition in condition_map.items():
                replace_condition_number = f"_{i}_"
                logic = re.sub(
                    r"\b" + replace_condition_number + r"\b", str(condition), logic
                )
            return eval(logic, {"__builtins__": {}}, condition_map)
        except Exception as e:
            print(f"Error evaluating logic: {e}")
            return False


class Settings(SerializableModel):
    inactivity_threshold: int
    meeting_object: str
    activities_per_contact: int
    contacts_per_account: int
    tracking_period: int
    activate_by_meeting: bool
    activate_by_opportunity: bool
    criteria: Optional[List[FilterContainer]] = None
    meetings_criteria: Optional[FilterContainer] = None
    salesforce_user_id: Optional[str]
    team_member_ids: Optional[List[str]] = None
    latest_date_queried: Optional[datetime] = None
    skip_account_criteria: Optional[FilterContainer] = None
    skip_opportunity_criteria: Optional[FilterContainer] = None


class FilterModel(SerializableModel):
    field: Optional[str] = None
    dataType: Optional[str] = None
    operator: Optional[str] = None
    value: Optional[str] = None
    options: Optional[List[dict]] = None


class FilterContainerModel(SerializableModel):
    name: str
    filters: List[FilterModel]
    filterLogic: str
    direction: Optional[str] = None


class SettingsModel(SerializableModel):
    activateByMeeting: bool
    activateByOpportunity: bool
    activitiesPerContact: int
    contactsPerAccount: int
    inactivityThreshold: int
    meetingObject: str
    trackingPeriod: int
    latestDateQueried: Optional[datetime] = None
    meetingsCriteria: Optional[FilterContainerModel] = None
    criteria: Optional[List[FilterContainerModel]] = None
    teamMemberIds: Optional[List[str]] = None
    salesforceUserId: Optional[str] = None
    skipAccountCriteria: Optional[FilterContainerModel] = None
    skipOpportunityCriteria: Optional[FilterContainerModel] = None


class DataType(str, Enum):
    STRING = "string"
    NUMBER = "number"
    DATE = "date"
    DATETIME = "datetime"
    SELECT = "select"
    IMAGE = "image"

class SObjectFieldModel(SerializableModel):
    type: str
    name: str
    label: str


class TableColumn(SerializableModel):
    id: str
    dataType: DataType
    label: str


class TokenData(SerializableModel):
    access_token: str
    refresh_token: str
    instance_url: str
    id: str
    token_type: str
    issued_at: str
    
class SessionState(SerializableModel):
    salesforce_id: str
    access_token: str
    refresh_token: str
    instance_url: str
    org_id: str
    is_sandbox: bool
    username: Optional[str] = None


class AuthenticationError(Exception):
    def __init__(self, message="Authentication failed"):
        self.message = message
        super().__init__(self.message)
