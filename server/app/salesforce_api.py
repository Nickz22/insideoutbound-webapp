import requests
from typing import List, Dict
from app.utils import pluck, format_error_message
from app.data_models import (
    ApiResponse,
    Contact,
    Account,
    CriteriaField,
    FilterContainer,
    SObjectFieldModel,
    UserModel,
    UserSObject,
)
from app.database.supabase_connection import get_session_state
from app.constants import SESSION_EXPIRED, FILTER_OPERATOR_MAPPING


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


def fetch_accounts_not_in_ids(account_ids):
    """
    Fetches all Accounts from Salesforce and loops through them to find those which are not in `account_ids`

    Parameters:
    - account_ids (list[str]): A list of account IDs to exclude from the fetched accounts.

    Returns:
    - ApiResponse: An ApiResponse object containing the fetched accounts as a list of Account objects.

    Throws:
    - Exception: Raises an exception with a formatted error message if any error occurs during the fetch operation.
    """
    api_response = ApiResponse(data=[], message="", success=False)

    try:
        soql_query = "SELECT Id,Name FROM Account"

        response = _fetch_sobjects(soql_query, get_credentials())
        accounts = [
            Account(id=account.get("Id"), name=account.get("Name"))
            for account in response.data
            if account.get("Id") not in account_ids
        ]

        api_response.data = accounts
        api_response.success = True
        api_response.message = "Accounts fetched successfully."
    except Exception as e:
        raise Exception(format_error_message(e))

    return api_response


def fetch_criteria_tasks_by_account_ids_from_date(
    account_ids: list[str],
    start: str,
    criteria: list[FilterContainer],
    salesforce_user_ids: list[str],
):
    """
    Takes response from fetch_tasks_by_account_ids_from_date_not_in_ids and organizes the tasks by criteria name.

    Parameters:
    - account_ids (list[str]): A list of account IDs to fetch tasks for.
    - start (str): The start date to fetch tasks from.
    - criteria (list[FilterContainer]): A list of FilterContainer objects.

    Returns:
    - ApiResponse: An ApiResponse object containing the fetched tasks organized by criteria name.
    """
    api_response = ApiResponse(data=[], message="", success=False)

    try:
        tasks_by_criteria_by_account_id = (
            fetch_tasks_by_account_ids_from_date_not_in_ids(
                account_ids, start, criteria, [], salesforce_user_ids
            ).data
        )
        tasks_by_criteria = {}

        for (
            account_id,
            tasks_by_criteria_name,
        ) in tasks_by_criteria_by_account_id.items():
            for criteria_name, tasks in tasks_by_criteria_name.items():
                if criteria_name not in tasks_by_criteria:
                    tasks_by_criteria[criteria_name] = []
                tasks_by_criteria[criteria_name].extend(tasks)

        api_response.data = tasks_by_criteria
        api_response.success = True
    except Exception as e:
        raise Exception(format_error_message(e))

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
        soql_query = "SELECT Id,Email,FirstName,LastName,Username,FullPhotoUrl,UserRole.Name FROM User WHERE IsActive = true"

        if ids:
            soql_query += f" AND Id IN ('{','.join(ids)}')"

        response = _fetch_sobjects(soql_query, get_credentials())
        for entry in response.data:

            entry["Role"] = (
                entry["UserRole"]["Name"] if entry.get("UserRole") is not None else None
            )
            del entry["UserRole"]
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


def fetch_tasks_by_account_ids_from_date_not_in_ids(
    account_ids: list[str],
    start: str,
    criteria: list[FilterContainer],
    already_counted_task_ids: list[str],
    salesforce_user_ids: list[str],
) -> ApiResponse:
    """
    Fetches tasks from Salesforce based on a list of account IDs, starting from a specific date,
    organized by criteria names for tasks related to contacts belonging to the specified accounts.
    This version batches queries by contact IDs to handle large datasets.

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
        contacts = fetch_contacts_by_account_ids(account_ids)
        contact_by_id = {contact.id: contact for contact in contacts.data}
        contact_ids = list(pluck(contacts.data, "id"))

        batch_size = 150
        tasks_by_criteria_name = {}  # To accumulate tasks across batches

        # Process in batches
        for i in range(0, len(contact_ids), batch_size):
            batch_contact_ids = contact_ids[i : i + batch_size]
            additional_filter = "WhoId IN ({})".format(
                ", ".join(map(lambda id: f"'{id}'", batch_contact_ids))
            )

            # Fetch tasks by criteria for the current batch
            batch_tasks = fetch_contact_tasks_by_criteria_from_date(
                criteria, start, additional_filter, salesforce_user_ids
            )

            # Merge batch_tasks into tasks_by_criteria_name
            for criteria_name, tasks in batch_tasks.data.items():
                if criteria_name not in tasks_by_criteria_name:
                    tasks_by_criteria_name[criteria_name] = []
                tasks_by_criteria_name[criteria_name].extend(tasks)

        # Organize tasks_by_criteria_name by account and criteria
        criteria_group_tasks_by_account_id = {
            account_id: {} for account_id in account_ids
        }

        for criteria_name, tasks in tasks_by_criteria_name.items():
            for task in tasks:
                if task.get("Id") in already_counted_task_ids:
                    continue
                contact = contact_by_id.get(task.get("WhoId"))
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
        api_response.message = "Tasks fetched and organized successfully."
    except Exception as e:
        raise Exception(format_error_message(e))

    return api_response


def fetch_tasks_by_user_ids(user_ids):
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


def fetch_contact_tasks_by_criteria_from_date(
    criteria, from_datetime, additional_filter=None, salesforce_user_ids: List[str] = []
) -> Dict[str, List[Dict]]:
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
    joined_user_ids = "','".join(salesforce_user_ids)
    soql_query = f"SELECT Id, WhoId, OwnerId, WhatId, Subject, Status, CreatedDate, CreatedById FROM Task WHERE CreatedDate >= {from_datetime} AND OwnerId IN ('{joined_user_ids}') AND "
    if additional_filter:
        soql_query += f"{additional_filter} AND "
    tasks_by_filter_name = {}

    try:
        for filter_container in criteria:
            combined_conditions = _construct_where_clause_from_filter(filter_container)

            contact_task_models = []
            print("fetching tasks for filter", filter_container.name)
            for task in _fetch_sobjects(
                f"{soql_query} {combined_conditions} ORDER BY CreatedDate ASC",
                get_credentials(),
            ).data:
                if not task.get("WhoId", "") or task.get(
                    "WhoId", ""
                ).upper().startswith("00Q"):
                    continue
                contact_task_models.append(task)

            tasks_by_filter_name[filter_container.name] = contact_task_models

        api_response.data = tasks_by_filter_name
        api_response.success = True
    except Exception as e:
        raise Exception(format_error_message(e))

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


def fetch_events_by_user_ids(user_ids):
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
        api_response.data = [
            {key: value for key, value in entry.items() if key != "attributes"}
            for entry in _fetch_sobjects(soql_query, get_credentials()).data
        ]
        api_response.success = True
    except Exception as e:
        raise Exception(format_error_message(e))

    return api_response


def fetch_events_by_account_ids_from_date(
    account_ids,
    start,
    salesforce_user_ids: List[str],
    meetings_criteria: FilterContainer,
):
    """
    Fetches events from Salesforce based on a list of account IDs.

    Parameters:
    - account_ids (list[str]): A list of account IDs to fetch events for
    - start (str): The start date for filtering events via CreatedDate, in ISO format
    - salesforce_user_ids (list[str]): A list of Salesforce user IDs to filter events by

    Returns:
    - dict: A dictionary where each key is an account ID and each value is the list of events fetched from Salesforce
      for that account. The events are represented as dictionaries with keys corresponding to the fields selected in the SOQL query.

    Throws:
    - Exception: Raises an exception with a formatted error message if any error occurs during the fetch
    """
    api_response = ApiResponse(data={}, message="", success=True)
    batch_size = 150

    contacts = fetch_contacts_by_account_ids(account_ids)
    contact_by_id = {contact.id: contact for contact in contacts.data}
    contact_ids = list(contact_by_id.keys())

    events_by_account_id = {}

    try:
        meeting_criteria_filter = _construct_where_clause_from_filter(meetings_criteria)
        # Process the contact IDs in batches of 150
        for i in range(0, len(contact_ids), batch_size):
            batch_contact_ids = contact_ids[i : i + batch_size]
            joined_contact_ids = "','".join(batch_contact_ids)
            joined_user_ids = "','".join(salesforce_user_ids)

            soql_query = f"SELECT Id, WhoId, WhatId, Subject, CreatedDate, StartDateTime, EndDateTime FROM Event WHERE WhoId IN ('{joined_contact_ids}') AND CreatedDate >= {start} AND CreatedById IN ('{joined_user_ids}') AND ({meeting_criteria_filter}) ORDER BY StartDateTime ASC"

            response = _fetch_sobjects(soql_query, get_credentials())
            for event in response.data:
                account_id = contact_by_id.get(event.get("WhoId")).account_id
                if account_id not in events_by_account_id:
                    events_by_account_id[account_id] = []
                events_by_account_id[account_id].append(event)

        api_response.data = events_by_account_id
        api_response.message = "Events fetched successfully."
    except Exception as e:
        raise Exception(format_error_message(e))

    return api_response


def fetch_opportunities_by_account_ids_from_date(
    account_ids, start, salesforce_user_ids: List[str]
) -> List[Dict]:
    """
    Fetches opportunities from Salesforce based on a list of account IDs, querying in batches of 150.

    Parameters:
    - account_ids (list[str]): A list of account IDs to fetch opportunities for.
    - start (str): The start date for filtering opportunities, in ISO format.

    Returns:
    - ApiResponse: An ApiResponse object containing the fetched opportunities as a list of Opportunity objects.

    Throws:
    - Exception: Raises an exception with a formatted error message if any error occurs during the fetch operation.
    """
    api_response = ApiResponse(data=[], message="", success=True)
    batch_size = 150

    try:
        # Process the account IDs in batches of 150
        for i in range(0, len(account_ids), batch_size):
            batch_ids = account_ids[i : i + batch_size]
            joined_ids = ",".join([f"'{id}'" for id in batch_ids])
            joined_user_ids = "','".join(salesforce_user_ids)
            soql_query = f"SELECT Id, AccountId, Amount, CreatedDate, StageName, Name, CloseDate FROM Opportunity WHERE CreatedDate >= {start} AND AccountId IN ({joined_ids}) AND CreatedById IN ('{joined_user_ids}') ORDER BY CreatedDate ASC"

            response = _fetch_sobjects(soql_query, get_credentials())
            for opportunity in response.data:
                api_response.data.append(opportunity)

        api_response.success = True
        api_response.message = "Opportunities fetched successfully."
    except Exception as e:
        api_response.success = False
        api_response.message = format_error_message(e)
        raise Exception(api_response.message)

    return api_response


def fetch_contacts_by_account_ids(account_ids):
    """
    Fetches contacts from Salesforce based on a list of account IDs, querying in batches of 150.

    Parameters:
    - account_ids (list[str]): A list of account IDs to fetch contacts for.

    Returns:
    - ApiResponse: An ApiResponse object containing the fetched contacts as a list of Contact objects.

    Throws:
    - Exception: Raises an exception with a formatted error message if any error occurs during the fetch operation.
    """
    api_response = ApiResponse(data=[], message="", success=True)
    batch_size = 150
    contact_models = []

    try:
        # Process the account IDs in batches of 150
        for i in range(0, len(account_ids), batch_size):
            batch_ids = account_ids[i : i + batch_size]
            joined_ids = ",".join([f"'{id}'" for id in batch_ids])
            soql_query = f"SELECT Id, FirstName, LastName, AccountId, Account.Name FROM Contact WHERE AccountId IN ({joined_ids})"

            response = _fetch_sobjects(soql_query, get_credentials())
            for contact in response.data:
                contact_models.append(
                    Contact(
                        id=contact.get("Id"),
                        first_name=(
                            contact.get("FirstName")
                            if contact.get("FirstName") != None
                            else ""
                        ),
                        last_name=contact.get("LastName"),
                        account_id=contact.get("AccountId"),
                        account=Account(
                            id=contact.get("AccountId"),
                            name=contact.get("Account").get("Name"),
                        ),
                    )
                )

        api_response.data = contact_models
    except Exception as e:
        raise Exception(format_error_message(e))

    return api_response


def fetch_contacts_by_ids_and_non_null_accounts(contact_ids):
    """
    Fetches contacts by their IDs from Salesforce and returns them as Contact model instances.

    Parameters:
    - contact_ids (list of str): A list of contact ID strings to fetch from Salesforce.

    Returns:
    - ApiResponse: An ApiResponse object containing a list of Contact model instances if the fetch is successful,
      or an error message if not. The ApiResponse's `success` attribute indicates the operation's success.

    Raises:
    - Exception: If the access tokens are missing or expired, or if an error occurs during the API request or data processing.
    """
    api_response = ApiResponse(data=[], message="", success=True)
    batch_size = 150
    contact_models = []

    try:
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

        # Filter out fields whose 'type' contains 'date' or 'reference' and those in the blacklist
        filtered_account_fields = [
            field["name"]
            for field in account_fields
            if "date" not in field["type"].lower()
            and "reference" not in field["type"].lower()
            and field["name"].lower() not in blacklist
        ]

        account_fields_str = ", ".join(
            [f"Account.{field}" for field in filtered_account_fields]
        )
        # Process the contact IDs in batches of 150
        for i in range(0, len(contact_ids), batch_size):
            batch_ids = contact_ids[i : i + batch_size]
            joined_ids = ",".join([f"'{id}'" for id in batch_ids])

            soql_query = f"SELECT Id, FirstName, LastName, AccountId, {account_fields_str} FROM Contact WHERE Id IN ({joined_ids}) AND AccountId != null"

            for contact in _fetch_sobjects(soql_query, get_credentials()).data:
                contact_models.append(
                    Contact(
                        id=contact.get("Id"),
                        first_name=(
                            contact.get("FirstName")
                            if contact.get("FirstName") != None
                            else ""
                        ),
                        last_name=contact.get("LastName"),
                        account_id=contact.get("AccountId"),
                        account=Account(
                            id=contact.get("AccountId"),
                            name=contact.get("Account").get("Name"),
                            owner_id=contact.get("Account").get("OwnerId"),
                            **contact.get("Account"),
                        ),
                    )
                )

        api_response.data = contact_models
        api_response.message = "Contacts fetched successfully."
        api_response.success = True
    except Exception as e:
        raise Exception(format_error_message(e))

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
        if (
            isinstance(e, requests.exceptions.HTTPError)
            and e.response.status_code == 401
        ):
            api_response.message = SESSION_EXPIRED

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
