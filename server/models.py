import re
from dataclasses import dataclass, asdict, field
from typing import List, Literal
from datetime import date, datetime
from typing import List, Optional, Any, Dict, Set
from server.utils import remove_underscores_from_numbers, parse_date_from_string


@dataclass
class ApiResponse:
    data: Any
    message: str
    success: bool
    status_code: Optional[int] = 200

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


@dataclass
class CriteriaField:
    name: str
    type: str
    options: List[str]


@dataclass
class ProspectingMetadata:
    name: str
    first_occurrence: date
    last_occurrence: date
    total: int


@dataclass
class Account:
    id: str
    name: Optional[str] = None


@dataclass
class Task:
    id: str
    created_date: datetime
    owner_id: str
    who_id: str
    subject: str
    status: str
    task_subtype: Optional[str] = None


@dataclass
class TaskSObject:
    Id: str
    CreatedDate: date
    WhoId: str
    Subject: str
    Status: str
    TaskSubtype: Optional[str] = None

    def to_dict(self):
        return {
            "Id": self.Id,
            "CreatedDate": self.CreatedDate,
            "WhoId": self.WhoId,
            "Subject": self.Subject,
            "Status": self.Status,
            "TaskSubtype": self.TaskSubtype,
        }


@dataclass
class TaskModel:
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


@dataclass
class Event:
    id: str
    created_date: date
    who_id: str
    subject: str
    start_datetime: datetime
    end_datetime: datetime

    def to_dict(self):
        return convert_to_dict(asdict(self))


@dataclass
class Contact:
    id: str
    first_name: str
    last_name: str
    account_id: str
    account: Account


from dataclasses import dataclass, field, asdict
from typing import Set, Optional, List, Dict
from datetime import date


@dataclass
class Activation:
    id: str
    account: Account
    activated_by_id: str
    active_contact_ids: Set[str]
    task_ids: Set[str]
    activated_date: Optional[date] = None
    first_prospecting_activity: Optional[date] = None
    last_prospecting_activity: Optional[date] = None
    event_ids: Optional[Set[str]] = None
    prospecting_metadata: Optional[List["ProspectingMetadata"]] = None
    days_activated: Optional[int] = None
    days_engaged: Optional[int] = None
    engaged_date: Optional[date] = None
    last_outbound_engagement: Optional[date] = None
    opportunity: Optional[Dict] = None
    status: str = "Activated"

    def __post_init__(self):
        self.activated_date = self._parse_date(self.activated_date)
        self.first_prospecting_activity = self._parse_date(
            self.first_prospecting_activity
        )
        self.last_prospecting_activity = self._parse_date(
            self.last_prospecting_activity
        )
        self.engaged_date = self._parse_date(self.engaged_date)
        self.last_outbound_engagement = self._parse_date(self.last_outbound_engagement)

    @staticmethod
    def _parse_date(value):
        if isinstance(value, str):
            return parse_date_from_string(value)
        elif isinstance(value, date):
            return value
        else:
            return None

    def to_dict(self):
        return convert_to_dict(asdict(self))


@dataclass
class ProspectingEffort:
    id: str
    activation_id: str
    prospecting_metadata: List[ProspectingMetadata]
    status: str
    date_entered: date
    tasks: List[Task]


@dataclass
class Filter:
    field: str
    operator: str
    value: str
    data_type: str
    options: Optional[str] = None


@dataclass
class FilterContainer:
    name: str
    filters: List[Filter]
    filter_logic: str


@dataclass
class Settings:
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


class FilterModel:
    def __init__(
        self,
        field=None,
        dataType=None,
        operator=None,
        value=None,
        filter_=None,
        options: Optional[List[str]] = None,
    ):
        if filter_ is not None:
            # Initialize from Filter object
            self.field = filter_.field
            self.dataType = filter_.data_type
            self.operator = filter_.operator
            self.value = filter_.value
            self.options = filter_.options
        else:
            # Initialize from individual attributes
            self.field = field
            self.dataType = dataType
            self.operator = operator
            self.value = value
            self.options = options

    def to_dict(self):
        return {
            "field": self.field,
            "dataType": self.dataType,
            "operator": self.operator,
            "value": self.value,
            "options": self.options,
        }


class FilterContainerModel:
    def __init__(
        self, name=None, filters=None, filterLogic=None, filter_container=None
    ):
        if filter_container is not None:
            self.name = filter_container.name
            self.filters = [
                FilterModel(filter_=filter_) for filter_ in filter_container.filters
            ]
            self.filterLogic = remove_underscores_from_numbers(
                filter_container.filter_logic
            )
        else:
            self.name = name
            self.filters = filters
            self.filterLogic = remove_underscores_from_numbers(filterLogic)

    def to_dict(self):
        return {
            "name": self.name,
            "filters": [filter_.to_dict() for filter_ in self.filters],
            "filterLogic": self.filterLogic,
        }


class SettingsModel:
    def __init__(
        self,
        activateByMeeting=None,
        activateByOpportunity=None,
        activitiesPerContact=None,
        contactsPerAccount=None,
        criteria=None,
        inactivityThreshold=None,
        meetingObject=None,
        meetingsCriteria=None,
        trackingPeriod=None,
        teamMemberIds=None,
        salesforceUserId=None,
        skipAccountCriteria=None,
        skipOpportunityCriteria=None,
        settings=None,
    ):
        if settings:
            self.activateByMeeting = settings.activate_by_meeting
            self.activateByOpportunity = settings.activate_by_opportunity
            self.activitiesPerContact = settings.activities_per_contact
            self.contactsPerAccount = settings.contacts_per_account
            self.criteria = [
                FilterContainerModel(filter_container=fc) for fc in settings.criteria
            ]
            self.inactivityThreshold = settings.inactivity_threshold
            self.meetingObject = settings.meeting_object
            self.meetingsCriteria = FilterContainerModel(
                filter_container=settings.meetings_criteria
            )
            self.trackingPeriod = settings.tracking_period
            self.teamMemberIds = settings.team_member_ids
            self.salesforceUserId = settings.salesforce_user_id
            self.skipAccountCriteria = (
                FilterContainerModel(filter_container=settings.skip_account_criteria)
                if settings.skip_account_criteria
                else None
            )
            self.skipOpportunityCriteria = (
                FilterContainerModel(
                    filter_container=settings.skip_opportunity_criteria
                )
                if settings.skip_opportunity_criteria
                else None
            )
        else:
            self.activateByMeeting = activateByMeeting
            self.activateByOpportunity = activateByOpportunity
            self.activitiesPerContact = activitiesPerContact
            self.contactsPerAccount = contactsPerAccount
            self.criteria = criteria
            self.inactivityThreshold = inactivityThreshold
            self.meetingObject = meetingObject
            self.meetingsCriteria = meetingsCriteria
            self.teamMemberIds = teamMemberIds
            self.trackingPeriod = trackingPeriod
            self.salesforceUserId = salesforceUserId
            self.skipAccountCriteria = skipAccountCriteria
            self.skipOpportunityCriteria = skipOpportunityCriteria

    def to_dict(self):
        return {
            "activateByMeeting": self.activateByMeeting,
            "activateByOpportunity": self.activateByOpportunity,
            "activitiesPerContact": self.activitiesPerContact,
            "contactsPerAccount": self.contactsPerAccount,
            "criteria": [criterion.to_dict() for criterion in self.criteria],
            "inactivityThreshold": self.inactivityThreshold,
            "meetingObject": self.meetingObject,
            "meetingsCriteria": self.meetingsCriteria.to_dict(),
            "teamMemberIds": self.teamMemberIds,
            "trackingPeriod": self.trackingPeriod,
            "salesforceUserId": self.salesforceUserId,
            "skipAccountCriteria": (
                self.skipAccountCriteria.to_dict() if self.skipAccountCriteria else None
            ),
            "skipOpportunityCriteria": (
                self.skipOpportunityCriteria.to_dict()
                if self.skipOpportunityCriteria
                else None
            ),
        }


@dataclass
class SObjectFieldModel:
    type: str
    name: str
    label: str

    def to_dict(self):
        return asdict(self)


@dataclass
class TableColumn:
    id: str
    dataType: Literal["string", "number", "date", "datetime", "select", "image"]
    label: str


@dataclass
class UserSObject:
    Id: str
    Email: str
    Username: str
    FirstName: str
    LastName: str
    FullPhotoUrl: str
    Role: str


@dataclass
class UserModel:
    id: str
    email: str
    username: str
    firstName: str
    lastName: str
    photoUrl: str
    role: str

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

    def to_dict(self):
        return convert_to_dict(asdict(self))


def convert_to_dict(obj):
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    elif isinstance(obj, set):
        return list(obj)
    elif isinstance(obj, dict):
        return {k: convert_to_dict(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_dict(v) for v in obj]
    elif hasattr(obj, "to_dict"):
        return obj.to_dict()
    return obj
