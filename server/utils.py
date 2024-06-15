import uuid
from dataclasses import is_dataclass
from typing import Any, Set


def pluck(arr: list, param: str) -> Set[Any]:
    plucked = set()
    for item in arr:
        # Check if item is a dictionary
        if isinstance(item, dict):
            value = item.get(param)
        # Check if item is a dataclass instance
        elif is_dataclass(item):
            value = getattr(item, param, None)
        # Assume item is an object with attributes
        else:
            value = getattr(item, param, None)
        plucked.add(value)
    return plucked


def generate_unique_id():
    return str(uuid.uuid4())
