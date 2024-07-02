import random
from server.tests.utils import is_valid_salesforce_query
from unittest.mock import MagicMock
from server.tests.c import (
    mock_tasks_for_criteria_with_contains_content,  # 3
    mock_tasks_for_criteria_with_unique_values_content,  # 3
)
from server.models import TaskSObject, OpportunitySObject
from typing import List, Dict
from datetime import datetime

MOCK_CONTACT_IDS = [f"mock_contact_id{i}" for i in range(10)]
MOCK_ACCOUNT_IDS = [f"mock_account_id{i}" for i in range(1, 6)]

today = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000+0000")

# each test should set this map to mock the appropriate response
sobject_api_mock_response_by_request_key: Dict[str, List[Dict]] = {
    "contains_content_criteria_query": [],
    "unique_values_content_criteria_query": [],
    "fetch_contacts_by_ids_and_non_null_accounts": [],
    "fetch_opportunities_by_account_ids_from_date": [],
    "fetch_events_by_account_ids_from_date": [],
    "fetch_contacts_by_account_ids": [],
    "fetch_accounts_not_in_ids": [],
}


def add_mock_response(request_key, response):
    """
    Sets the mock response for a given request key

    request_key: str
    response: List[Dict[str, Any]] almost always a list of SObjects
    """
    mock_return_values = sobject_api_mock_response_by_request_key[request_key]
    mock_return_values.append(get_mock_http_response_json(response))
    sobject_api_mock_response_by_request_key[request_key] = mock_return_values


def clear_mocks():
    """
    Dynamically clears all the mock responses by setting each value to None
    """
    global sobject_api_mock_response_by_request_key
    for key in sobject_api_mock_response_by_request_key.keys():
        sobject_api_mock_response_by_request_key[key] = []


def response_based_on_query(url, **kwargs):
    """
    Mocks the response of a GET request to Salesforce's SObject API
    """
    print(f"URL: {url}")
    print(f"Parameters: {kwargs}")
    try:
        query_param = kwargs.get("params", {}).get("q", "")
        is_valid_query = is_valid_salesforce_query(query_param)

        if not is_valid_query:
            return MagicMock(
                status_code=400, json=lambda: {"error": f"Invalid query {query_param}"}
            )

        # Mapping query characteristics to the corresponding key in the mock response dictionary
        query_to_key_map = {
            (
                "Status LIKE '%Mock%'" in query_param
                and "Status LIKE '%Status%'" in query_param
                and "Subject LIKE '%task%'" in query_param
                and "Subject LIKE '%subject%'" in query_param
            ): "contains_content_criteria_query",
            (
                "Status LIKE '%Unique%'" in query_param
                and "Status LIKE '%Other%'" in query_param
                and "Subject LIKE '%Unique Subject%'" in query_param
            ): "unique_values_content_criteria_query",
            (
                "Id IN" in query_param and "AccountId != null" in query_param
            ): "fetch_contacts_by_ids_and_non_null_accounts",
            (
                "FROM Opportunity" in query_param
                and "CreatedDate >= " in query_param
                and "AccountId IN" in query_param
            ): "fetch_opportunities_by_account_ids_from_date",
            (
                "FROM Event" in query_param
                and "CreatedDate >= " in query_param
                and "WhoId IN" in query_param
            ): "fetch_events_by_account_ids_from_date",
            (
                "AccountId IN" in query_param and "FROM Contact" in query_param
            ): "fetch_contacts_by_account_ids",
            ("SELECT Id FROM Account" in query_param): "fetch_accounts_not_in_ids",
        }

        # Determine which mock response to use based on the query characteristics
        for condition, key in query_to_key_map.items():
            if condition:
                mock_responses = sobject_api_mock_response_by_request_key.get(key)
                mock_response = mock_responses.pop(0) if mock_responses else None
                if mock_response:
                    return MagicMock(status_code=200, json=lambda: mock_response)
                else:
                    return MagicMock(
                        status_code=404,
                        json=lambda: {
                            "error": f"No more mock data available for endpoint {key}"
                        },
                    )

        return MagicMock(status_code=404, json=lambda: {"error": "Not found"})
    except Exception as e:
        raise Exception(f"An error occurred while processing the query: {str(e)}")


# mock data
def get_n_mock_tasks_per_x_contacts_for_contains_content_crieria_query(n, x):
    if x > len(MOCK_CONTACT_IDS):
        raise ValueError("Number of contacts exceeds the number of mock contact")
    if n > 3:
        raise ValueError("Number of tasks exceeds the number of mock tasks")
    cloned_tasks = []
    for i in range(x):
        for j in range(n):
            task_copy = TaskSObject(**mock_tasks_for_criteria_with_contains_content[j])
            task_copy.WhoId = MOCK_CONTACT_IDS[i]
            cloned_tasks.append(task_copy.to_dict())
    return cloned_tasks


def get_n_mock_tasks_per_x_contacts_for_unique_values_content_criteria_query(n, x):
    if x > len(MOCK_CONTACT_IDS):
        raise ValueError("Number of contacts exceeds the number of mock contact")
    if n > 3:
        raise ValueError("Number of tasks exceeds the number of mock tasks")
    cloned_tasks = []
    for i in range(x):
        for j in range(n):
            task_copy = TaskSObject(
                **mock_tasks_for_criteria_with_unique_values_content[j]
            )
            task_copy.WhoId = MOCK_CONTACT_IDS[i]
            cloned_tasks.append(task_copy.to_dict())
    return cloned_tasks


def get_three_mock_tasks_per_two_contacts_for_contains_content_criteria_query():
    return get_n_mock_tasks_per_x_contacts_for_contains_content_crieria_query(3, 2)


def get_one_mock_task_per_contact_for_contains_content_criteria_query():
    return get_n_mock_tasks_per_x_contacts_for_contains_content_crieria_query(
        1, len(MOCK_CONTACT_IDS)
    )


def get_thirty_mock_tasks_across_ten_contacts_for_contains_content_criteria_query():
    return get_n_mock_tasks_per_x_contacts_for_contains_content_crieria_query(3, 10)


def get_thirty_mock_tasks_across_ten_contacts_for_unique_values_content_criteria_query():
    return get_n_mock_tasks_per_x_contacts_for_unique_values_content_criteria_query(
        3, 10
    )


def get_n_mock_contacts_for_account(n, account_id):
    contacts = []
    for range_index in range(n):
        contact = {
            "Id": f"mock_contact_id{range_index}",
            "FirstName": f"MockFirstName{range_index}",
            "LastName": f"MockLastName{range_index}",
            "AccountId": account_id,
            "Account": {"Name": f"MockAccountName_{range_index + 1}"},
        }
        contacts.append(contact)
    return contacts


def get_ten_mock_contacts_spread_across_five_accounts():
    contacts = []
    for i, contact_id in enumerate(MOCK_CONTACT_IDS):
        account_index = i // 2  # This will assign two contacts per account
        contact = {
            "Id": contact_id,
            "FirstName": f"MockFirstName{i}",
            "LastName": f"MockLastName{i}",
            "AccountId": MOCK_ACCOUNT_IDS[account_index],
            "Account": {"Name": f"MockAccountName_{account_index + 1}"},
        }
        contacts.append(contact)
    return contacts


def get_five_mock_accounts():
    accounts = []
    for i, account_id in enumerate(MOCK_ACCOUNT_IDS):
        account = {
            "Id": account_id,
            "Name": f"MockAccountName_{i + 1}",
        }
        accounts.append(account)
    return accounts


def get_mock_opportunity_for_account(account_id):
    return OpportunitySObject(
        Id=f"mock_opportunity_id_{random.randint(1000, 9999)}",
        Name=f"Mock Opportunity",
        AccountId=account_id,
        Amount=round(random.uniform(1000, 100000), 2),
        StageName="Prospecting",
        CreatedDate=today,
    ).to_dict()


def get_mock_event_for_contact(contact_id):
    return {
        "Id": f"mock_event_id_{random.randint(1000, 9999)}",
        "Subject": "Mock Event",
        "WhoId": contact_id,
        "CreatedDate": today,
        "StartDateTime": today,
        "EndDateTime": today,
    }


def get_mock_http_response_json(data):
    return {
        "totalSize": len(data),
        "done": True,
        "records": data,
    }
