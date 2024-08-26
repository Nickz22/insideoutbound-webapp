import pytest, os, asyncio
from unittest.mock import patch
from app import create_app
from app.data_models import (
    TokenData,
    TableColumn,
    DataType,
    SettingsModel,
    FilterContainerModel,
    FilterModel,
)
from typing import List
from app.database.dml import save_session, delete_session, upsert_activations
from app.database.activation_selector import (
    load_active_activations_order_by_first_prospecting_activity_asc,
    load_inactive_activations,
)
from app.database.supabase_connection import get_supabase_admin_client
from app.tests.mocks import (
    mock_tasks_for_criteria_with_contains_content,
    mock_tasks_for_criteria_with_unique_values_content,
    get_thirty_mock_tasks_across_ten_contacts_for_contains_content_criteria_query,
    get_thirty_mock_tasks_across_ten_contacts_for_unique_values_content_criteria_query,
    get_ten_mock_contacts_spread_across_five_accounts,
    get_five_mock_accounts,
    get_mock_opportunity_for_account,
    add_mock_response,
    MOCK_ACCOUNT_IDS,
    response_based_on_query,
    mock_fetch_sobjects_async,
    clear_mocks,
    get_n_mock_contacts_for_account,
    get_mock_opportunity_for_account,
    get_mock_event_for_contact,
    get_two_mock_contacts_per_account,
    get_one_mock_task_per_contact_for_contains_content_criteria_query_x,
)

mock_user_id = "mock_user_id"

from datetime import datetime, timedelta
import json

pytest_plugins = ("pytest_asyncio",)


@pytest.mark.asyncio
class TestActivationLogic:
    @pytest.fixture(autouse=True)
    async def setup_method(self, request):
        # Set up app and client
        os.environ["FLASK_ENV"] = "testing"
        self.app = create_app()
        self.app.testing = True
        self.client = self.app.test_client()

        # Set up API header
        mock_token_data = TokenData(
            access_token="mock_access_token",
            refresh_token="mock_refresh_token",
            instance_url="https://mock_instance_url.com",
            id="mock_user_id",
            token_type="mock_token_type",
            issued_at="mock_issued_at",
        )

        # Use a context manager to ensure the app context is maintained
        with self.app.app_context():
            token = save_session(mock_token_data, True)
            self.api_header = {"X-Session-Token": token}
            
            # Run the onboarding flow
            self.do_onboarding_flow()

            # Setup mock responses
            self.setup_mock_user()

            yield  # This will run the test

            # Cleanup after the test
            delete_session(self.api_header["X-Session-Token"])
            supabase = get_supabase_admin_client()
            supabase.table("Activations").delete().in_(
                "activated_by_id", [mock_user_id]
            ).execute()
            self.app_context.pop()
            # clear any mock api responses setup by last test
            clear_mocks()

    @staticmethod
    def setup_mock_user():
        add_mock_response("fetch_logged_in_salesforce_user", {"Id": mock_user_id})

    @pytest.mark.asyncio
    @patch(
        "app.salesforce_api._fetch_sobjects_async",
        side_effect=mock_fetch_sobjects_async,
    )
    @patch("requests.get", side_effect=response_based_on_query)
    async def test_should_set_activations_without_prospecting_activities_past_inactivity_threshold_as_unresponsive(
        self, mock_sobject_fetch, async_mock_sobject_fetch
    ):
        with self.app.app_context():
            self.setup_thirty_tasks_across_ten_contacts_and_five_accounts()
            response = await asyncio.to_thread(self.client.post, "/fetch_prospecting_activity", headers=self.api_header)
            initial_activations = self.assert_and_return_payload(response)

            assert len(initial_activations) == 5

            # Set the last_prospecting_activity of the first activation to 11 days ago
            activation_to_inactivate = (
                load_active_activations_order_by_first_prospecting_activity_asc()
            ).data[0]
            activation_to_inactivate.last_prospecting_activity = (
                datetime.now() - timedelta(days=11)
            ).strftime("%Y-%m-%dT%H:%M:%S.000+0000")

            upsert_activations([activation_to_inactivate])

            self.setup_zero_new_prospecting_activities_and_zero_new_opportunities_and_zero_new_events()

            response = await asyncio.to_thread(
                self.client.post, "/fetch_prospecting_activity", headers=self.api_header
            )
            self.assert_and_return_payload(response)

            unresponsive_activations = load_inactive_activations().data
            assert len(unresponsive_activations) == 1
            assert unresponsive_activations[0].id == activation_to_inactivate.id

    @pytest.mark.asyncio
    @patch(
        "app.salesforce_api._fetch_sobjects_async",
        side_effect=mock_fetch_sobjects_async,
    )
    @patch("requests.get", side_effect=response_based_on_query)
    async def test_should_create_new_activation_when_one_activity_per_contact_and_one_meeting_or_one_opportunity_is_in_salesforce(
        self, mock_sobject_fetch, async_mock_sobject_fetch
    ):
        with self.app.app_context():
            self.setup_one_activity_per_contact_with_staggered_created_dates_and_one_event_under_a_single_account_and_one_opportunity_for_a_different_account()

            activations = await self.assert_and_return_payload_async(
                asyncio.to_thread(self.client.post, "/fetch_prospecting_activity", headers=self.api_header)
            )
            assert len(activations) == 2

            meeting_set_activation = next(a for a in activations if a["status"] == "Meeting Set")
            opportunity_created_activation = next(a for a in activations if a["status"] == "Opportunity Created")

            assert len(meeting_set_activation["event_ids"]) == 1
            assert opportunity_created_activation["opportunity"]["amount"] == 1733.42

            self._validate_prospecting_metadata(meeting_set_activation)
            self._validate_prospecting_metadata(opportunity_created_activation)

            self._validate_prospecting_effort(meeting_set_activation, expected_efforts=2)
            self._validate_prospecting_effort(opportunity_created_activation, expected_efforts=3)

    def _validate_prospecting_metadata(self, activation):
        metadata = activation["prospecting_metadata"]
        assert len(metadata) == 1
        assert metadata[0]["name"] == "Contains Content"
        assert metadata[0]["total"] == 2

        first_date = datetime.strptime(metadata[0]["first_occurrence"], "%Y-%m-%d")
        last_date = datetime.strptime(metadata[0]["last_occurrence"], "%Y-%m-%d")
        assert (last_date - first_date).days == 1

    def _validate_prospecting_effort(self, activation, expected_efforts):
        efforts = activation["prospecting_effort"]
        assert len(efforts) == expected_efforts

        effort_by_status = {e["status"]: e for e in efforts}

        if "Activated" in effort_by_status:
            assert len(effort_by_status["Activated"]["task_ids"]) == 0

        if "Engaged" in effort_by_status:
            assert len(effort_by_status["Engaged"]["task_ids"]) > 0

        if "Opportunity Created" in effort_by_status:
            assert len(effort_by_status["Opportunity Created"]["task_ids"]) > 0

    @staticmethod
    def assert_and_return_payload(response):
        assert response.status_code == 200
        data = response.get_json()  # Remove the 'await' here, dumbass!
        return data["data"][0]["raw_data"]

    async def assert_and_return_payload_async(self, response_future):
        response = await response_future
        assert response.status_code == 200
        data = response.get_json()
        return data["data"][0]["raw_data"]

    def do_onboarding_flow(self):
        """
        constructs a settings model and saves it via the save_settings API
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
            self.get_filter_container_via_tasks_from_generate_filters_api(
                mock_tasks_for_criteria_with_contains_content,
                columns,
            )
        )
        contains_content_filter_model.name = "Contains Content"
        contains_content_filter_model.direction = "inbound"

        unique_values_content_filter_model = (
            self.get_filter_container_via_tasks_from_generate_filters_api(
                mock_tasks_for_criteria_with_unique_values_content,
                columns,
            )
        )
        unique_values_content_filter_model.name = "Unique Content"
        unique_values_content_filter_model.direction = "outbound"

        assert unique_values_content_filter_model.filterLogic == "", "Filter logic should be an empty string, Morty!"

        # set non-null filters for contains_content_filter_model
        unique_values_content_filter_model.filterLogic = "((1 OR 2) AND 3)"
        unique_values_content_filter_model.filters = [
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
        ]

        prospecting_activity_criteria = [
            contains_content_filter_model,
            unique_values_content_filter_model,
        ]

        post_data = SettingsModel(
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
        ).to_dict()

        response = self.client.post(
            "/save_settings",
            data=json.dumps(post_data),
            content_type="application/json",
            headers=self.api_header,
        )

        # assert response status code is 200
        assert response.status_code == 200, response.data

    def setup_thirty_tasks_across_ten_contacts_and_five_accounts(self):
        add_mock_response(
            "contains_content_criteria_query",
            get_thirty_mock_tasks_across_ten_contacts_for_contains_content_criteria_query(
                mock_user_id
            ),
        )
        add_mock_response(
            "unique_values_content_criteria_query",
            get_thirty_mock_tasks_across_ten_contacts_for_unique_values_content_criteria_query(
                mock_user_id
            ),
        )
        add_mock_response(
            "fetch_accounts_not_in_ids",
            get_five_mock_accounts(),
        )
        add_mock_response(
            "fetch_contacts_by_ids_and_non_null_accounts",
            get_ten_mock_contacts_spread_across_five_accounts(),
        )
        add_mock_response(
            "fetch_opportunities_by_account_ids_from_date",
            [get_mock_opportunity_for_account(MOCK_ACCOUNT_IDS[0])],
        )
        add_mock_response("fetch_events_by_account_ids_from_date", [])
        add_mock_response(
            "fetch_contacts_by_account_ids",
            get_ten_mock_contacts_spread_across_five_accounts(),
        )
        add_mock_response(
            "fetch_contacts_by_account_ids",
            get_ten_mock_contacts_spread_across_five_accounts(),
        )

    def setup_zero_new_prospecting_activities_and_zero_new_opportunities_and_zero_new_events(
        self,
    ):
        add_mock_response("fetch_contacts_by_account_ids", [])
        add_mock_response("fetch_opportunities_by_account_ids_from_date", [])
        add_mock_response("fetch_events_by_account_ids_from_date", [])
        add_mock_response("fetch_accounts_not_in_ids", [])
        add_mock_response("fetch_contacts_by_account_ids", [])
        add_mock_response("fetch_contacts_by_account_ids", [])

    def setup_one_activity_per_contact_with_staggered_created_dates_and_one_event_under_a_single_account_and_one_opportunity_for_a_different_account(
        self,
    ):

        mock_accounts = get_five_mock_accounts()
        for account in mock_accounts:
            account["OwnerId"] = mock_user_id

        ## This Opportunity must be created before the mock tasks are created
        mock_opportunity = get_mock_opportunity_for_account(mock_accounts[0]["Id"])
        mock_opportunity["OwnerId"] = mock_user_id
        mock_contacts = get_two_mock_contacts_per_account(mock_accounts)
        for contact in mock_contacts:
            contact["OwnerId"] = mock_user_id
        mock_event = get_mock_event_for_contact(mock_contacts[3]["Id"])
        mock_event["OwnerId"] = mock_user_id
        mock_tasks = (
            get_one_mock_task_per_contact_for_contains_content_criteria_query_x(
                mock_contacts
            )
        )
        for task in mock_tasks:
            task["OwnerId"] = mock_user_id

        # Create a mapping from contact IDs to account IDs
        contact_to_account_id = {
            contact["Id"]: contact["AccountId"] for contact in mock_contacts
        }

        # Group tasks by account ID via the tasks' "WhoId" column
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

        # Set dates for tasks under the account related to the event
        if event_related_account_id in tasks_by_account_id:
            tasks = tasks_by_account_id[event_related_account_id]
            if len(tasks) >= 2:
                tasks[0]["CreatedDate"] = (today - timedelta(days=3)).strftime(
                    "%Y-%m-%dT%H:%M:%S.000+0000"
                )
                tasks[1]["CreatedDate"] = (today - timedelta(days=2)).strftime(
                    "%Y-%m-%dT%H:%M:%S.000+0000"
                )

        # Set dates for tasks under the account related to the opportunity
        if opportunity_related_account_id in tasks_by_account_id:
            tasks = tasks_by_account_id[opportunity_related_account_id]
            if len(tasks) >= 2:
                tasks[0]["CreatedDate"] = (today - timedelta(days=1)).strftime(
                    "%Y-%m-%dT%H:%M:%S.000+0000"
                )
                tasks[1]["CreatedDate"] = today.strftime("%Y-%m-%dT%H:%M:%S.000+0000")

        mock_tasks = [task for tasks in tasks_by_account_id.values() for task in tasks]

        add_mock_response(
            "contains_content_criteria_query",
            mock_tasks,
        )
        add_mock_response("unique_values_content_criteria_query", [])

        add_mock_response(
            "fetch_contacts_by_ids_and_non_null_accounts",
            mock_contacts,
        )

        add_mock_response("fetch_accounts_not_in_ids", mock_accounts)

        add_mock_response(
            "fetch_opportunities_by_account_ids_from_date",
            [mock_opportunity],
        )

        add_mock_response(
            "fetch_events_by_account_ids_from_date",
            [mock_event],
        )
        add_mock_response(
            "fetch_contacts_by_account_ids",
            mock_contacts,
        )
        add_mock_response(
            "fetch_contacts_by_account_ids",
            mock_contacts,
        )


    def get_filter_container_via_tasks_from_generate_filters_api(
        self, tasks, columns
    ) -> FilterContainerModel:
        """
        Hits the `/generate_filters` endpoint with the given tasks and returns the FilterContainerModel
        """
        response = self.client.post(
            "/generate_filters",
            data=json.dumps({"tasksOrEvents": tasks, "selectedColumns": columns}),
            content_type="application/json",
            headers=self.api_header,
        )
        response_json = json.loads(response.data.decode())["data"][0]
        response_json["filters"] = [
            FilterModel(**filter) for filter in response_json["filters"]
        ]

        return FilterContainerModel(**response_json)