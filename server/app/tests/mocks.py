import random, copy, re
from aiohttp import web
from app.tests.utils import is_valid_salesforce_query
from unittest.mock import MagicMock
from app.tests.c import (
    mock_tasks_for_criteria_with_contains_content,  # 3
    mock_tasks_for_criteria_with_unique_values_content,  # 3
)
from typing import List, Dict
from datetime import datetime

MOCK_CONTACT_IDS = [f"mock_contact_id{i}" for i in range(10)]
MOCK_ACCOUNT_IDS = [f"mock_account_id{i}" for i in range(1, 6)]
MOCK_ACCOUNT_FIELD_DESCRIBE_RESULT = [
    {
        "fields": [
            {"name": "Id", "label": "Account ID", "type": "id"},
            {"name": "Name", "label": "Account Name", "type": "string"},
            {"name": "BillingStreet", "label": "Billing Street", "type": "textarea"},
            {"name": "Phone", "label": "Phone", "type": "phone"},
            {"name": "Industry", "label": "Industry", "type": "picklist"},
        ]
    }
]


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
    "fetch_logged_in_salesforce_user": [],
    "fetch_sobject_fields__account": MOCK_ACCOUNT_FIELD_DESCRIBE_RESULT,
    "fetch_salesforce_users": []
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

import re

def mock_fetch_sobjects_async(soql_query, credentials, session):
    return response_based_on_query(soql_query, return_raw_data=True)

def response_based_on_query(url, **kwargs):
    """
    Mocks the response of a GET request to Salesforce's SObject API
    """
    print(f"URL: {url}")
    print(f"Parameters: {kwargs}")
    print(f"Return raw data: {kwargs.get('return_raw_data', False)}")
    try:
        query_param = kwargs.get("params", {}).get("q", "") or url
        is_valid_query = "/describe" or is_valid_salesforce_query(query_param) in url
        return_raw_data = kwargs.get('return_raw_data', False)
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
            ("SELECT Id,Name,Industry,AnnualRevenue,NumberOfEmployees,CreatedDate FROM Account" in query_param): "fetch_accounts_not_in_ids",
            ("Account" in url and "describe" in url): "fetch_sobject_fields__account",
            ("FROM User" in query_param): "fetch_salesforce_users",
        }

        # Determine which mock response to use based on the query characteristics
        for condition, key in query_to_key_map.items():
            if condition:
                mock_responses = sobject_api_mock_response_by_request_key.get(key)
                mock_response = mock_responses.pop(0) if mock_responses else None
                if mock_response and not return_raw_data:
                    return MagicMock(status_code=200, json=lambda: mock_response)
                elif mock_response and return_raw_data:
                    return mock_response["records"]
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

def get_n_mock_tasks_for_contacts_for_unique_values_content_criteria_query(
    n, contacts, assignee_id
):
    if n > 3:
        raise ValueError("Number of tasks exceeds the number of mock tasks")
    cloned_tasks = []
    for i, contact in enumerate(contacts):
        for j in range(n):
            task_copy = copy.deepcopy(
                mock_tasks_for_criteria_with_unique_values_content[j]
            )
            task_copy["Id"] = f"mock_task_id_{i}_{j}"
            task_copy["WhoId"] = contact["Id"]
            task_copy["OwnerId"] = assignee_id
            cloned_tasks.append(task_copy)
    return cloned_tasks

def get_n_mock_tasks_per_contact_for_contains_content_crieria_query(
    n, contacts, assignee_id
):
    if len(contacts) > len(MOCK_CONTACT_IDS):
        raise ValueError("Number of contacts exceeds the number of mock contact")
    if n > 3:
        raise ValueError("Number of tasks exceeds the number of mock tasks")
    cloned_tasks = []
    for i in range(len(contacts)):
        for j in range(n):
            task_copy = copy.deepcopy(mock_tasks_for_criteria_with_contains_content[j])
            task_copy["Id"] = f"mock_task_id_{i}_{j}"
            task_copy["WhoId"] = contacts[i]["Id"]
            task_copy["OwnerId"] = assignee_id
            cloned_tasks.append(task_copy)
    return cloned_tasks

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

def get_two_mock_contacts_per_account(accounts):
    mock_contacts = []
    for account in accounts:
        for i in range(2):
            contact = {
                "Id": f"mock_contact_id_{account['Id']}_{i}",
                "FirstName": f"MockFirstName_{account['Id']}_{i}",
                "LastName": f"MockLastName_{account['Id']}_{i}",
                "AccountId": account["Id"],
                "Account": {"Id": account["Id"], "Name": account["Name"]},
            }
            mock_contacts.append(contact)

    return mock_contacts


def get_five_mock_accounts(owner_id="mock_owner_id"):
    accounts = []
    for i, account_id in enumerate(MOCK_ACCOUNT_IDS):
        account = {
            "Id": account_id,
            "Name": f"MockAccountName_{i + 1}",
        }
        accounts.append(account)
    return accounts


def get_mock_opportunity_for_account(account_id):
    return {
        "Id": f"mock_opportunity_id_{random.randint(1000, 9999)}",
        "Name": "Mock Opportunity",
        "AccountId": account_id,
        "Amount": 1733.42,
        "StageName": "Prospecting",
        "CreatedDate": today,
        "CloseDate": datetime.today().date().isoformat(),
    }


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
