import requests
import asyncio
import aiohttp
from flask import current_app as app
from typing import List, Dict
from app.utils import pluck, format_error_message, group_by
from app.data_models import (
    ApiResponse,
    Contact,
    Account,
    CriteriaField,
    FilterContainer,
    SObjectFieldModel,
    UserModel,
    UserSObject,
    TokenData,
)
from app.database.supabase_connection import get_session_state
from app.constants import SESSION_EXPIRED, FILTER_OPERATOR_MAPPING
import concurrent.futures
from config import Config
import logging


def get_credentials():
    session_state = get_session_state()

    return session_state["access_token"], session_state["instance_url"]


VALID_FIELD_TYPES = ("string", "picklist", "combobox", "int")


def fetch_criteria_fields(sobject_type: str) -> List[CriteriaField]:
    """
    Fetches the field describe info from Salesforce for the Task object and creates CriteriaField instances.

    Returns:
    - List[CriteriaField]: A list of CriteriaField instances representing fields of the Task object.
    """
    api_response = ApiResponse(data=[], message="", success=False)

    try:
        fields_data = _fetch_object_fields(sobject_type, get_credentials()).data
        criteria_fields = [
            CriteriaField(
                name=field["name"],
                type="string" if field["type"] != "int" else "number",
                options=(
                    [
                        picklist
                        for picklist in field["picklistValues"]
                        if picklist["active"]
                    ]
                    if field["type"] == "picklist"
                    else []
                ),
            )
            for field in fields_data
            if field["type"] in VALID_FIELD_TYPES or field["name"] == "Id"
        ]
        api_response.data = criteria_fields
        api_response.success = True
    except Exception as e:
        api_response.message = (
            f"While getting criteria fields {format_error_message(e)}"
        )

    return api_response


def fetch_salesforce_users(ids: list[str] = None) -> ApiResponse:
    """
    Fetches Salesforce users from Salesforce.

    Returns:
    - ApiResponse: An ApiResponse object containing the fetched Salesforce users as a list of dictionaries.

    Throws:
    - Exception: Raises an exception with a formatted error message if any error occurs during the fetch operation.
    """
    api_response = ApiResponse(data=[], message="", success=False)

    try:
        soql_query = "SELECT Id,Email,FirstName,LastName,Username,FullPhotoUrl,UserRole.Name FROM User"

        if ids:
            soql_query += " WHERE Id IN ({})".format(",".join(f"'{id}'" for id in ids))

        response = _fetch_sobjects(soql_query, get_credentials())
        for entry in response.data:

            entry["Role"] = (
                entry["UserRole"]["Name"] if entry.get("UserRole") is not None else None
            )
            if "UserRole" in entry:
                del entry["UserRole"]
            if "attributes" in entry:
                del entry["attributes"]

        users = [
            UserModel.from_sobject(
                UserSObject(**{k: v for k, v in entry.items() if k != "attributes"})
            )
            for entry in response.data
        ]
        api_response.data = users
        api_response.success = True
    except Exception as e:
        raise Exception(format_error_message(e))

    return api_response


def fetch_any_prospecting_activity_from_date(
    start: str, criteria: List[FilterContainer], salesforce_user_ids: List[str]
) -> List[Dict]:
    joined_user_ids = "','".join(salesforce_user_ids)
    base_query = f"SELECT WhoId FROM Task WHERE CreatedDate >= {start} AND OwnerId IN ('{joined_user_ids}') AND "

    all_tasks = []
    for filter_container in criteria:
        combined_conditions = _construct_where_clause_from_filter(filter_container)
        full_query = f"{base_query} {combined_conditions}"

        tasks = _fetch_sobjects(full_query, get_credentials())
        all_tasks.extend(tasks)

    return all_tasks


async def fetch_prospecting_tasks_by_account_ids_from_date_not_in_ids(
    start: str,
    criteria: List[FilterContainer],
    already_counted_task_ids: List[str],
    salesforce_user_ids: List[str],
) -> ApiResponse:
    api_response = ApiResponse(data={}, message="", success=False)

    # 1. Fetch all tasks meeting any criteria
    print("Fetching all matching tasks")
    all_tasks = fetch_all_matching_tasks(start, criteria, salesforce_user_ids).data

    # 2. Group tasks by WhoId
    print("Grouping tasks by WhoId")
    tasks_by_who_id = group_by(all_tasks, "WhoId")

    # 3. Fetch contacts for these WhoIds
    print("Fetching contacts for these WhoIds")
    contact_by_id = await fetch_contact_by_id_map(list(tasks_by_who_id.keys()))

    # 4 & 5. Group tasks by AccountId and criteria
    print("Grouping tasks by AccountId and criteria")
    tasks_by_account_and_criteria = group_tasks_by_account_and_criteria(
        tasks_by_who_id, contact_by_id, criteria, already_counted_task_ids
    )

    api_response.data = tasks_by_account_and_criteria
    api_response.success = True
    api_response.message = "Tasks fetched and organized successfully"

    return api_response


def fetch_all_matching_tasks(
    start: str, criteria: List[FilterContainer], salesforce_user_ids: List[str]
) -> List[Dict]:
    combined_criteria = " OR ".join(
        [_construct_where_clause_from_filter(fc) for fc in criteria]
    )
    soql_query = f"""
    SELECT Id, WhoId, OwnerId, Priority, WhatId, Subject, Status, CallDurationInSeconds, CallType, CallDisposition, CreatedDate, CreatedById, TaskSubtype
    FROM Task
    WHERE CreatedDate >= {start}
    AND OwnerId IN ('{("','".join(salesforce_user_ids))}')
    AND ({combined_criteria})
    """
    return _fetch_sobjects(soql_query, get_credentials())


async def fetch_contacts_by_account_ids(account_ids: List[str]) -> List[Contact]:
    contact_batch_size = 300
    composite_batch_size = 5
    account_batches = [
        account_ids[i : i + contact_batch_size]
        for i in range(0, len(account_ids), contact_batch_size)
    ]
    composite_batches = [
        account_batches[i : i + composite_batch_size]
        for i in range(0, len(account_batches), composite_batch_size)
    ]

    async with aiohttp.ClientSession() as session:
        contact_fetch_jobs = [
            fetch_contact_composite_batch_by_account(batch, session)
            for batch in composite_batches
        ]
        results = await asyncio.gather(*contact_fetch_jobs)

    contacts = []
    for result in results:
        for batch_result in result:
            contacts.extend(batch_result)

    return contacts


async def fetch_contact_composite_batch_by_account(
    account_batches: List[List[str]], session: aiohttp.ClientSession
) -> List[List[Contact]]:
    access_token, instance_url = get_credentials()
    if not access_token or not instance_url:
        raise Exception("Session expired")

    composite_request = {"allOrNone": False, "compositeRequest": []}

    for i, batch in enumerate(account_batches):
        account_id_filter = "','".join(batch)
        composite_request["compositeRequest"].append(
            {
                "method": "GET",
                "url": f"/services/data/v55.0/query/?q=SELECT Id,FirstName,LastName,AccountId FROM Contact WHERE AccountId IN ('{account_id_filter}')",
                "referenceId": f"ContactQuery{i}",
            }
        )

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    async with session.post(
        f"{instance_url}/services/data/v55.0/composite",
        json=composite_request,
        headers=headers,
    ) as response:
        if response.status != 200:
            raise Exception(f"API request failed: {await response.text()}")

        data = await response.json()
        results = []
        for composite_response in data["compositeResponse"]:
            result = []
            contacts = composite_response["body"]["records"]

            # Process initial batch of contacts
            result.extend(_process_contacts(contacts))

            # Fetch and process remaining contacts if any
            next_records_url = composite_response["body"].get("nextRecordsUrl")
            while next_records_url:
                async with session.get(
                    f"{instance_url}{next_records_url}", headers=headers
                ) as next_response:
                    if next_response.status != 200:
                        raise Exception(
                            f"API request failed: {await next_response.text()}"
                        )

                    next_data = await next_response.json()
                    result.extend(_process_contacts(next_data["records"]))
                    next_records_url = next_data.get("nextRecordsUrl")

            results.append(result)
        return results


def _process_contacts(contacts):
    return [
        Contact(
            id=contact["Id"],
            first_name=contact["FirstName"] or "",
            last_name=contact["LastName"] or "",
            account_id=contact["AccountId"],
        )
        for contact in contacts
        if contact.get("AccountId")
    ]


import time


async def fetch_contact_by_id_map(contact_ids: List[str]) -> Dict[str, str]:
    start_time = time.time()
    print(f"Starting fetch_contact_by_id_map for {len(contact_ids)} contacts")

    contact_batch_size = 300
    composite_batch_size = 3  # Reduced from 5 to 3
    contact_batches = [
        contact_ids[i : i + contact_batch_size]
        for i in range(0, len(contact_ids), contact_batch_size)
    ]
    composite_batches = [
        contact_batches[i : i + composite_batch_size]
        for i in range(0, len(contact_batches), composite_batch_size)
    ]

    async with aiohttp.ClientSession() as session:
        contact_by_id = {}
        for i, batch in enumerate(composite_batches):
            print(f"Processing composite batch {i+1} of {len(composite_batches)}")
            results = await fetch_contact_composite_batch(batch, session)
            for result in results:
                contact_by_id.update(result)

            if i < len(composite_batches) - 1:  # Don't wait after the last batch
                await asyncio.sleep(0.5)  # 0.5 second delay between composite batches

    end_time = time.time()
    print(
        f"Completed fetch_contact_by_id_map. Total contacts processed: {len(contact_by_id)}. Time taken: {end_time - start_time:.2f} seconds"
    )
    return contact_by_id


import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Create logger
logger = logging.getLogger(__name__)


async def fetch_contact_composite_batch(
    contact_batches: List[List[str]], session: aiohttp.ClientSession
) -> List[Dict[str, Account]]:
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # seconds
    TIMEOUT = 10  # seconds

    async def make_request_with_retry(request_func, *args, **kwargs):
        for attempt in range(MAX_RETRIES):
            try:
                return await asyncio.wait_for(
                    request_func(*args, **kwargs), timeout=TIMEOUT
                )
            except asyncio.TimeoutError:
                if attempt == MAX_RETRIES - 1:
                    raise
                logger.warning(
                    f"Request timed out after {TIMEOUT} seconds. Retrying in {RETRY_DELAY} seconds... (Attempt {attempt + 1}/{MAX_RETRIES})"
                )
                await asyncio.sleep(RETRY_DELAY)
            except Exception as e:
                if attempt == MAX_RETRIES - 1:
                    raise
                logger.warning(
                    f"Request failed: {str(e)}. Retrying in {RETRY_DELAY} seconds... (Attempt {attempt + 1}/{MAX_RETRIES})"
                )
                await asyncio.sleep(RETRY_DELAY)

    async def make_composite_request():
        async with session.post(
            f"{instance_url}/services/data/v55.0/composite",
            json=composite_request,
            headers=headers,
        ) as response:
            if response.status != 200:
                raise Exception(f"API request failed: {await response.text()}")
            return await response.json()

    async def fetch_next_records(url):
        await asyncio.sleep(0.5)  # 0.5 second delay before each pagination request
        async with session.get(
            f"{instance_url}{url}", headers=headers
        ) as next_response:
            if next_response.status != 200:
                raise Exception(f"API request failed: {await next_response.text()}")
            return await next_response.json()

    access_token, instance_url = get_credentials()
    if not access_token or not instance_url:
        raise Exception("Session expired")

    print(f"Fetching contacts for batch with {len(contact_batches)} batches")

    composite_request = {"allOrNone": False, "compositeRequest": []}

    account_fields = _fetch_object_fields("Account", get_credentials()).data

    blacklist = {
        "isdeleted",
        "masterrecordid",
        "parentid",
        "billinglatitude",
        "billinglongitude",
        "billingcodegeoaccuracy",
        "shippinglatitude",
        "shippinglongitude",
        "photourl",
        "dandbcompanyid",
    }

    filtered_account_fields = [
        field["name"]
        for field in account_fields
        if "reference" not in field["type"].lower()
        and field["name"].lower() not in blacklist
    ]
    filtered_account_fields.extend(["Owner.FirstName", "Owner.LastName", "Owner.Id"])

    account_fields_str = ", ".join(
        [f"Account.{field}" for field in filtered_account_fields]
    )

    for i, batch in enumerate(contact_batches):
        contact_id_filter = "','".join(batch)
        composite_request["compositeRequest"].append(
            {
                "method": "GET",
                "url": f"/services/data/v55.0/query/?q=SELECT Id,FirstName,LastName,AccountId, {account_fields_str} FROM Contact WHERE Id IN ('{contact_id_filter}')",
                "referenceId": f"ContactQuery{i}",
            }
        )

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    start_time = time.time()
    try:
        data = await make_request_with_retry(make_composite_request)
        logger.info(
            f"Composite request successful. Time taken: {time.time() - start_time:.2f} seconds"
        )
    except Exception as e:
        logger.error(f"Composite request failed after {MAX_RETRIES} attempts: {str(e)}")
        return []

    results = []
    for composite_response in data["compositeResponse"]:
        result = {}
        contacts = composite_response["body"]["records"]

        print(f"Processing {len(contacts)} contacts from initial batch")
        for contact in contacts:
            if contact.get("AccountId"):
                result[contact["Id"]] = _process_contact(contact)

        next_records_url = composite_response["body"].get("nextRecordsUrl")
        page_count = 1
        while next_records_url:
            print(f"Fetching next records url (page {page_count}): {next_records_url}")
            try:
                next_data = await make_request_with_retry(
                    fetch_next_records, next_records_url
                )
                logger.info(
                    f"Next records request successful. Time taken: {time.time() - start_time:.2f} seconds"
                )
            except Exception as e:
                logger.error(
                    f"Next records request failed after {MAX_RETRIES} attempts: {str(e)}"
                )
                break

            print(
                f"Processing {len(next_data['records'])} contacts from page {page_count}"
            )
            for contact in next_data["records"]:
                if contact.get("AccountId"):
                    result[contact["Id"]] = _process_contact(contact)

            next_records_url = next_data.get("nextRecordsUrl")
            page_count += 1

        print(f"Finished processing batch. Total contacts: {len(result)}")
        results.append(result)

    print(f"Completed fetch_contact_composite_batch. Total batches: {len(results)}")
    return results


def _process_contact(contact):
    account_data = contact["Account"]
    return Contact(
        id=contact["Id"],
        first_name=contact["FirstName"] or "",
        last_name=contact["LastName"] or "",
        account_id=contact["AccountId"],
        account=Account(
            id=account_data.get("Id"),
            name=account_data.get("Name"),
            owner_id=account_data.get("Owner", {}).get("Id"),
            created_date=account_data.get("CreatedDate"),
            owner=(
                UserModel(
                    id=account_data.get("Owner", {}).get("Id"),
                    firstName=account_data.get("Owner", {}).get("FirstName"),
                    lastName=account_data.get("Owner", {}).get("LastName"),
                )
                if account_data.get("Owner")
                else None
            ),
        ),
    )


def group_tasks_by_account_and_criteria(
    tasks_by_who_id: Dict[str, List[Dict]],
    contact_by_id: Dict[str, Contact],
    criteria: List[FilterContainer],
    already_counted_task_ids: List[str],
) -> Dict[str, Dict[str, Dict[str, List[Dict]]]]:
    tasks_by_account_and_criteria = {}

    def process_criterion(criterion):
        criterion_results = {}
        for who_id, tasks in tasks_by_who_id.items():
            contact = contact_by_id.get(who_id)
            if not contact:
                continue
            account = contact.account
            for task in tasks:
                if task["Id"] in already_counted_task_ids:
                    continue
                if criterion.matches(task):
                    # Assign the Account to the task
                    task["Account"] = account
                    task["Contact"] = contact
                    if account.id not in criterion_results:
                        criterion_results[account.id] = {}
                    if who_id not in criterion_results[account.id]:
                        criterion_results[account.id][who_id] = {}
                    if criterion.name not in criterion_results[account.id][who_id]:
                        criterion_results[account.id][who_id][criterion.name] = []
                    criterion_results[account.id][who_id][criterion.name].append(task)
        return criterion_results

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_criterion = {
            executor.submit(process_criterion, criterion): criterion
            for criterion in criteria
        }
        for future in concurrent.futures.as_completed(future_to_criterion):
            criterion_results = future.result()
            for account_id, who_id_data in criterion_results.items():
                if account_id not in tasks_by_account_and_criteria:
                    tasks_by_account_and_criteria[account_id] = {}
                for who_id, criteria_data in who_id_data.items():
                    if who_id not in tasks_by_account_and_criteria[account_id]:
                        tasks_by_account_and_criteria[account_id][who_id] = {}
                    tasks_by_account_and_criteria[account_id][who_id].update(
                        criteria_data
                    )

    return tasks_by_account_and_criteria


def fetch_tasks_by_user_ids(user_ids: List[str], limit: int = None):
    """
    Fetches tasks from Salesforce based on a list of user IDs.

    Parameters:
    - user_ids (list[str]): A list of user IDs to fetch tasks for.
    - fields (list[str]): A list of field names to fetch for each task.

    Returns:
    - ApiResponse: An ApiResponse object containing the fetched tasks as a list of Task objects.

    Throws:
    - Exception: Raises an exception with a formatted error message if any error occurs during the fetch operation.
    """
    api_response = ApiResponse(data=[], message="", success=False)

    try:
        joined_user_ids = "','".join(user_ids)
        task_fields = pluck(fetch_task_fields().data, "name")
        soql_query = f"SELECT {','.join(task_fields)} FROM Task WHERE OwnerId IN ('{joined_user_ids}')"
        if limit:
            soql_query += f" LIMIT {limit}"
        api_response.data = [
            {key: value for key, value in entry.items() if key != "attributes"}
            for entry in _fetch_sobjects(soql_query, get_credentials()).data
        ]
        api_response.success = True
    except Exception as e:
        error_msg = format_error_message(e)
        print(error_msg)
        raise Exception(error_msg)

    return api_response


def get_task_query_count(filter_container, salesforce_user_ids):
    api_response = ApiResponse(data=[], message="", success=False)
    try:
        soql_query = "SELECT COUNT() FROM Task WHERE "
        combined_conditions = _construct_where_clause_from_filter(filter_container)

        if salesforce_user_ids:
            joined_user_ids = "','".join(salesforce_user_ids)
            soql_query += f"OwnerId IN ('{joined_user_ids}') AND "

        soql_query += combined_conditions

        response = _fetch_sobjects_count(soql_query, get_credentials())

        count = response.data

        api_response.data = [{"count": count}]
        api_response.success = True
        api_response.message = "Task count retrieved successfully"
    except Exception as e:
        raise Exception(format_error_message(e))

    return api_response


def fetch_events_by_user_ids(user_ids: List[str], limit: int = None):
    """
    Fetches events from Salesforce based on a list of user IDs.

    Parameters:
    - user_ids (list[str]): A list of user IDs to fetch events for.
    - fields (list[str]): A list of field names to fetch for each event.

    Returns:
    - ApiResponse: An ApiResponse object containing the fetched events as a list of Event objects.

    Throws:
    - Exception: Raises an exception with a formatted error message if any error occurs during the fetch operation.
    """
    api_response = ApiResponse(data=[], message="", success=False)

    try:
        joined_user_ids = "','".join(user_ids)
        event_fields = pluck(fetch_event_fields().data, "name")
        soql_query = f"SELECT {','.join(event_fields)} FROM Event WHERE OwnerId IN ('{joined_user_ids}')"
        if limit:
            soql_query += f" LIMIT {limit}"
        api_response.data = [
            {key: value for key, value in entry.items() if key != "attributes"}
            for entry in _fetch_sobjects(soql_query, get_credentials()).data
        ]
        api_response.success = True
    except Exception as e:
        raise Exception(format_error_message(e))

    return api_response


def fetch_events_by_contact_ids_from_date(
    contact_ids: List[str],
    start: str,
    salesforce_user_ids: List[str],
    meetings_criteria: FilterContainer,
):
    """
    Fetches events from Salesforce and post-processes them to match the given contact IDs.

    Parameters:
    - contact_ids (list[str]): A list of contact IDs to fetch events for
    - start (str): The start date for filtering events via CreatedDate, in ISO format
    - salesforce_user_ids (list[str]): A list of Salesforce user IDs to filter events by
    - meetings_criteria (FilterContainer): Criteria for filtering meetings

    Returns:
    - ApiResponse: An ApiResponse object containing a dictionary where each key is a contact ID
      and each value is the list of events for that contact.

    Throws:
    - Exception: Raises an exception with a formatted error message if any error occurs during the fetch
    """
    api_response = ApiResponse(data={}, message="", success=True)

    try:
        meeting_criteria_filter = _construct_where_clause_from_filter(meetings_criteria)
        joined_user_ids = "','".join(salesforce_user_ids)

        soql_query = f"""
        SELECT Id, WhoId, WhatId, Subject, CreatedDate, StartDateTime, EndDateTime 
        FROM Event 
        WHERE CreatedDate >= {start} 
        AND CreatedById IN ('{joined_user_ids}') 
        AND ({meeting_criteria_filter}) 
        ORDER BY StartDateTime ASC
        """

        response = _fetch_sobjects(soql_query, get_credentials())

        events_by_contact_id = {}
        for event in response.data:
            who_id = event.get("WhoId")
            if who_id in contact_ids:
                if who_id not in events_by_contact_id:
                    events_by_contact_id[who_id] = []
                events_by_contact_id[who_id].append(event)

        api_response.data = events_by_contact_id
        api_response.message = "Events fetched and filtered successfully."
    except Exception as e:
        api_response.success = False
        api_response.message = format_error_message(e)
        raise Exception(api_response.message)

    return api_response


def fetch_opportunities_by_account_ids_from_date(
    account_ids, start, salesforce_user_ids: List[str]
) -> List[Dict]:
    """
    Fetches opportunities from Salesforce based on a list of account IDs, querying once and filtering.
    """
    api_response = ApiResponse(data=[], message="", success=True)

    try:
        joined_user_ids = "','".join(salesforce_user_ids)
        soql_query = f"""
        SELECT Id, AccountId, Amount, CreatedDate, StageName, Name, CloseDate 
        FROM Opportunity 
        WHERE CreatedDate >= {start} 
        AND CreatedById IN ('{joined_user_ids}') 
        ORDER BY CreatedDate ASC
        """

        response = _fetch_sobjects(soql_query, get_credentials())
        api_response.data = [
            opp for opp in response.data if opp.get("AccountId") in account_ids
        ]

        api_response.success = True
        api_response.message = "Opportunities fetched and filtered successfully."
    except Exception as e:
        api_response.success = False
        api_response.message = format_error_message(e)
        raise Exception(api_response.message)

    return api_response


def fetch_logged_in_salesforce_user() -> ApiResponse:
    api_response = ApiResponse(data=[], message="", success=False)

    access_token, instance_url = get_credentials()

    if not access_token or not instance_url:
        api_response.message = "No valid Salesforce session found"
        return api_response

    url = f"{instance_url}/services/oauth2/userinfo"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # This will raise an HTTPError for bad responses
        user_data = response.json()
        api_response.data = UserModel(
            id=user_data["user_id"],
            email=user_data["email"],
            orgId=user_data["organization_id"],
            username=user_data["preferred_username"],
            lastName=user_data["family_name"],
            firstName=user_data["given_name"],
            photoUrl=user_data["picture"],
        )
        api_response.success = True
    except requests.exceptions.RequestException as e:
        api_response.message = f"Failed to fetch logged in user ID: {str(e)}"
        if isinstance(e, requests.exceptions.HTTPError) and (
            e.response.status_code == 401 or e.response.status_code == 403
        ):
            api_response.message = SESSION_EXPIRED
            api_response.type = "AuthenticationError"

    return api_response


def fetch_task_fields() -> ApiResponse:
    """
    Retrieves fields for the Task object from Salesforce.
    """

    api_response = ApiResponse(data=[], message="", success=False)

    response = _fetch_object_fields("Task", get_credentials())
    sobject_field_models = [
        SObjectFieldModel(type=entry["type"], name=entry["name"], label=entry["label"])
        for entry in response.data
        if entry["type"] in VALID_FIELD_TYPES or entry["name"] == "Id"
    ]

    if response.success:
        api_response.success = True
        api_response.data = sobject_field_models
    else:
        raise Exception(
            f"Failed to fetch Task fields ({response.status_code}): {get_http_error_message(response)}"
        )
    return api_response


def fetch_event_fields() -> ApiResponse:
    """
    Retrieves fields for the Event object from Salesforce.
    """

    api_response = ApiResponse(data=[], message="", success=False)

    response = _fetch_object_fields("Event", get_credentials())
    sobject_field_models = [
        SObjectFieldModel(type=entry["type"], name=entry["name"], label=entry["label"])
        for entry in response.data
        if entry["type"] in VALID_FIELD_TYPES or entry["name"] == "Id"
    ]

    if response.success:
        api_response.success = True
        api_response.data = sobject_field_models
    else:
        api_response.message = f"Failed to fetch Event fields ({response.status_code}): {get_http_error_message(response)}"
        api_response.status_code = response.status_code

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


def _fetch_object_fields(object_name, credentials):
    try:
        access_token, instance_url = credentials
        api_response = ApiResponse(data=[], message="", success=False)
        if not access_token or not instance_url:
            raise Exception("Session expired")
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(
            f"{instance_url}/services/data/v55.0/sobjects/{object_name}/describe",
            headers=headers,
        )
        if response.status_code == 200:
            fields = response.json()["fields"]
            api_response.success = True
            api_response.data = fields
            api_response.status_code = 200
        else:
            api_response.message = f"Failed to fetch {object_name} fields ({response.status_code}): {get_http_error_message(response)}"
            api_response.status_code = response.status_code
    except Exception as e:
        raise Exception(format_error_message(e))
    return api_response


def _fetch_sobjects_count(soql_query, credentials):
    try:
        access_token, instance_url = credentials
        if not access_token or not instance_url:
            raise Exception(SESSION_EXPIRED)
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(
            f"{instance_url}/services/data/v55.0/query",
            headers=headers,
            params={"q": soql_query},
        )
        if response.status_code == 200:
            return ApiResponse(
                success=True,
                data=response.json()["totalSize"],
                message=None,
                status_code=200,
            )
        else:
            raise Exception(
                f"Failed to fetch sobjects count ({response.status_code}): {get_http_error_message(response)}"
            )
    except Exception as e:
        raise Exception(format_error_message(e))


def _fetch_sobjects(soql_query, credentials):
    try:
        access_token, instance_url = credentials
        if not access_token or not instance_url:
            raise Exception(SESSION_EXPIRED)

        headers = {"Authorization": f"Bearer {access_token}"}
        url = f"{instance_url}/services/data/v55.0/query"

        all_records = []
        next_records_url = None

        while True:
            if next_records_url:
                response = requests.get(next_records_url, headers=headers)
            else:
                response = requests.get(url, headers=headers, params={"q": soql_query})

            response.raise_for_status()
            data = response.json()

            all_records.extend(data["records"])

            # Check if there are more records to fetch
            if data.get("done", True):
                break

            next_records_url = f"{instance_url}{data['nextRecordsUrl']}"

        return ApiResponse(
            success=True,
            data=all_records,
            message=None,
            status_code=200,
        )
    except requests.exceptions.RequestException as e:
        raise Exception(f"API request failed: {format_error_message(e)}")
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
    elif filter_obj.data_type == "string" and operator == "NOT LIKE":
        value = f" '%{value}%'"
    elif filter_obj.data_type == "string":
        value = f"'{value}'"
    elif filter_obj.data_type == "date" or filter_obj.data_type == "number":
        value = f"{value}"

    return f"{field} {operator}{value}"


def get_http_error_message(response):
    if response.status_code == 401:
        return f"{SESSION_EXPIRED}"
    elif isinstance(response.json(), dict):
        return response.json().get("error", "An error occurred")
    else:
        return response.json()[0].get("message", "An error occurred")


def refresh_access_token(refresh_token: str, is_sandbox: bool) -> ApiResponse:
    base_sf_domain = "test" if is_sandbox else "login"
    token_url = f"https://{base_sf_domain}.salesforce.com/services/oauth2/token"

    payload = {
        "grant_type": "refresh_token",
        "client_id": Config.CLIENT_ID,
        "client_secret": Config.CLIENT_SECRET,
        "refresh_token": refresh_token,
    }

    try:
        response = requests.post(token_url, data=payload)
        response.raise_for_status()
        token_data = response.json()

        logging.info("Successfully refreshed access token")

        # Create TokenData object, setting refresh_token only if it's in the response
        token_data_obj = TokenData(
            access_token=token_data["access_token"],
            refresh_token=token_data.get(
                "refresh_token", refresh_token
            ),  # Use old refresh_token if not provided
            instance_url=token_data["instance_url"],
            id=token_data["id"],
            token_type=token_data["token_type"],
            issued_at=token_data["issued_at"],
        )

        return ApiResponse(success=True, data=[token_data_obj])
    except requests.RequestException as e:
        logging.error(f"Failed to refresh access token: {str(e)}")
        if e.response is not None:
            logging.error(f"Response content: {e.response.content}")
        return ApiResponse(
            success=False,
            message=f"Failed to refresh access token: {str(e)}",
        )
