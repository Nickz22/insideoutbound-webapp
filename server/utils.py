import uuid, traceback
from dataclasses import is_dataclass
from typing import Any, Set
from datetime import timedelta, datetime, date, timezone
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


# setting utils
def get_team_member_salesforce_ids(settings):
    salesforce_user_ids = [settings.salesforce_user_id] + (
        [id for id in settings.team_member_ids]
        if settings.team_member_ids is not None and len(settings.team_member_ids) > 0
        else []
    )
    return salesforce_user_ids


# id utils
def generate_unique_id():
    return str(uuid.uuid4())


# date utils
def add_days(date, days):
    return date + timedelta(days=days)


def is_model_date_field_within_window(
    sobject_model, start_date, period_days, date_field="CreatedDate"
):
    """
    Check if the date field of a model is within a window of days from a start date.

    :param sobject_model: The model to check
    :param start_date: The start date of the window
    :param period_days: The number of days in the window
    :param date_field: The date field to check
    """
    ## offset-naive start time
    start_time = (
        datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%S.%f%z")
        .astimezone(timezone.utc)
        .replace(tzinfo=None)
    )
    end_date = start_time + timedelta(days=period_days)
    if isinstance(sobject_model, dict):
        model_date_value = datetime.strptime(
            sobject_model[date_field], "%Y-%m-%dT%H:%M:%S.%f%z"
        ).replace(tzinfo=None)
    else:
        model_date_value = getattr(sobject_model, date_field)
    return start_time <= model_date_value <= end_date


def convert_datetime_to_utc_z_format(datetime_str: str) -> str:
    # Parse the input string to a datetime object, including milliseconds and timezone
    dt = datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M:%S.%f%z")
    # Convert to UTC and remove timezone information
    dt_utc = dt.astimezone(tz=timezone.utc).replace(tzinfo=None)
    # Format the datetime object to the desired string format
    return dt_utc.strftime("%Y-%m-%dT%H:%M:%S") + "Z"

def datetime_to_iso_string_z(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

def parse_date_from_string(salesforce_datetime_str: str) -> date:
    """
    Takes a date string formatted as 'YYYY-MM-DDTHH:MM:SS' and returns a date object.
    """
    return datetime.strptime(salesforce_datetime_str, "%Y-%m-%dT%H:%M:%S").date()


def parse_date_with_timezone(date_str) -> datetime:
    """
    Takes a datetime string formatted as 'YYYY-MM-DDTHH:MM:SS.mmm+ZZZZ' and converts it to a timezone-naive datetime object.
    """
    try:
        # Split the datetime string by the last '+' or '-' to separate the datetime and timezone parts
        if "+" in date_str:
            base_time, tz_info = date_str.rsplit("+", 1)
            tz_sign = 1
        else:
            base_time, tz_info = date_str.rsplit("-", 1)
            tz_sign = -1

        # Convert timezone info from 'HHMM' to a timedelta object assuming 'HHMM' format
        tz_hours = int(tz_info[:2])
        tz_minutes = int(tz_info[2:4])
        timezone_delta = timedelta(hours=tz_hours, minutes=tz_minutes) * tz_sign

        # Parse the base datetime part
        dt = datetime.strptime(base_time, "%Y-%m-%dT%H:%M:%S.%f")

        # Apply the timezone offset to get the datetime in UTC and remove timezone information
        dt = dt - timezone_delta
        return dt
    except ValueError as e:
        raise ValueError(f"Error parsing date string: {date_str}. Error: {str(e)}")


# error utils
def format_error_message(e):
    tb_str = traceback.format_exc()
    return f"{tb_str} [{str(e)}]"


# string utils
def surround_numbers_with_underscores(text):
    return re.sub(r"(\d+)", r"_\1_", text)


def remove_underscores_from_numbers(text):
    return re.sub(r"_(\d+)_", r"\1", text)
