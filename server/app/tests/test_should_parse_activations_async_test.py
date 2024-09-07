import pytest, os, asyncio, random
from unittest.mock import patch
from app import create_app
from app.data_models import (
    Activation,
    TokenData,
    TableColumn,
    DataType,
    SettingsModel,
    FilterContainerModel,
    FilterModel,
    ProspectingEffort,
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
    get_mock_opportunity_for_account,
    get_one_mock_task_per_contact_for_unique_content_criteria_query_x,
    add_mock_response,
    get_three_mock_tasks_per_two_contacts_for_contains_content_criteria_query,
    get_n_mock_tasks_for_contacts_for_unique_values_content_criteria_query,
    get_n_mock_tasks_per_contact_for_contains_content_crieria_query,
)

mock_user_id = "mock_user_id"

from datetime import datetime, timedelta
import json

pytest_plugins = ("pytest_asyncio",)

from flask import has_app_context
import logging
from contextlib import contextmanager

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


@contextmanager
def context_tracker(app):
    ctx = app.app_context()
    try:
        ctx.push()
        yield ctx
    except Exception as e:
        logger.exception(f"Exception in context_tracker: {e}")
        raise
    finally:
        try:
            ctx.pop()
        except Exception as e:
            logger.exception(f"Exception while popping context: {e}")


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

        with context_tracker(self.app):
            token = save_session(mock_token_data, True)
            self.api_header = {"X-Session-Token": token}

            # Run the onboarding flow
            self.do_onboarding_flow()

            # Setup mock responses
            self.setup_mock_user()

            try:
                yield
            finally:
                delete_session(self.api_header["X-Session-Token"])
                supabase = get_supabase_admin_client()
                supabase.table("Activations").delete().in_(
                    "activated_by_id", [mock_user_id]
                ).execute()

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
    async def test_should_create_activation_when_sufficient_outbound_prospecting_activities(
        self, mock_sobject_fetch, async_mock_sobject_fetch
    ):
        with self.app.app_context():
            # Setup mock data
            mock_account = get_five_mock_accounts()[0]
            mock_contacts = get_two_mock_contacts_per_account([mock_account])
            mock_tasks = (
                get_n_mock_tasks_for_contacts_for_unique_values_content_criteria_query(
                    3, mock_contacts, mock_user_id
                )
            )

            # Setup mock responses
            add_mock_response("fetch_accounts_not_in_ids", [mock_account])
            add_mock_response("fetch_contacts_by_account_ids", mock_contacts)
            add_mock_response("fetch_contacts_by_account_ids", mock_contacts)
            add_mock_response("unique_values_content_criteria_query", mock_tasks)
            add_mock_response("contains_content_criteria_query", [])
            add_mock_response("fetch_opportunities_by_account_ids_from_date", [])
            add_mock_response("fetch_events_by_account_ids_from_date", [])
            add_mock_response(
                "fetch_contacts_by_ids_and_non_null_accounts", mock_contacts
            )

            # Fetch prospecting activity
            response = await asyncio.to_thread(
                self.client.post, "/fetch_prospecting_activity", headers=self.api_header
            )
            activations = self.assert_and_return_payload(response)

            # Assertions
            assert len(activations) == 1, "Expected one activation to be created"
            activation = activations[0]
            assert (
                activation["status"] == "Activated"
            ), "Activation status should be 'Activated'"
            assert (
                activation["account"]["id"] == mock_account["Id"]
            ), "Activation should be for the correct account"
            assert (
                len(activation["active_contact_ids"]) == 2
            ), "Activation should have two active contacts"

            # Validate prospecting effort
            self._validate_prospecting_effort(
                activation,
                expected_efforts=1,
                expected_activated_effort=6,
                expected_engaged_effort=0,
                expected_opportunity_created_effort=0,
            )

            # Validate prospecting metadata
            metadata = activation["prospecting_metadata"]
            assert len(metadata) == 1, "Expected one metadata entry"
            assert (
                metadata[0]["name"] == "Unique Content"
            ), "Metadata should be for 'Unique Content'"
            assert (
                metadata[0]["total"] == 6
            ), "Expected 6 total activities (3 per contact)"

    @pytest.mark.asyncio
    @patch(
        "app.salesforce_api._fetch_sobjects_async",
        side_effect=mock_fetch_sobjects_async,
    )
    @patch("requests.get", side_effect=response_based_on_query)
    async def test_should_not_create_activation_with_insufficient_outbound_activities(
        self, mock_sobject_fetch, async_mock_sobject_fetch
    ):
        with self.app.app_context():
            # Setup mock data
            mock_account = get_five_mock_accounts()[0]
            mock_contacts = get_two_mock_contacts_per_account([mock_account])

            # Create 5 outbound and 1 inbound task
            outbound_tasks = get_n_mock_tasks_for_contacts_for_unique_values_content_criteria_query(
                3, mock_contacts[:1], mock_user_id
            ) + get_n_mock_tasks_for_contacts_for_unique_values_content_criteria_query(
                2, mock_contacts[1:], mock_user_id
            )
            inbound_task = (
                get_n_mock_tasks_per_contact_for_contains_content_crieria_query(
                    1, mock_contacts[1:], mock_user_id
                )
            )

            # Setup mock responses
            add_mock_response("fetch_accounts_not_in_ids", [mock_account])
            add_mock_response("fetch_contacts_by_account_ids", mock_contacts)
            add_mock_response("fetch_contacts_by_account_ids", mock_contacts)
            add_mock_response("unique_values_content_criteria_query", outbound_tasks)
            add_mock_response("contains_content_criteria_query", inbound_task)
            add_mock_response("fetch_opportunities_by_account_ids_from_date", [])
            add_mock_response("fetch_events_by_account_ids_from_date", [])
            add_mock_response(
                "fetch_contacts_by_ids_and_non_null_accounts", mock_contacts
            )

            # Fetch prospecting activity
            response = await asyncio.to_thread(
                self.client.post, "/fetch_prospecting_activity", headers=self.api_header
            )
            activations = self.assert_and_return_payload(response)

            # Assertions
            assert len(activations) == 0, "Expected no activations to be created"

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
            response = await asyncio.to_thread(
                self.client.post, "/fetch_prospecting_activity", headers=self.api_header
            )
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
                asyncio.to_thread(
                    self.client.post,
                    "/fetch_prospecting_activity",
                    headers=self.api_header,
                )
            )
            assert len(activations) == 2

            meeting_set_activation = next(
                a for a in activations if a["status"] == "Meeting Set"
            )
            opportunity_created_activation = next(
                a for a in activations if a["status"] == "Opportunity Created"
            )

            assert len(meeting_set_activation["event_ids"]) == 1
            assert opportunity_created_activation["opportunity"]["amount"] == 1733.42

            self._validate_prospecting_metadata(meeting_set_activation)
            self._validate_prospecting_metadata(opportunity_created_activation)

            self._validate_prospecting_effort(
                meeting_set_activation, expected_efforts=2, expected_activated_effort=2
            )
            self._validate_prospecting_effort(
                opportunity_created_activation,
                expected_efforts=2,
                expected_activated_effort=1,
                expected_opportunity_created_effort=1,
            )

    @pytest.mark.asyncio
    @patch(
        "app.salesforce_api._fetch_sobjects_async",
        side_effect=mock_fetch_sobjects_async,
    )
    @patch("requests.get", side_effect=response_based_on_query)
    async def test_should_increment_existing_activation_to_opportunity_created_status_when_opportunity_is_created_under_previously_activated_account(
        self, mock_sobject_fetch, async_mock_sobject_fetch
    ):
        with self.app.app_context():
            # setup mock api responses for one account activated via meeting set and another via opportunity created
            self.setup_one_activity_per_contact_with_staggered_created_dates_and_one_event_under_a_single_account_and_one_opportunity_for_a_different_account()

            activations = await self.assert_and_return_payload_async(
                asyncio.to_thread(
                    self.client.post,
                    "/fetch_prospecting_activity",
                    headers=self.api_header,
                )
            )

            meeting_set_activation: Activation = next(
                a for a in activations if a["status"] == "Meeting Set"
            )

            mock_contacts_for_more_tasks = [
                {"Id": contact_id}
                for contact_id in meeting_set_activation["active_contact_ids"]
            ]
            for contact in mock_contacts_for_more_tasks:
                contact["AccountId"] = meeting_set_activation["account"]["id"]
                contact["FirstName"] = "FirstName"
                contact["LastName"] = "LastName"
                contact["Account"] = {
                    "Id": meeting_set_activation["account"]["id"],
                    "Name": "Mock Account Name",
                }

            add_mock_response(
                "fetch_contacts_by_account_ids", mock_contacts_for_more_tasks
            )
            # setup mock api response to return an opportunity for the account activated via meeting set
            mock_opportunity = get_mock_opportunity_for_account(
                meeting_set_activation["account"]["id"]
            )
            add_mock_response(
                "fetch_opportunities_by_account_ids_from_date",
                [mock_opportunity],
            )

            mock_tasks = (
                get_one_mock_task_per_contact_for_unique_content_criteria_query_x(
                    mock_contacts_for_more_tasks
                )
            )
            for mock_task in mock_tasks:
                mock_task["Id"] = f"new_mock_task_id_{mock_task['WhoId']}"
            add_mock_response("contains_content_criteria_query", [])
            add_mock_response("unique_values_content_criteria_query", mock_tasks)
            add_mock_response("fetch_contacts_by_account_ids", [])
            add_mock_response(
                "fetch_events_by_account_ids_from_date",
                [],
            )
            add_mock_response("fetch_accounts_not_in_ids", [])

            updated_activations = await self.assert_and_return_payload_async(
                asyncio.to_thread(
                    self.client.post,
                    "/fetch_prospecting_activity",
                    headers=self.api_header,
                )
            )

            # Isolate the activation which meets the criteria
            activation_with_opportunity_created = [
                activation
                for activation in updated_activations
                if activation["status"] == "Opportunity Created"
                and activation["event_ids"]
            ]

            # Assert that there is at least one activation meeting the criteria
            assert (
                len(activation_with_opportunity_created) > 0
            ), "No Activation with Status 'Opportunity Created' and non-empty 'event_ids' found"

            prospecting_effort: List[ProspectingEffort] = (
                activation_with_opportunity_created[0]["prospecting_effort"]
            )
            assert len(prospecting_effort) == 3

            activated_prospecting_effort = [
                pe for pe in prospecting_effort if pe["status"] == "Activated"
            ]
            meeting_set_prospecting_effort = [
                pe for pe in prospecting_effort if pe["status"] == "Meeting Set"
            ]
            opportunity_created_prospecting_effort = [
                pe for pe in prospecting_effort if pe["status"] == "Opportunity Created"
            ]

            assert len(activated_prospecting_effort) == 1
            assert len(meeting_set_prospecting_effort) == 1
            assert len(opportunity_created_prospecting_effort) == 1

            assert len(activated_prospecting_effort[0]["task_ids"]) == 2
            assert len(meeting_set_prospecting_effort[0]["task_ids"]) == 0
            assert len(opportunity_created_prospecting_effort[0]["task_ids"]) == 2

    @pytest.mark.asyncio
    @patch(
        "app.salesforce_api._fetch_sobjects_async",
        side_effect=mock_fetch_sobjects_async,
    )
    @patch("requests.get", side_effect=response_based_on_query)
    async def test_should_create_new_activations_for_previously_activated_accounts_after_inactivity_threshold_is_reached(
        self, mock_sobject_fetch, async_mock_sobject_fetch
    ):
        with self.app.app_context():
            # setup mock api responses
            self.setup_thirty_tasks_across_ten_contacts_and_five_accounts()

            # initial account activation
            response = await asyncio.to_thread(
                self.client.post, "/fetch_prospecting_activity", headers=self.api_header
            )
            initial_activations = self.assert_and_return_payload(response)

            assert len(initial_activations) == 5

            # set last_prospecting_activity of first activation to 1 day over threshold
            activation_to_inactivate = (
                load_active_activations_order_by_first_prospecting_activity_asc().data[
                    0
                ]
            )
            activation_to_inactivate.last_prospecting_activity = (
                datetime.now() - timedelta(days=11)
            ).strftime("%Y-%m-%dT%H:%M:%S.000+0000")

            response = upsert_activations([activation_to_inactivate])

            if not response.success:
                raise Exception(response.message)

            # setup no prospecting activity to come back from Salesforce to force inactivation of Activation
            self.setup_zero_new_prospecting_activities_and_zero_new_opportunities_and_zero_new_events()

            # inactivate the Accounts
            response = await asyncio.to_thread(
                self.client.post, "/fetch_prospecting_activity", headers=self.api_header
            )
            self.assert_and_return_payload(response)

            inactive_activations = load_inactive_activations().data

            assert len(inactive_activations) == 1
            assert inactive_activations[0].id == activation_to_inactivate.id

            # setup prospecting activities to come back from Salesforce on the new attempt
            self.setup_six_tasks_across_two_contacts_and_one_account(
                inactive_activations[0].account.id
            )

            # assert that new activations are created for the previously activated accounts
            response = await asyncio.to_thread(
                self.client.post, "/fetch_prospecting_activity", headers=self.api_header
            )
            updated_activations = self.assert_and_return_payload(response)

            is_inactive_account_reactivated = any(
                activation["account"]["id"] == inactive_activations[0].account.id
                for activation in updated_activations
            )

            assert is_inactive_account_reactivated

    @pytest.mark.asyncio
    @patch(
        "app.salesforce_api._fetch_sobjects_async",
        side_effect=mock_fetch_sobjects_async,
    )
    @patch("requests.get", side_effect=response_based_on_query)
    async def test_should_update_activation_status_to_opportunity_created_without_additional_task(
        self, mock_sobject_fetch, async_mock_sobject_fetch
    ):
        with self.app.app_context():
            # Set up the initial activation
            self.setup_one_activity_per_contact_with_staggered_created_dates_and_one_event_under_a_single_account_and_one_opportunity_for_a_different_account()

            initial_activations = await self.assert_and_return_payload_async(
                asyncio.to_thread(
                    self.client.post,
                    "/fetch_prospecting_activity",
                    headers=self.api_header,
                )
            )

            meeting_set_activation = next(
                a for a in initial_activations if a["status"] == "Meeting Set"
            )

            # Create a new opportunity for the account with "Meeting Set" status
            mock_opportunity = get_mock_opportunity_for_account(
                meeting_set_activation["account"]["id"]
            )
            mock_opportunity["Amount"] = 6969.42

            add_mock_response(
                "fetch_opportunities_by_account_ids_from_date",
                [mock_opportunity],
            )

            # No new tasks
            mock_contacts = get_n_mock_contacts_for_account(
                1, meeting_set_activation["account"]["id"]
            )
            # mock twice since two different queries are being made against same endpoint
            add_mock_response("fetch_contacts_by_account_ids", mock_contacts)
            add_mock_response("fetch_contacts_by_account_ids", mock_contacts)
            add_mock_response("contains_content_criteria_query", [])
            add_mock_response("unique_values_content_criteria_query", [])
            add_mock_response("fetch_events_by_account_ids_from_date", [])
            add_mock_response("fetch_accounts_not_in_ids", [])

            # Fetch updated activations
            updated_activations = await self.assert_and_return_payload_async(
                asyncio.to_thread(
                    self.client.post,
                    "/fetch_prospecting_activity",
                    headers=self.api_header,
                )
            )

            # Find the activation that should have been updated
            updated_activation = next(
                (
                    a
                    for a in updated_activations
                    if a["account"]["id"] == meeting_set_activation["account"]["id"]
                ),
                None,
            )

            # Assert that the activation exists and has been updated
            assert updated_activation is not None, "The activation should still exist"
            assert (
                updated_activation["status"] == "Opportunity Created"
            ), "Status should be 'Opportunity Created'"
            assert (
                updated_activation["opportunity"]["amount"] == 6969.42
            ), "Opportunity amount should be updated"

            # Check that no new prospecting effort was added
            assert len(updated_activation["prospecting_effort"]) == len(
                meeting_set_activation["prospecting_effort"]
            ), "No new prospecting effort should be added"

    def setup_one_activity_per_contact_with_staggered_created_dates_and_one_event_under_a_single_account_and_one_opportunity_for_a_different_account(
        self,
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
            contact["OwnerId"] = mock_user_id
        mock_event = get_mock_event_for_contact(mock_contacts[3]["Id"])
        mock_event["OwnerId"] = mock_user_id
        mock_tasks = (
            get_n_mock_tasks_for_contacts_for_unique_values_content_criteria_query(
                1, mock_contacts, mock_user_id
            )
        )
        for task in mock_tasks:
            task["OwnerId"] = mock_user_id

        # Create a mapping from contact IDs to account IDs
        contact_to_account_id = {
            contact["Id"]: contact["AccountId"] for contact in mock_contacts
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

        mock_tasks = [task for tasks in tasks_by_account_id.values() for task in tasks]

        add_mock_response("unique_values_content_criteria_query", mock_tasks)

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

    def setup_six_tasks_across_two_contacts_and_one_account(self, account_id):
        mock_contacts = get_n_mock_contacts_for_account(2, account_id)
        mock_tasks = (
            get_n_mock_tasks_for_contacts_for_unique_values_content_criteria_query(
                3, mock_contacts, mock_user_id
            )
        )
        
        for task in mock_tasks:
            task["Id"] = str(random.randint(1000, 9999))

        add_mock_response("unique_values_content_criteria_query", mock_tasks)
        add_mock_response(
            "fetch_accounts_not_in_ids",
            [account for account in get_five_mock_accounts() if account["Id"] == account_id],
        )
        add_mock_response(
            "fetch_contacts_by_account_ids",
            mock_contacts,
        )
        add_mock_response(
            "fetch_contacts_by_account_ids",
            mock_contacts,
        )
        add_mock_response(
            "contains_content_criteria_query",
            [],
        )
        add_mock_response("unique_values_content_criteria_query", mock_tasks)
        add_mock_response(
            "fetch_contacts_by_ids_and_non_null_accounts",
            mock_contacts,
        )
        add_mock_response(
            "fetch_opportunities_by_account_ids_from_date",
            [],
        )
        add_mock_response(
            "fetch_opportunities_by_account_ids_from_date",
            [],
        )
        add_mock_response("fetch_events_by_account_ids_from_date", [])
        add_mock_response(
            "fetch_contacts_by_account_ids",
            mock_contacts,
        )
        add_mock_response(
            "fetch_contacts_by_account_ids",
            mock_contacts,
        )

    def _validate_prospecting_metadata(self, activation):
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

    def _validate_prospecting_effort(
        self,
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
                len(effort_by_status["Activated"]["task_ids"])
                == expected_activated_effort
            )

        if "Engaged" in effort_by_status:
            assert (
                len(effort_by_status["Engaged"]["task_ids"]) == expected_engaged_effort
            )

        if "Opportunity Created" in effort_by_status:
            assert (
                len(effort_by_status["Opportunity Created"]["task_ids"])
                == expected_opportunity_created_effort
            )

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

        assert (
            unique_values_content_filter_model.filterLogic == ""
        ), "Filter logic should be an empty string, Morty!"

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

        mock_accounts = get_five_mock_accounts()
        mock_contacts = [
            contact
            for account in mock_accounts
            for contact in get_n_mock_contacts_for_account(2, account["Id"])
        ]
        for contact in mock_contacts:
            contact["Id"] = f"mock_contact_id_{random.randint(1000, 9999)}"

        mock_tasks = (
            get_n_mock_tasks_for_contacts_for_unique_values_content_criteria_query(
                3, mock_contacts, mock_user_id
            )
        )
        add_mock_response("unique_values_content_criteria_query", mock_tasks)
        add_mock_response("unique_values_content_criteria_query", mock_tasks)
        add_mock_response(
            "fetch_accounts_not_in_ids",
            mock_accounts,
        )
        add_mock_response(
            "fetch_contacts_by_ids_and_non_null_accounts",
            mock_contacts,
        )
        add_mock_response(
            "fetch_opportunities_by_account_ids_from_date",
            [get_mock_opportunity_for_account(mock_accounts[0]["Id"])],
        )
        add_mock_response("fetch_events_by_account_ids_from_date", [])
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

    def setup_zero_new_prospecting_activities_and_zero_new_opportunities_and_zero_new_events(
        self,
    ):
        add_mock_response("fetch_contacts_by_account_ids", [])
        add_mock_response("fetch_opportunities_by_account_ids_from_date", [])
        add_mock_response("fetch_events_by_account_ids_from_date", [])
        add_mock_response("fetch_accounts_not_in_ids", [])
        add_mock_response("fetch_contacts_by_account_ids", [])
        add_mock_response("fetch_contacts_by_account_ids", [])
