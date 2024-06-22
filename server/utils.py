import uuid
from dataclasses import is_dataclass
from typing import Any, Set
from datetime import timedelta
from functools import reduce
import re

# filter utils
def add_underscores_to_numbers(expression):
    transformed_expression = re.sub(r'\b(\d+)\b', r'_\1_', expression)
    return transformed_expression

# list utils
def get_nested_value(item, path):
    """Helper function to safely get a nested value from a dict or dataclass based on a dot-separated path."""
    keys = path.split(".")

    def get_value(current_item, key):
        # If the current part is a dictionary, use get
        if isinstance(current_item, dict):
            return current_item.get(key)
        # If it's a dataclass or an object, use getattr
        elif is_dataclass(current_item) or hasattr(current_item, key):
            return getattr(current_item, key, None)
        return None

    return reduce(get_value, keys, item)


def pluck(arr: list, param: str) -> Set[Any]:
    plucked = set()
    for item in arr:
        value = get_nested_value(item, param)
        if value is not None:  # Optionally skip None values
            plucked.add(value)
    return plucked


def group_by(arr: list, param: str) -> dict:
    grouped = {}
    for item in arr:
        key = get_nested_value(item, param)
        if key is not None:  # Optionally skip None values
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(item)
    return grouped


# id utils
def generate_unique_id():
    return str(uuid.uuid4())


# date utils
def add_days(date, days):
    return date + timedelta(days=days)


def is_model_created_within_period(sobject_model, start_date, period_days):
    end_date = start_date + timedelta(days=period_days)
    return start_date <= sobject_model.created_date <= end_date
