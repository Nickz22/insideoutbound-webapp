from dataclasses import dataclass
from typing import List
from datetime import date, datetime
from typing import List, Optional, Any

from server.utils import remove_underscores_from_numbers


@dataclass
class ApiResponse:
    data: Any
    message: str
    success: bool


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
    name: str


@dataclass
class Opportunity:
    id: str
    name: str
    amount: int
    created_date: date
    status: str


@dataclass
class Task:
    id: str
    created_date: date
    who_id: str
    subject: str
    status: str
    task_subtype: Optional[str] = None


@dataclass
class TaskModel:
    id: str
    createdDate: date
    whoId: str
    subject: str
    status: str
    taskSubtype: Optional[str] = None


@dataclass
class Event:
    id: str
    created_date: date
    who_id: str
    subject: str


@dataclass
class Contact:
    id: str
    first_name: str
    last_name: str
    account_id: str
    account: Account


@dataclass
class Activation:
    id: str
    account: Account
    activated_date: date
    active_contact_ids: set[str]
    first_prospecting_activity: date
    last_prospecting_activity: date
    task_ids: set[str]
    event_ids: Optional[set[str]] = None
    prospecting_metadata: Optional[List[ProspectingMetadata]] = None
    days_activated: Optional[int] = None
    days_engaged: Optional[int] = None
    engaged_date: Optional[date] = None
    last_outbound_engagement: Optional[date] = None
    opportunity: Optional[Opportunity] = None
    status: Optional[str] = "Activated"


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
    latest_date_queried: Optional[datetime] = None
    skip_account_criteria: Optional[FilterContainer] = None
    skip_opportunity_criteria: Optional[FilterContainer] = None


class FilterModel:
    def __init__(
        self, field=None, dataType=None, operator=None, value=None, filter_=None
    ):
        if filter_ is not None:
            # Initialize from Filter object
            self.field = filter_.field
            self.dataType = filter_.data_type
            self.operator = filter_.operator
            self.value = filter_.value
        else:
            # Initialize from individual attributes
            self.field = field
            self.dataType = dataType
            self.operator = operator
            self.value = value

    def to_dict(self):
        return {
            "field": self.field,
            "dataType": self.dataType,
            "operator": self.operator,
            "value": self.value,
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
            self.trackingPeriod = trackingPeriod
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
            "trackingPeriod": self.trackingPeriod,
            "skipAccountCriteria": (
                self.skipAccountCriteria.to_dict() if self.skipAccountCriteria else None
            ),
            "skipOpportunityCriteria": (
                self.skipOpportunityCriteria.to_dict()
                if self.skipOpportunityCriteria
                else None
            ),
        }
