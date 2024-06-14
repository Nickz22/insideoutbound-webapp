from dataclasses import dataclass
from typing import List

@dataclass
class Filter:
    field: str
    operator: str
    value: str
    data_type: str

@dataclass
class FilterContainer:
    filters: List[Filter]
    filterLogic: str
