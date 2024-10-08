import json, random
from datetime import datetime, timedelta
from app.data_models import (
    SettingsModel,
    FilterContainerModel,
    FilterModel,
    TableColumn,
    DataType,
)
from app.tests.mocks import (
    mock_tasks_for_criteria_with_contains_content,
    set_mock_contacts_for_map,
    get_five_mock_accounts,
    get_n_mock_contacts_for_account,
    get_mock_opportunity_for_account,
    get_mock_event_for_contact,
    get_two_mock_contacts_per_account,
    add_mock_response,
    get_n_mock_tasks_for_contacts_for_unique_values_content_criteria_query,
)
from app.mapper.mapper import convert_settings_model_to_settings
import json
from typing import List
from app.data_models import TokenData
def get_mock_token_data() -> TokenData:
    return TokenData(
        access_token="mock_access_token",
        refresh_token="mock_refresh_token",
        instance_url="https://mock_instance_url.com",
        id="https://mock_instance_url.com/mock_org_id/mock_user_id",
        token_type="mock_token_type",
        issued_at="mock_issued_at",
    )

def do_onboarding_flow(client, api_header):
    """
    Constructs a settings model and saves it via the save_settings API
    """
    columns: List[TableColumn] = [
        {
            "id": "Status",
            "dataType": DataType.STRING,
            "label": "Status",
        },
        {
            "id": "Subject",
            "dataType": DataType.STRING,
            "label": "Subject",
        },
    ]

    contains_content_filter_model = (
        get_filter_container_via_tasks_from_generate_filters_api(
            client,
            api_header,
            mock_tasks_for_criteria_with_contains_content,
            columns,
        )
    )
    contains_content_filter_model.name = "Contains Content"
    contains_content_filter_model.direction = "inbound"

    unique_values_content_filter_model = FilterContainerModel(
        name="Unique Content",
        direction="outbound",
        filterLogic="((1 OR 2) AND 3)",
        filters=[
            FilterModel(
                field="Status",
                dataType="string",
                operator="contains",
                value="Unique",
            ),
            FilterModel(
                field="Status",
                dataType="string",
                operator="contains",
                value="Other",
            ),
            FilterModel(
                field="Subject",
                dataType="string",
                operator="contains",
                value="Unique Subject",
            ),
        ],
    )

    unique_values_content_filter_model.direction = "outbound"

    prospecting_activity_criteria = [
        contains_content_filter_model,
        unique_values_content_filter_model,
    ]

    settings_model = SettingsModel(
        activateByMeeting=True,
        activateByOpportunity=True,
        activitiesPerContact=3,
        contactsPerAccount=2,
        criteria=prospecting_activity_criteria,
        inactivityThreshold=10,
        meetingObject="Event",
        meetingsCriteria=FilterContainerModel(
            name="Meetings",
            filters=[
                FilterModel(
                    field="Subject",
                    dataType="string",
                    operator="contains",
                    value="Meeting",
                )
            ],
            filterLogic="1",
        ),
        trackingPeriod=5,
    )

    response = client.post(
        "/save_settings",
        data=json.dumps(settings_model.to_dict()),
        content_type="application/json",
        headers=api_header,
    )

    # assert response status code is 200
    assert response.status_code == 200, response.data
    return convert_settings_model_to_settings(settings_model)


def get_filter_container_via_tasks_from_generate_filters_api(
    client, api_header, tasks, columns
) -> FilterContainerModel:
    """
    Hits the `/generate_filters` endpoint with the given tasks and returns the FilterContainerModel
    """
    response = client.post(
        "/generate_filters",
        data=json.dumps({"tasksOrEvents": tasks, "selectedColumns": columns}),
        content_type="application/json",
        headers=api_header,
    )
    response_json = json.loads(response.data.decode())["data"][0]
    response_json["filters"] = [
        FilterModel(**filter) for filter in response_json["filters"]
    ]

    return FilterContainerModel(**response_json)


def setup_thirty_tasks_across_ten_contacts_and_five_accounts_for_start_of_test(
    mock_user_id,
):
    mock_accounts = get_five_mock_accounts()
    mock_contacts = [
        contact
        for account in mock_accounts
        for contact in get_n_mock_contacts_for_account(2, account["Id"])
    ]
    for contact in mock_contacts:
        contact.id = f"mock_contact_id_{random.randint(1000, 9999)}"

    mock_tasks = get_n_mock_tasks_for_contacts_for_unique_values_content_criteria_query(
        3, mock_contacts, mock_user_id
    )

    set_mock_contacts_for_map(mock_contacts)
    add_mock_response(
        "fetch_all_matching_tasks", mock_tasks
    )  # compute new activations flow
    add_mock_response(
        "fetch_events_by_contact_ids_from_date", []
    )  # increment existing activations flow
    add_mock_response(
        "fetch_events_by_contact_ids_from_date", []
    )  # compute new activations flow

    # increment existing activations flow
    add_mock_response(
        "fetch_opportunities_by_account_ids_from_date",
        [get_mock_opportunity_for_account(mock_accounts[0]["Id"])],
    )
    # compute new activations flow
    add_mock_response(
        "fetch_opportunities_by_account_ids_from_date",
        [get_mock_opportunity_for_account(mock_accounts[0]["Id"])],
    )
    add_mock_response(
        "fetch_salesforce_users",
        [{"Id": mock_user_id, "FirstName": "Mock", "LastName": "User"}],
    )


def setup_zero_new_prospecting_activities_and_zero_new_opportunities_and_zero_new_events(
    mock_user_id,
):
    set_mock_contacts_for_map([])
    add_mock_response("fetch_all_matching_tasks", [])  # unresponsive flow
    add_mock_response(
        "fetch_all_matching_tasks", []
    )  # increment existing activations flow
    add_mock_response("fetch_all_matching_tasks", [])  # compute new activations flow
    add_mock_response(
        "fetch_events_by_contact_ids_from_date", []
    )  # increment existing activations flow
    add_mock_response(
        "fetch_events_by_contact_ids_from_date", []
    )  # compute new activations flow
    add_mock_response(
        "fetch_opportunities_by_account_ids_from_date", []
    )  # increment existing activations flow
    add_mock_response(
        "fetch_opportunities_by_account_ids_from_date", []
    )  # compute new activations flow
    add_mock_response(
        "fetch_salesforce_users",
        [{"Id": mock_user_id, "FirstName": "Mock", "LastName": "User"}],
    )


def validate_prospecting_metadata(activation):
    metadata = activation["prospecting_metadata"]
    assert len(metadata) == 1
    assert (
        metadata[0]["name"] == "Contains Content"
        or metadata[0]["name"] == "Unique Content"
    )
    assert metadata[0]["total"] == 2

    first_date = datetime.strptime(metadata[0]["first_occurrence"], "%Y-%m-%d")
    last_date = datetime.strptime(metadata[0]["last_occurrence"], "%Y-%m-%d")
    assert (last_date - first_date).days == 1


def validate_prospecting_effort(
    activation,
    expected_efforts,
    expected_activated_effort=0,
    expected_engaged_effort=0,
    expected_opportunity_created_effort=0,
):
    efforts = activation["prospecting_effort"]
    assert len(efforts) == expected_efforts

    effort_by_status = {e["status"]: e for e in efforts}

    if "Activated" in effort_by_status:
        assert (
            len(effort_by_status["Activated"]["task_ids"]) == expected_activated_effort
        )

    if "Engaged" in effort_by_status:
        assert len(effort_by_status["Engaged"]["task_ids"]) == expected_engaged_effort

    if "Opportunity Created" in effort_by_status:
        assert (
            len(effort_by_status["Opportunity Created"]["task_ids"])
            == expected_opportunity_created_effort
        )


def assert_and_return_payload(response):
    assert (
        response.status_code == 200
    ), f"Unexpected status code: {response.status_code}, Response data: {response.data}"
    data = response.get_json()
    return data["data"][0]["raw_data"]


async def assert_and_return_payload_async(response_future):
    response = await response_future
    response_data = response.data.decode("utf-8")
    response_json = json.loads(response_data)
    assert (
        response.status_code == 200
    ), f"Unexpected status code: {response.status_code}, Response message: {response_json.get('message', 'No message')}"
    data = response.get_json()
    return data["data"][0]["raw_data"]


def get_salesforce_compatible_datetime_now():
    now = datetime.now()
    return now.strftime("%Y-%m-%dT%H:%M:%S.000+0000")


def get_salesforce_compatible_datetime_days_from_now(days_in_future: int):
    now = datetime.now()
    return (now + timedelta(days=days_in_future)).strftime("%Y-%m-%dT%H:%M:%S.000+0000")


def get_salesforce_compatible_datetime_hours_from_now(hours_in_future: int):
    now = datetime.now()
    return (now + timedelta(hours=hours_in_future)).strftime(
        "%Y-%m-%dT%H:%M:%S.000+0000"
    )


def setup_one_activity_per_contact_with_staggered_created_dates_and_one_event_under_a_single_account_and_one_opportunity_for_a_different_account(
    mock_user_id
):
    mock_accounts = get_five_mock_accounts()
    for account in mock_accounts:
        account["OwnerId"] = mock_user_id

    ## This Opportunity must be created before the mock tasks are created so that
    ### the prospecting effort will be split among "Activated" and "Opportunity Created" statuses
    mock_opportunity = get_mock_opportunity_for_account(mock_accounts[0]["Id"])
    mock_opportunity["OwnerId"] = mock_user_id
    mock_contacts = get_two_mock_contacts_per_account(mock_accounts)
    for contact in mock_contacts:
        contact.owner_id = mock_user_id
    mock_event = get_mock_event_for_contact(mock_contacts[3].id)
    mock_event["OwnerId"] = mock_user_id
    mock_tasks = get_n_mock_tasks_for_contacts_for_unique_values_content_criteria_query(
        1, mock_contacts, mock_user_id
    )
    for task in mock_tasks:
        task["OwnerId"] = mock_user_id

    # Create a mapping from contact IDs to account IDs
    contact_to_account_id = {
        contact.id: contact.account_id for contact in mock_contacts
    }

    # Group tasks by account ID via the "WhoId" column
    tasks_by_account_id = {}
    for task in mock_tasks:
        contact_id = task["WhoId"]
        account_id = contact_to_account_id.get(contact_id)
        if account_id:
            if account_id not in tasks_by_account_id:
                tasks_by_account_id[account_id] = []
            tasks_by_account_id[account_id].append(task)

    # Identify the account related to the event and the account related to the opportunity
    event_related_account_id = contact_to_account_id[mock_event["WhoId"]]
    opportunity_related_account_id = mock_opportunity["AccountId"]

    # Setting CreatedDate on Tasks
    today = datetime.now()

    # Set past dates for tasks under the account related to the event
    if event_related_account_id in tasks_by_account_id:
        tasks = tasks_by_account_id[event_related_account_id]
        if len(tasks) >= 2:
            tasks[0]["CreatedDate"] = (today - timedelta(days=3)).strftime(
                "%Y-%m-%dT%H:%M:%S.000+0000"
            )
            tasks[1]["CreatedDate"] = (today - timedelta(days=2)).strftime(
                "%Y-%m-%dT%H:%M:%S.000+0000"
            )

    # Set past dates for tasks under the account related to the opportunity
    if opportunity_related_account_id in tasks_by_account_id:
        tasks = tasks_by_account_id[opportunity_related_account_id]
        if len(tasks) >= 2:
            tasks[0]["CreatedDate"] = (today - timedelta(days=1)).strftime(
                "%Y-%m-%dT%H:%M:%S.000+0000"
            )
            tasks[1]["CreatedDate"] = today.strftime("%Y-%m-%dT%H:%M:%S.000+0000")

    set_mock_contacts_for_map(mock_contacts)
    mock_tasks = [task for tasks in tasks_by_account_id.values() for task in tasks]
    add_mock_response("fetch_all_matching_tasks", mock_tasks)
    set_mock_contacts_for_map(mock_contacts)
    add_mock_response("fetch_events_by_contact_ids_from_date", [mock_event])
    add_mock_response(
        "fetch_opportunities_by_account_ids_from_date",
        [mock_opportunity],
    )
    add_mock_response(
        "fetch_salesforce_users",
        [{"Id": mock_user_id, "FirstName": "Mock", "LastName": "User"}],
    )
    add_mock_response(
        "fetch_salesforce_users",
        [{"Id": mock_user_id, "FirstName": "Mock", "LastName": "User"}],
    )
    
def setup_one_activity_per_contact_with_staggered_created_dates_and_one_task_meeting_under_a_single_account_and_one_opportunity_for_a_different_account(
    mock_user_id, settings: SettingsModel
):
    mock_accounts = get_five_mock_accounts()
    for account in mock_accounts:
        account["OwnerId"] = mock_user_id

    ## This Opportunity must be created before the mock tasks are created so that
    ### the prospecting effort will be split among "Activated" and "Opportunity Created" statuses
    mock_opportunity = get_mock_opportunity_for_account(mock_accounts[0]["Id"])
    mock_opportunity["OwnerId"] = mock_user_id
    mock_contacts = get_two_mock_contacts_per_account(mock_accounts)
    for contact in mock_contacts:
        contact.owner_id = mock_user_id
    
    mock_task_meeting = {
        "Id": "00T" + str(random.randint(1000, 9999)),
        "Subject": "Meeting",
        "WhoId": mock_contacts[3].id,
        "AccountId": mock_accounts[0]["Id"],
        "ActivityDate": datetime.now().strftime("%Y-%m-%d"),
        "OwnerId": mock_user_id,
        "CreatedDate" : datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000+0000")
    }
    
    mock_task_meeting["OwnerId"] = mock_user_id
    mock_tasks = get_n_mock_tasks_for_contacts_for_unique_values_content_criteria_query(
        1, mock_contacts, mock_user_id
    )
    for task in mock_tasks:
        task["OwnerId"] = mock_user_id

    # Create a mapping from contact IDs to account IDs
    contact_to_account_id = {
        contact.id: contact.account_id for contact in mock_contacts
    }

    # Group tasks by account ID via the "WhoId" column
    tasks_by_account_id = {}
    for task in mock_tasks:
        contact_id = task["WhoId"]
        account_id = contact_to_account_id.get(contact_id)
        if account_id:
            if account_id not in tasks_by_account_id:
                tasks_by_account_id[account_id] = []
            tasks_by_account_id[account_id].append(task)

    # Identify the account related to the event and the account related to the opportunity
    event_related_account_id = contact_to_account_id[mock_task_meeting["WhoId"]]
    opportunity_related_account_id = mock_opportunity["AccountId"]

    # Setting CreatedDate on Tasks
    today = datetime.now()

    # Set past dates for tasks under the account related to the event
    if event_related_account_id in tasks_by_account_id:
        tasks = tasks_by_account_id[event_related_account_id]
        if len(tasks) >= 2:
            tasks[0]["CreatedDate"] = (today - timedelta(days=3)).strftime(
                "%Y-%m-%dT%H:%M:%S.000+0000"
            )
            tasks[1]["CreatedDate"] = (today - timedelta(days=2)).strftime(
                "%Y-%m-%dT%H:%M:%S.000+0000"
            )

    # Set past dates for tasks under the account related to the opportunity
    if opportunity_related_account_id in tasks_by_account_id:
        tasks = tasks_by_account_id[opportunity_related_account_id]
        if len(tasks) >= 2:
            tasks[0]["CreatedDate"] = (today - timedelta(days=1)).strftime(
                "%Y-%m-%dT%H:%M:%S.000+0000"
            )
            tasks[1]["CreatedDate"] = today.strftime("%Y-%m-%dT%H:%M:%S.000+0000")

    set_mock_contacts_for_map(mock_contacts)
    mock_tasks = [task for tasks in tasks_by_account_id.values() for task in tasks]
    add_mock_response("fetch_all_matching_tasks", mock_tasks + [mock_task_meeting])
    set_mock_contacts_for_map(mock_contacts)
    add_mock_response(
        "fetch_opportunities_by_account_ids_from_date",
        [mock_opportunity],
    )
    add_mock_response(
        "fetch_salesforce_users",
        [{"Id": mock_user_id, "FirstName": "Mock", "LastName": "User"}],
    )


def setup_six_tasks_across_two_contacts_and_one_account(account_id, mock_user_id):
    mock_contacts = get_n_mock_contacts_for_account(2, account_id)
    mock_tasks = get_n_mock_tasks_for_contacts_for_unique_values_content_criteria_query(
        3, mock_contacts, mock_user_id
    )

    for task in mock_tasks:
        task["Id"] = str(random.randint(1000, 9999))

    set_mock_contacts_for_map(mock_contacts)
    add_mock_response("fetch_all_matching_tasks", mock_tasks)  # unresponsive flow
    add_mock_response(
        "fetch_all_matching_tasks", mock_tasks
    )  # compute new activations flow
    add_mock_response(
        "fetch_events_by_contact_ids_from_date", []
    )  # increment existing activations flow
    add_mock_response(
        "fetch_events_by_contact_ids_from_date", []
    )  # compute new activations flow
    add_mock_response(
        "fetch_opportunities_by_account_ids_from_date", []
    )  # increment existing activations flow
    add_mock_response(
        "fetch_opportunities_by_account_ids_from_date", []
    )  # compute new activations flow
    add_mock_response(
        "fetch_salesforce_users",
        [{"Id": mock_user_id, "FirstName": "Mock", "LastName": "User"}],
    )
