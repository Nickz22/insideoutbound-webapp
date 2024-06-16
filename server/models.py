from dataclasses import dataclass
from typing import List
from datetime import date
from typing import List, Optional


@dataclass
class ProcessResponse:
    data: List[dict]
    message: str
    success: bool
    metadata: Optional[dict] = None


@dataclass
class ApiResponse:
    data: List[dict]
    message: str
    success: bool


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
    filterLogic: str


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

@dataclass
class Event:
    id: str
    created_date: date
    who_id: str
    subject: str
    status: str

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
    prospecting_metadata: Optional[List[ProspectingMetadata]] = None
    days_activated: Optional[int] = None
    days_engaged: Optional[int] = None
    engaged_date: Optional[date] = None
    last_outbound_engagement: Optional[date] = Nones
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
