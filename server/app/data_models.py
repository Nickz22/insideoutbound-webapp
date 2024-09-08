from pydantic import BaseModel, Field
from typing import List, Optional, Set, Any, Dict
from datetime import date, datetime
from enum import Enum


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


class Task(SerializableModel):
    id: str
    created_date: datetime
    owner_id: str
    who_id: str
    subject: str
    status: str
    task_subtype: Optional[str] = None


class TaskSObject(SerializableModel):
    Id: str
    CreatedDate: date
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


class Contact(SerializableModel):
    id: str
    first_name: str
    last_name: str
    account_id: str
    account: Account


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


class ProspectingEffort(SerializableModel):
    activation_id: str
    prospecting_metadata: List[ProspectingMetadata]
    status: str
    date_entered: date
    task_ids: Set[str]

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

class Activation(SerializableModel):
    id: str
    account: Account
    activated_by_id: str
    activated_by: UserModel
    active_contact_ids: Set[str]
    task_ids: Set[str]
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


class Filter(SerializableModel):
    field: str
    operator: str
    value: str
    data_type: str
    options: Optional[str] = None


class FilterContainer(SerializableModel):
    name: str
    filters: List[Filter]
    filter_logic: str
    direction: Optional[str] = None


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
    instance_url: str
    id: str
    token_type: str
    issued_at: str


class AuthenticationError(Exception):
    def __init__(self, message="Authentication failed"):
        self.message = message
        super().__init__(self.message)
