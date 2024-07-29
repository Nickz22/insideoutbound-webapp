from pydantic import BaseModel
from typing import List, Optional, Dict, Set, Any
from datetime import date, datetime
from uuid import UUID
from enum import Enum


def serialize_complex_types(obj: Any) -> Any:
    if isinstance(obj, (set, frozenset)):
        return list(obj)
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, BaseModel):
        return obj.model_dump()
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
        return {
            "data": (
                [
                    entry.to_dict() if hasattr(entry, "to_dict") else entry
                    for entry in self.data
                ]
                if self.data
                else None
            ),
            "message": self.message,
            "success": self.success,
            "status_code": self.status_code,
        }


class CriteriaField(SerializableModel):
    name: str
    type: str
    options: List[dict]


class ProspectingMetadata(SerializableModel):
    name: str
    first_occurrence: date
    last_occurrence: date
    total: int


class Account(SerializableModel):
    id: str
    name: Optional[str] = None
    owner_id: Optional[str] = None


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


class Activation(SerializableModel):
    id: str
    account: Account
    activated_by_id: str
    active_contact_ids: Set[str]
    task_ids: Set[str]
    activated_date: Optional[date] = None
    first_prospecting_activity: Optional[datetime] = None
    last_prospecting_activity: Optional[datetime] = None
    event_ids: Optional[Set[str]] = None
    prospecting_metadata: Optional[List[ProspectingMetadata]] = None
    days_activated: Optional[int] = None
    days_engaged: Optional[int] = None
    engaged_date: Optional[date] = None
    last_outbound_engagement: Optional[datetime] = None
    opportunity: Optional[Dict] = None
    status: str = "Activated"


class ProspectingEffort(SerializableModel):
    id: str
    activation_id: str
    prospecting_metadata: List[ProspectingMetadata]
    status: str
    date_entered: date
    tasks: List[Task]


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


class Settings(SerializableModel):
    inactivity_threshold: int
    criteria: List[FilterContainer]
    meetings_criteria: FilterContainer
    meeting_object: str
    activities_per_contact: int
    contacts_per_account: int
    tracking_period: int
    activate_by_meeting: bool
    activate_by_opportunity: bool
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


class SettingsModel(SerializableModel):
    activateByMeeting: bool
    activateByOpportunity: bool
    activitiesPerContact: int
    contactsPerAccount: int
    criteria: List[FilterContainerModel]
    inactivityThreshold: int
    meetingObject: str
    meetingsCriteria: FilterContainerModel
    trackingPeriod: int
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


class UserSObject(SerializableModel):
    Id: str
    Email: str
    Username: str
    LastName: str
    FullPhotoUrl: str
    FirstName: Optional[str] = None
    Role: Optional[str] = None


class UserModel(SerializableModel):
    id: str
    email: str
    username: str
    lastName: str
    photoUrl: str
    firstName: Optional[str] = None
    role: Optional[str] = None

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


class AuthenticationError(Exception):
    def __init__(self, message="Authentication failed"):
        self.message = message
        super().__init__(self.message)