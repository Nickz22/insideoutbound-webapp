from dataclasses import dataclass
from typing import List
from datetime import date

@dataclass
class ProcessResponse:
    data: List[dict]
    message: str
    success: bool
    metadata: dict
    

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
    close_date: date
    created_date: date
    
@dataclass
class Task: 
    id: str


@dataclass
class Activation:
    id: str
    account: Account
    activated_date: date
    days_activated: int
    days_engaged: int
    engaged_date: date
    last_outbound_engagement: date
    last_prospecting_activity: date
    opportunity: Opportunity
    status: str
    active_contacts: int
    prospecting_metadata: List[ProspectingMetadata]

@dataclass
class ProspectingEffort:
    id: str
    activation_id: str
    prospecting_metadata: List[ProspectingMetadata]
    status: str
    date_entered: date
    tasks: List[Task]