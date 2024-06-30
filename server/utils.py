import uuid, traceback
from dataclasses import is_dataclass
from typing import Any, Set
from datetime import timedelta, datetime
from functools import reduce
import re


# filter utils
def add_underscores_to_numbers(expression):
    transformed_expression = re.sub(r"\b(\d+)\b", r"_\1_", expression)
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


def is_model_date_field_within_window(
    sobject_model, start_date, period_days, date_field="created_date"
):
    """
    Check if the date field of a model is within a window of days from a start date.

    :param sobject_model: The model to check
    :param start_date: The start date of the window
    :param period_days: The number of days in the window
    :param date_field: The date field to check
    """
    end_date = start_date + timedelta(days=period_days)
    model_date_value = getattr(sobject_model, date_field)
    return start_date <= model_date_value <= end_date


def dt_to_iso_format(dt: datetime):
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def parse_date_with_timezone(date_str) -> datetime:
    """
    Takes a datetime string from an SObject and converts it to a datetime object with timezone.
    """
    base_time = date_str[:-9]
    timezone = date_str[-5:]
    fixed_timezone = timezone[:3] + ":" + timezone[3:]

    iso_formatted_str = base_time + fixed_timezone

    return datetime.fromisoformat(iso_formatted_str)


# error utils
def format_error_message(e):
    tb_str = traceback.format_exc()
    return f"{tb_str} [{str(e)}]"


# string utils
def surround_numbers_with_underscores(text):
    return re.sub(r"(\d+)", r"_\1_", text)


def remove_underscores_from_numbers(text):
    return re.sub(r"_(\d+)_", r"\1", text)
