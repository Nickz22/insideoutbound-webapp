import random, copy
from app.tests.utils import is_valid_salesforce_query
from unittest.mock import MagicMock, AsyncMock
from app.tests.c import (
    mock_tasks_for_criteria_with_contains_content,  # 3
    mock_tasks_for_criteria_with_unique_values_content,  # 3
)
from typing import List, Dict
from datetime import datetime
from app.data_models import Contact, Account, UserModel
from app.log_config import log_message

MOCK_CONTACT_IDS = [f"mock_contact_id{i}" for i in range(10)]
MOCK_ACCOUNT_IDS = [f"mock_account_id{i}" for i in range(1, 6)]
MOCK_ACCOUNT_FIELD_DESCRIBE_RESULT = {
    "fields": [
        {"name": "Id", "label": "Account ID", "type": "id"},
        {"name": "Name", "label": "Account Name", "type": "string"},
        {"name": "BillingStreet", "label": "Billing Street", "type": "textarea"},
        {"name": "Phone", "label": "Phone", "type": "phone"},
        {"name": "Industry", "label": "Industry", "type": "picklist"},
    ]
}


today = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000+0000")

# each test should set this map to mock the appropriate response
sobject_api_mock_response_by_request_key: Dict[str, List[Dict]] = {
    "fetch_all_matching_tasks": [],
    "fetch_contact_by_id_map": [],
    "fetch_events_by_contact_ids_from_date": [],
    "fetch_opportunities_by_account_ids_from_date": [],
    "fetch_logged_in_salesforce_user": [],
    "fetch_salesforce_users": [],
}

# Add this new dictionary for permanent mock responses
permanent_mock_responses = {
    "fetch_sobject_fields__account": MOCK_ACCOUNT_FIELD_DESCRIBE_RESULT
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

mock_contacts_for_map = []

def set_mock_contacts_for_map(contacts: List[Contact]):
    global mock_contacts_for_map
    mock_contacts_for_map = contacts


def get_mock_contacts_for_map() -> List[Contact]:
    return mock_contacts_for_map


def mock_fetch_contact_by_id_map(contact_ids: List[str]) -> Dict[str, Contact]:
    return {
        contact.id: contact
        for contact in get_mock_contacts_for_map()
        if contact.id in contact_ids
    }
    
def mock_fetch_contacts_by_account_ids(account_ids: List[str]) -> List[Contact]:
    return [
        contact
        for contact in get_mock_contacts_for_map()
        if contact.account_id in account_ids
    ]


def response_based_on_query(url, **kwargs):
    """
    Mocks the response of a GET or POST request to Salesforce's API
    """
    log_message(f"URL: {url}", "debug")
    log_message(f"Parameters: {kwargs}", "debug")
    log_message(f"Return raw data: {kwargs.get('return_raw_data', False)}", "debug")
    try:
        query_param = kwargs.get("params", {}).get("q", "") or url
        json_data = kwargs.get("json", {})
        is_valid_query = (
            "/describe" in url
            or is_valid_salesforce_query(query_param)
            or "services/data/v55.0/composite" in url
        )
        return_raw_data = kwargs.get("return_raw_data", False)
        if not is_valid_query:
            raise ValueError(f"Invalid query {query_param}")

        # Mapping query characteristics to the corresponding key in the mock response dictionary
        query_to_key_map = {
            (
                "FROM Opportunity" in query_param
            ): "fetch_opportunities_by_account_ids_from_date",
            ("FROM Event" in query_param): "fetch_events_by_contact_ids_from_date",
            ("Account" in url and "describe" in url): "fetch_sobject_fields__account",
            ("FROM User" in query_param): "fetch_salesforce_users",
            (
                "SELECT Id, WhoId, OwnerId, Priority, WhatId, Subject, Status, CallDurationInSeconds, CallType, CallDisposition, CreatedDate, CreatedById, TaskSubtype"
                in query_param
            ): "fetch_all_matching_tasks",
            (
                "Account.Owner.FirstName, Account.Owner.LastName, Account.Owner.Id"
                and "FROM Contact" in query_param
            ): "fetch_contact_by_id_map",
            ("services/data/v55.0/composite" in url): "fetch_contact_by_id_map",
        }

        # Determine which mock response to use based on the query characteristics
        for condition, key in query_to_key_map.items():
            if not condition:
                continue

            mock_response = None
            if key in permanent_mock_responses:
                mock_response = permanent_mock_responses[key]
            else:
                mock_responses = sobject_api_mock_response_by_request_key.get(key)
                mock_response = mock_responses.pop(0) if mock_responses else None

            if mock_response:
                if (
                    key == "fetch_contact_by_id_map"
                    and "services/data/v55.0/composite" in url
                ):
                    return sobject_api_mock_response_by_request_key[
                        "fetch_contact_by_id_map"
                    ]
                elif not return_raw_data:
                    return MagicMock(status_code=200, json=lambda: mock_response)
                else:
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
            task_copy["WhoId"] = contact.id
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
            task_copy["WhoId"] = contacts[i].id
            task_copy["OwnerId"] = assignee_id
            cloned_tasks.append(task_copy)
    return cloned_tasks


def get_n_mock_contacts_for_account(n, account_id) -> List[Contact]:
    contacts = []
    for range_index in range(n):
        account = Account(
            id=account_id,
            name=f"MockAccountName_{range_index + 1}",
            owner=UserModel(id="mock_owner_id", firstName="Mock", lastName="Owner"),
        )
        contact = Contact(
            id=f"mock_contact_id{range_index}",
            first_name=f"MockFirstName{range_index}",
            last_name=f"MockLastName{range_index}",
            account_id=account_id,
            account=account,
        )
        contacts.append(contact)
    return contacts


def get_two_mock_contacts_per_account(accounts) -> List[Contact]:
    mock_contacts = []
    for account in accounts:
        for i in range(2):
            account_model = Account(
                id=account["Id"],
                name=account["Name"],
                owner=UserModel(
                    id=account["Owner"]["Id"],
                    firstName=account["Owner"]["FirstName"],
                    lastName=account["Owner"]["LastName"],
                ),
            )

            contact = Contact(
                id=f"mock_contact_id_{account['Id']}_{i}",
                first_name=f"MockFirstName_{account['Id']}_{i}",
                last_name=f"MockLastName_{account['Id']}_{i}",
                account_id=account["Id"],
                account=account_model,
                owner_id=account["Owner"]["Id"],
            )
            mock_contacts.append(contact)

    return mock_contacts


def get_five_mock_accounts(owner_id="mock_owner_id"):
    accounts = []
    for i, account_id in enumerate(MOCK_ACCOUNT_IDS):
        account = {
            "Id": account_id,
            "Name": f"MockAccountName_{i + 1}",
            "Owner": {"Id": owner_id, "FirstName": "Mock", "LastName": "Owner"},
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
