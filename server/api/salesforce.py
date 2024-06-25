import requests, traceback
from models import ApiResponse, Contact, Account, Task, Opportunity, Event
from cache import load_tokens
from constants import SESSION_EXPIRED, FILTER_OPERATOR_MAPPING
from datetime import datetime
from utils import pluck, format_error_message
from typing import List, Dict
from models import CriteriaField, Task


def get_criteria_fields(sobject_type: str) -> List[CriteriaField]:
    """
    Fetches the field describe info from Salesforce for the Task object and creates CriteriaField instances.

    Returns:
    - List[CriteriaField]: A list of CriteriaField instances representing fields of the Task object.
    """
    api_response = ApiResponse(data=[], message="", success=False)
    access_token, instance_url = (
        load_tokens()
    )  # Assume load_tokens gets the necessary authentication tokens

    if not access_token or not instance_url:
        api_response.message = SESSION_EXPIRED
        return api_response

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    fields_endpoint = f"{instance_url}/services/data/v55.0/sobjects/{sobject_type}/describe"  # Replace 'XX' with your actual API version

    try:
        response = requests.get(fields_endpoint, headers=headers)
        if response.status_code == 200:
            fields_data = response.json().get("fields", [])
            criteria_fields = [
                CriteriaField(
                    name=field["name"],
                    type=field["type"] if field["name"] != "Subject" else "string",
                    options=(
                        field["picklistValues"] if field["type"] == "picklist" else []
                    ),
                )
                for field in fields_data
            ]
            api_response.data = criteria_fields
            api_response.success = True
        else:
            api_response.message = f"Failed to fetch criteria fields ({response.status_code}): {get_http_error_message(response)}"
    except Exception as e:
        api_response.message = (
            f"While getting criteria fields {format_error_message(e)}"
        )

    return api_response


def fetch_tasks_by_account_ids_from_date_not_in_ids(
    account_ids, start, criteria, already_counted_task_ids
):
    """
    Fetches tasks from Salesforce based on a list of account IDs, starting from a specific date,
    organized by criteria names for tasks related to contacts belonging to the specified accounts.

    Parameters:
    - account_ids (list[str]): A list of account IDs to fetch tasks for.
    - start (datetime): The start date to fetch tasks from.
    - criteria (list[FilterContainer]): A list of FilterContainer objects.
    - already_counted_task_ids (list[str]): A list of task IDs that have already been counted.

    Returns:
    - ApiResponse: Response whose `data` is a dictionary where each key is an account ID and each value is another dictionary with
            keys as criteria names and values as lists of tasks fetched from Salesforce.

    Throws:
    - Exception: Raises an exception with a formatted error message if any error occurs during the fetch operation.
    """
    api_response = ApiResponse(data=[], message="", success=False)

    try:
        access_token, instance_url = load_tokens()  # Load tokens from file

        if not instance_url or not access_token:
            raise Exception(SESSION_EXPIRED)

        contacts = fetch_contacts_by_account_ids(account_ids)
        contact_by_id = {contact.id: contact for contact in contacts.data}
        contact_ids = pluck(contacts.data, "id")

        criteria_group_tasks_by_account_id = {}
        additional_filter = ""
        if len(contact_ids) > 0:
            additional_filter = f"WhoId IN ('{','.join(contact_ids)}')"

        # Fetch tasks by criteria
        tasks_by_criteria_name = fetch_contact_tasks_by_criteria_from_date(
            criteria, start, additional_filter
        )

        # Organizing tasks_by_criteria_name by account and criteria
        criteria_group_tasks_by_account_id = {
            account_id: {} for account_id in account_ids
        }

        for criteria_name, tasks in tasks_by_criteria_name.data.items():
            # remove tasks_by_criteria_name that have already been counted
            ## we can't filter the query because the query string has max 4k length
            for task in tasks:
                if task.id in already_counted_task_ids:
                    continue
                contact = contact_by_id.get(task.who_id)
                if contact:
                    account_id = contact.account_id
                    if (
                        criteria_name
                        not in criteria_group_tasks_by_account_id[account_id]
                    ):
                        criteria_group_tasks_by_account_id[account_id][
                            criteria_name
                        ] = []
                    criteria_group_tasks_by_account_id[account_id][
                        criteria_name
                    ].append(task)

        api_response.data = criteria_group_tasks_by_account_id
        api_response.success = True
    except Exception as e:
        raise Exception(format_error_message(e))

    return api_response


def fetch_contact_tasks_by_criteria_from_date(
    criteria, from_datetime, additional_filter=None
) -> Dict[str, List[Task]]:
    """
    Fetches tasks from Salesforce based on a list of filtering criteria.

    Parameters:
    - criteria (list[FilterContainer]): A list of FilterContainer objects. Each FilterContainer object contains
      a list of filters and a filter_logic string. The filters are used to construct the WHERE clause of the SOQL query,
      and the filter_logic string specifies how these filters should be combined.
    - from_datetime (string): An ISO string representing the createddate of the last task fetched. Crucial to minimizing the size of query results.
    - additional_filter (string): An optional additional filter to apply to the SOQL query.

    Returns:
    - dict: A dictionary where each key is the name of a filter container and each value is a list of Task objects fetched from Salesforce.

    Throws:
    - Exception: Raises an exception with a formatted error message if any error occurs during the fetch operation.
    """
    api_response = ApiResponse(data=[], message="", success=False)
    access_token, instance_url = load_tokens()  # Load tokens from file

    if not instance_url or not access_token:
        raise Exception(SESSION_EXPIRED)

    soql_query = f"SELECT Id, WhoId, WhatId, Subject, Status, CreatedDate FROM Task WHERE CreatedDate >= {from_datetime} AND "
    if additional_filter:
        soql_query += f"{additional_filter} AND "
    tasks_by_filter_name = {}

    try:
        for filter_container in criteria:
            combined_conditions = _construct_where_clause_from_filter(filter_container)

            fetch_response = _fetch_sobjects(
                f"{soql_query} {combined_conditions} ORDER BY CreatedDate ASC",
                instance_url,
                access_token,
            )

            contact_task_models = []
            for task in fetch_response.data:
                if not (
                    task.get("WhoId", "") and task.get("WhoId", "").startswith("003")
                ):
                    continue
                contact_task_models.append(
                    Task(
                        id=task.get("Id"),
                        who_id=task.get("WhoId"),
                        subject=task.get("Subject"),
                        status=task.get("Status"),
                        created_date=_parse_date_with_timezone(
                            task["CreatedDate"].replace("Z", "+00:00")
                        ),
                    )
                )

            tasks_by_filter_name[filter_container.name] = contact_task_models

        api_response.data = tasks_by_filter_name
        api_response.success = True
    except Exception as e:
        raise Exception(format_error_message(e))

    return api_response


def fetch_events_by_account_ids_from_date(account_ids, start):
    """
    Fetches events from Salesforce based on a list of account IDs.

    Parameters:
    - account_ids (list[str]): A list of account IDs to fetch events for.

    Returns:
    - dict: A dictionary where each key is an account ID and each value is the list of events fetched from Salesforce
      for that account. The events are represented as dictionaries with keys corresponding to the fields selected in the SOQL query.

    Throws:
    - Exception: Raises an exception with a formatted error message if any error occurs during the fetch
    """
    api_response = ApiResponse(data={}, message="", success=False)
    access_token, instance_url = load_tokens()  # Load tokens from file

    if not instance_url or not access_token:
        raise Exception(SESSION_EXPIRED)

    contacts = fetch_contacts_by_account_ids(account_ids)
    contact_by_id = {contact.id: contact for contact in contacts.data}
    contact_ids = pluck(contacts.data, "id")

    soql_query = f"SELECT Id, WhoId, WhatId, Subject, StartDateTime, EndDateTime FROM Event WHERE WhoId IN ('{','.join(contact_ids)}') AND CreatedDate >= {start} ORDER BY StartDateTime ASC"
    events_by_account_id = {}

    try:
        fetch_response = _fetch_sobjects(soql_query, instance_url, access_token)

        for event in fetch_response.data:
            account_id = contact_by_id.get(event.get("WhoId")).account_id
            if account_id not in events_by_account_id:
                events_by_account_id[account_id] = []
            events_by_account_id[account_id].append(
                Event(
                    id=event.get("Id"),
                    who_id=event.get("WhoId"),
                    what_id=event.get("WhatId"),
                    subject=event.get("Subject"),
                    start_date_time=_parse_date_with_timezone(
                        event["StartDateTime"].replace("Z", "+00:00")
                    ),
                    end_date_time=_parse_date_with_timezone(
                        event["EndDateTime"].replace("Z", "+00:00")
                    ),
                )
            )

        api_response.data = events_by_account_id
        api_response.success = True
    except Exception as e:
        raise Exception(format_error_message(e))

    return api_response


def fetch_opportunities_by_account_ids_from_date(account_ids, start):
    """
    Fetches opportunities from Salesforce based on a list of account IDs.

    Parameters:
    - account_ids (list[str]): A list of account IDs to fetch opportunities for.

    Returns:
    - dict: A dictionary where each key is an account ID and each value is the list of opportunities fetched from Salesforce
      for that account. The opportunities are represented as dictionaries with keys corresponding to the fields selected in the SOQL query.
    """
    api_response = ApiResponse(data={}, message="", success=False)
    access_token, instance_url = load_tokens()  # Load tokens from file

    if not instance_url or not access_token:
        raise Exception(SESSION_EXPIRED)

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    try:
        joined_ids = ",".join([f"'{id}'" for id in account_ids])
        soql_query = f"SELECT Id, AccountId, Amount, CreatedDate, StageName FROM Opportunity WHERE CreatedDate >= {start} AND AccountId IN ({joined_ids})"
        request_url = f"{instance_url}/services/data/v55.0/query?q={soql_query}"
        opportunity_models = []

        response = requests.get(request_url, headers=headers)
        if response.status_code == 200:
            opportunities = response.json().get("records", [])
            for opportunity in opportunities:
                opportunity_models.append(
                    Opportunity(
                        id=opportunity.get("Id"),
                        account_id=opportunity.get("AccountId"),
                        amount=opportunity.get("Amount"),
                        created_date=_parse_date_with_timezone(
                            opportunity["CreatedDate"].replace("Z", "+00:00")
                        ),
                        status=opportunity.get("Status"),
                    )
                )
            api_response.data = opportunity_models
            api_response.success = True
            api_response.message = "Opportunities fetched successfully."
        else:
            raise Exception(
                f"Failed to fetch opportunities ({response.status_code}): {get_http_error_message(response)}"
            )
    except Exception as e:
        raise Exception(format_error_message(e))

    return api_response


def fetch_contacts_by_account_ids(account_ids):
    """
    Fetches contacts from Salesforce based on a list of account IDs.

    Parameters:
    - account_ids (list[str]): A list of account IDs to fetch contacts for.

    Returns:
    - ApiResponse: An ApiResponse object containing the fetched contacts as a list of Contact objects.

    Throws:
    - Exception: Raises an exception with a formatted error message if any error occurs during the fetch operation.
    """
    api_response = ApiResponse(data=[], message="", success=False)
    access_token, instance_url = load_tokens()  # Load tokens from file

    if not instance_url or not access_token:
        raise Exception(SESSION_EXPIRED)

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    try:
        joined_ids = ",".join([f"'{id}'" for id in account_ids])
        soql_query = (
            f"SELECT Id, AccountId FROM Contact WHERE AccountId IN ({joined_ids})"
        )
        request_url = f"{instance_url}/services/data/v55.0/query?q={soql_query}"
        contact_models = []

        response = requests.get(request_url, headers=headers)
        if response.status_code == 200:
            contacts = response.json().get("records", [])
            for contact in contacts:
                contact_models.append(
                    Contact(
                        id=contact.get("Id"),
                        first_name=contact.get("FirstName"),
                        last_name=contact.get("LastName"),
                        account_id=contact.get("AccountId"),
                        account=Account(
                            id=contact.get("AccountId"),
                            name=contact.get("Account").get("Name"),
                        ),
                    )
                )
            api_response.data = contact_models
            api_response.success = True
        else:
            raise Exception(
                f"Failed to fetch contacts ({response.status_code}): {get_http_error_message(response)}"
            )
    except Exception as e:
        api_response.message = format_error_message(e)

    return api_response


def fetch_contacts_by_ids(contact_ids):

    api_response = ApiResponse(data=[], message="", success=False)

    access_token, instance_url = load_tokens()  # Load tokens from file
    if not instance_url or not access_token:
        raise Exception(SESSION_EXPIRED)

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    try:

        joined_ids = ",".join([f"'{id}'" for id in contact_ids])
        soql_query = f"SELECT Id, FirstName, LastName, AccountId, Account.Name FROM Contact WHERE Id IN ({joined_ids}) AND AccountId != null"
        request_url = f"{instance_url}/services/data/v55.0/query?q={soql_query}"
        contact_models = []

        response = requests.get(request_url, headers=headers)
        if response.status_code == 200:
            contacts = response.json().get("records", [])
            for contact in contacts:
                contact_models.append(
                    Contact(
                        id=contact.get("Id"),
                        first_name=contact.get("FirstName"),
                        last_name=contact.get("LastName"),
                        account_id=contact.get("AccountId"),
                        account=Account(
                            id=contact.get("AccountId"),
                            name=contact.get("Account").get("Name"),
                        ),
                    )
                )
            api_response.data = contact_models
            api_response.success = True
            api_response.message = "Contacts fetched successfully."
        else:
            raise Exception(
                f"Failed to fetch contacts from Salesforce ({response.status_code}): {get_http_error_message(response)}"
            )
    except Exception as e:
        raise Exception(format_error_message(e))

    return api_response


# helpers
def _construct_where_clause_from_filter(filter_container):
    """
    Construct and apply filter logic for a given filter container.

    Parameters:
        filter_container: The filter container object with filters and filter_logic.

    Returns:
        A string representing the SOQL condition part.
    """
    # Construct conditions
    conditions = [_construct_condition(f) for f in filter_container.filters]
    condition_by_index = {
        str(index + 1): condition for index, condition in enumerate(conditions)
    }

    # Apply filter logic by replacing placeholders with actual conditions
    combined_conditions = filter_container.filter_logic
    for index, condition in condition_by_index.items():
        combined_conditions = combined_conditions.replace(f"_{index}_", condition)

    return combined_conditions


def _fetch_sobjects(soql_query, instance_url, access_token):
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
            raise Exception(
                f"Failed to fetch sobjects ({response.status_code}): {get_http_error_message(response)}"
            )
    except Exception as e:
        raise Exception(format_error_message(e))


def _map_operator(operator, data_type):
    return FILTER_OPERATOR_MAPPING[data_type].get(operator, operator)


def _construct_condition(filter_obj):
    field = filter_obj.field
    value = filter_obj.value

    operator = _map_operator(filter_obj.operator, filter_obj.data_type)

    if filter_obj.data_type == "string" and operator == "LIKE":
        value = f" '%{value}%'"
    elif filter_obj.data_type == "string":
        value = f"'{value}'"
    elif filter_obj.data_type == "date" or filter_obj.data_type == "number":
        value = f"{value}"

    return f"{field} {operator}{value}"


def _parse_date_with_timezone(date_str):
    base_time = date_str[:-9]
    timezone = date_str[-5:]
    fixed_timezone = timezone[:3] + ":" + timezone[3:]

    iso_formatted_str = base_time + fixed_timezone

    return datetime.fromisoformat(iso_formatted_str)


def get_http_error_message(response):
    if response.status_code == 401:
        return f"{SESSION_EXPIRED}"
    else:
        return response.json()[0].get("message", "An error occurred")
