import requests, traceback
from models import ApiResponse
from cache import load_tokens
from constants import MISSING_ACCESS_TOKEN, FILTER_OPERATOR_MAPPING


def fetch_contact_tasks_by_criteria(criteria):
    """
    Fetches tasks from Salesforce based on a list of filtering criteria.

    Parameters:
    - criteria (list[FilterContainer]): A list of FilterContainer objects. Each FilterContainer object contains
      a list of filters and a filterLogic string. The filters are used to construct the WHERE clause of the SOQL query,
      and the filterLogic string specifies how these filters should be combined.

    Returns:
    - dict: A dictionary where each key is the name of a filter (as specified in the FilterContainer) and each value
      is the list of tasks fetched from Salesforce that match the filter criteria. The tasks are represented as
      dictionaries with keys corresponding to the fields selected in the SOQL query.
    """
    api_response = ApiResponse(data=[], message="", success=False)
    access_token, instance_url = load_tokens()  # Load tokens from file

    if not instance_url or not access_token:
        api_response.success = False
        api_response.message = MISSING_ACCESS_TOKEN
        return api_response

    soql_query = f"SELECT Id, WhoId, WhatId, Subject, Status FROM Task WHERE"
    tasks_by_filter_name = {}

    try:
        for filter_container in criteria:
            conditions = [construct_condition(f) for f in filter_container.filters]

            condition_by_index = {
                str(index + 1): condition for index, condition in enumerate(conditions)
            }

            combined_conditions = filter_container.filterLogic
            for index, condition in condition_by_index.items():
                combined_conditions = combined_conditions.replace(
                    f"_{index}_", condition
                )

            print(
                f"{filter_container.name} SOQL Query:",
                f"{soql_query} {combined_conditions}",
            )
            fetch_response = _fetch_tasks(
                f"{soql_query} {combined_conditions}", instance_url, access_token
            )
            if not fetch_response.success:
                api_response.success = False
                api_response.message = fetch_response.message
                break

            contact_tasks = [
                task
                for task in fetch_response.data
                if task.get("WhoId", "") and task.get("WhoId", "").startswith("003")
            ]
            tasks_by_filter_name[filter_container.name] = contact_tasks
    except Exception as e:
        api_response.success = False
        api_response.message = f"{traceback.format_exc()} [{str(e)}]"
        return api_response

    api_response.data = tasks_by_filter_name
    api_response.success = True

    return api_response


def fetch_contacts_by_ids(contact_ids):

    api_response = ApiResponse(data=[], message="", success=False)

    access_token, instance_url = load_tokens()  # Load tokens from file
    if not instance_url or not access_token:
        api_response.success = False
        api_response.message = MISSING_ACCESS_TOKEN

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    try:

        joined_ids = ",".join([f"'{id}'" for id in contact_ids])
        soql_query = f"SELECT Id, Name, Email FROM Contact WHERE Id IN ({joined_ids})"
        request_url = f"{instance_url}/services/data/v55.0/query?q={soql_query}"

        response = requests.get(request_url, headers=headers)
        if response.status_code == 200:
            contacts = response.json().get("records", [])
            api_response.data = contacts
            api_response.success = True
            api_response.message = "Contacts fetched successfully."
        else:
            api_response.message = "Failed to fetch contacts from Salesforce."
            api_response.success = False
    except Exception as e:
        api_response.message = str(e)
        api_response.success = False

    return api_response


# helpers
def _fetch_tasks(soql_query, instance_url, access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        response = requests.get(
            f"{instance_url}/services/data/v55.0/query",
            headers=headers,
            params={"q": soql_query},
        )
        if response.status_code == 200:
            return ApiResponse(
                success=True, data=response.json()["records"], message=None
            )
        else:
            return ApiResponse(
                success=False,
                data=None,
                message=f"Error fetching tasks: {response.status_code} {response.text}",
            )
    except Exception as e:
        return ApiResponse(success=False, data=None, message=str(e))


def map_operator(operator, data_type):
    return FILTER_OPERATOR_MAPPING[data_type].get(operator, operator)


def construct_condition(filter_obj):
    field = filter_obj.field
    value = filter_obj.value

    operator = map_operator(filter_obj.operator, filter_obj.data_type)

    if filter_obj.data_type == "string" and operator == "LIKE":
        value = f" '%{value}%'"
    elif filter_obj.data_type == "string":
        value = f"'{value}'"
    elif filter_obj.data_type == "date" or filter_obj.data_type == "number":
        value = f"{value}"

    return f"{field} {operator}{value}"
