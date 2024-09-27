import pytest
import os
import asyncio
from unittest.mock import patch
from app import create_app
from app.data_models import TokenData
from app.database.dml import save_session, delete_session, save_settings
from app.database.supabase_connection import get_supabase_admin_client
from app.database.activation_selector import (
    load_active_activations_order_by_first_prospecting_activity_asc,
)
from app.tests.mocks import (
    response_based_on_query,
    add_mock_response,
    clear_mocks,
    get_five_mock_accounts,
    get_two_mock_contacts_per_account,
    get_n_mock_tasks_for_contacts_for_unique_values_content_criteria_query,
    get_mock_opportunity_for_account,
    mock_fetch_contact_by_id_map,
    mock_fetch_contacts_by_account_ids,
    set_mock_contacts_for_map,
)
from app.tests.test_helpers import (
    do_onboarding_flow,
    get_mock_token_data,
    setup_one_activity_per_contact_with_staggered_created_dates_and_one_event_under_a_single_account_and_one_opportunity_for_a_different_account,
    assert_and_return_payload_async,
    get_salesforce_compatible_datetime_now,
    get_salesforce_compatible_datetime_hours_from_now,
)
from contextlib import contextmanager
import logging

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

mock_user_id = "mock_user_id"

pytest_plugins = ("pytest_asyncio",)


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
class TestNoNewActivationWithMeetingOrOpportunity:
    @pytest.fixture(autouse=True)
    async def setup_method(self, request):
        os.environ["FLASK_ENV"] = "testing"
        self.app = create_app()
        self.app.testing = True
        self.client = self.app.test_client()

        mock_token_data: TokenData = get_mock_token_data()

        with context_tracker(self.app):
            token = save_session(mock_token_data, True)
            self.api_header = {"X-Session-Token": token}

            settings = do_onboarding_flow(self.client, self.api_header)
            settings.activate_by_meeting = False
            settings.activate_by_opportunity = False
            save_settings(settings)
            self.setup_mock_user()

            try:
                yield
            finally:
                delete_session(self.api_header["X-Session-Token"])
                supabase = get_supabase_admin_client()
                supabase.table("Activations").delete().in_(
                    "activated_by_id", [mock_user_id]
                ).execute()
                clear_mocks()

    @pytest.mark.asyncio
    @patch("requests.get", side_effect=response_based_on_query)
    @patch(
        "app.salesforce_api.fetch_contact_by_id_map",
        side_effect=mock_fetch_contact_by_id_map,
    )
    async def test_should_not_create_new_activation_when_activate_by_meeting_and_activate_by_opportunity_are_false(
        self, mock_sobject_fetch, mock_fetch_contact_composite
    ):
        with self.app.app_context():
            setup_one_activity_per_contact_with_staggered_created_dates_and_one_event_under_a_single_account_and_one_opportunity_for_a_different_account(
                mock_user_id
            )

            activations = await assert_and_return_payload_async(
                asyncio.to_thread(
                    self.client.post,
                    "/fetch_prospecting_activity",
                    headers=self.api_header,
                )
            )

            # Assert that no activations were created
            assert len(activations) == 0, "Expected no activations, but found some"
            activations = (
                load_active_activations_order_by_first_prospecting_activity_asc()
            )

            assert (
                len(activations.data) == 0
            ), "Expected no activations in the database, but found some"

    @pytest.mark.asyncio
    @patch("requests.get", side_effect=response_based_on_query)
    @patch(
        "app.salesforce_api.fetch_contact_by_id_map",
        side_effect=mock_fetch_contact_by_id_map,
    )
    @patch(
        "app.services.activation_service.fetch_contacts_by_account_ids",
        side_effect=mock_fetch_contacts_by_account_ids,
    )
    async def test_should_change_status_when_new_meeting_is_added_while_activate_by_meeting_is_false(
        self,
        mock_sobject_fetch,
        mock_fetch_contact_composite,
        mock_fetch_contacts_by_account_ids,
    ):
        with self.app.app_context():
            # Setup initial activation
            mock_account = get_five_mock_accounts()[0]
            mock_contacts = get_two_mock_contacts_per_account([mock_account])
            mock_tasks = (
                get_n_mock_tasks_for_contacts_for_unique_values_content_criteria_query(
                    3, mock_contacts, mock_user_id
                )
            )

            set_mock_contacts_for_map(mock_contacts)
            add_mock_response("fetch_all_matching_tasks", mock_tasks)
            add_mock_response("fetch_opportunities_by_account_ids_from_date", [])
            add_mock_response("fetch_events_by_contact_ids_from_date", [])
            add_mock_response(
                "fetch_salesforce_users",
                [{"Id": mock_user_id, "FirstName": "Mock", "LastName": "User"}],
            )

            # Create initial activation
            await self._create_initial_activation()

            # Now, let's add a meeting
            mock_event = {
                "Id": "mock_event_id",
                "WhoId": mock_contacts[0].id,
                "WhatId": mock_account["Id"],
                "Subject": "Mock Event",
                "StartDateTime": "2023-05-01T10:00:00.000+0000",
                "EndDateTime": "2023-05-01T11:00:00.000+0000",
            }

            # unresponsive flow
            add_mock_response("fetch_all_matching_tasks", [])
            # increment flow
            add_mock_response("fetch_all_matching_tasks", [])
            # increment flow
            add_mock_response("fetch_opportunities_by_account_ids_from_date", [])
            # compute activation flow
            add_mock_response("fetch_opportunities_by_account_ids_from_date", [])
            # increment flow
            add_mock_response("fetch_events_by_contact_ids_from_date", [mock_event])
            # compute activation flow
            add_mock_response("fetch_events_by_contact_ids_from_date", [mock_event])
            add_mock_response(
                "fetch_salesforce_users",
                [{"Id": mock_user_id, "FirstName": "Mock", "LastName": "User"}],
            )

            # Fetch updated prospecting activity
            updated_activation = await self._fetch_updated_activation()

            # Assertions
            assert (
                updated_activation["status"] == "Meeting Set"
            ), "Activation status should be 'Meeting Set' because a meeting was added"
            assert (
                len(updated_activation["event_ids"]) == 1
            ), "Activation should have one event"
            assert (
                updated_activation["opportunity"] is None
            ), "Activation should not have an opportunity"

    @pytest.mark.asyncio
    @patch("requests.get", side_effect=response_based_on_query)
    @patch(
        "app.salesforce_api.fetch_contact_by_id_map",
        side_effect=mock_fetch_contact_by_id_map,
    )
    @patch(
        "app.services.activation_service.fetch_contacts_by_account_ids",
        side_effect=mock_fetch_contacts_by_account_ids,
    )
    async def test_should_change_activation_status_when_new_opportunity_added_and_activate_by_opportunity_is_false(
        self,
        mock_sobject_fetch,
        mock_fetch_contact_composite,
        mock_fetch_contacts_by_account_ids,
    ):
        with self.app.app_context():
            # Setup initial activation
            mock_account = get_five_mock_accounts()[0]
            mock_contacts = get_two_mock_contacts_per_account([mock_account])
            mock_tasks = (
                get_n_mock_tasks_for_contacts_for_unique_values_content_criteria_query(
                    3, mock_contacts, mock_user_id
                )
            )

            set_mock_contacts_for_map(mock_contacts)
            add_mock_response("fetch_all_matching_tasks", mock_tasks)
            add_mock_response("fetch_opportunities_by_account_ids_from_date", [])
            add_mock_response("fetch_events_by_contact_ids_from_date", [])
            add_mock_response(
                "fetch_salesforce_users",
                [{"Id": mock_user_id, "FirstName": "Mock", "LastName": "User"}],
            )

            # Create initial activation
            await self._create_initial_activation()

            # Now, let's add an opportunity
            mock_opportunity = {
                "Id": "mock_opportunity_id",
                "AccountId": mock_account["Id"],
                "Name": "Mock Opportunity",
                "Amount": 10000,
                "CloseDate": "2023-06-01",
                "StageName": "Prospecting",
            }

            # unresponsive flow
            add_mock_response("fetch_all_matching_tasks", [])
            # increment flow
            add_mock_response("fetch_all_matching_tasks", [])
            # compute activation flow
            add_mock_response("fetch_all_matching_tasks", [])
            # increment flow
            add_mock_response(
                "fetch_opportunities_by_account_ids_from_date", [mock_opportunity]
            )
            # compute activation flow
            add_mock_response("fetch_opportunities_by_account_ids_from_date", [])
            # increment flow
            add_mock_response("fetch_events_by_contact_ids_from_date", [])
            # compute activation flow
            add_mock_response("fetch_events_by_contact_ids_from_date", [])
            add_mock_response(
                "fetch_salesforce_users",
                [{"Id": mock_user_id, "FirstName": "Mock", "LastName": "User"}],
            )

            # Fetch prospecting activity again
            updated_activation = await self._fetch_updated_activation()

            # Assertions
            assert (
                updated_activation["status"] == "Opportunity Created"
            ), "Activation status should be 'Opportunity Created' because an opportunity was added"
            assert (
                len(updated_activation["event_ids"] or []) == 0
            ), "Activation should have no events"
            assert (
                updated_activation["opportunity"] is not None
            ), "Activation should have an opportunity"
            assert (
                updated_activation["opportunity"]["amount"] == 10000
            ), "Opportunity amount should be 10000"

    @pytest.mark.asyncio
    @patch("requests.get", side_effect=response_based_on_query)
    @patch(
        "app.salesforce_api.fetch_contact_by_id_map",
        side_effect=mock_fetch_contact_by_id_map,
    )
    @patch(
        "app.services.activation_service.fetch_contacts_by_account_ids",
        side_effect=mock_fetch_contacts_by_account_ids,
    )
    async def test_should_roll_up_existing_meeting_and_opportunity_when_creating_activation(
        self,
        mock_sobject_fetch,
        mock_fetch_contact_composite,
        mock_fetch_contacts_by_account_ids,
    ):
        with self.app.app_context():
            # Setup initial activation with existing meeting and opportunity
            mock_account = get_five_mock_accounts()[0]
            mock_contacts = get_two_mock_contacts_per_account([mock_account])
            mock_tasks = (
                get_n_mock_tasks_for_contacts_for_unique_values_content_criteria_query(
                    3, mock_contacts, mock_user_id
                )
            )
            # scramble task ids and set CreatedDate to now
            for mock_task in mock_tasks:
                mock_task["Id"] = "mock_task_id_" + mock_task["Id"]
                mock_task["CreatedDate"] = get_salesforce_compatible_datetime_now()

            # Add a mock event (meeting)
            mock_event = {
                "Id": "mock_event_id",
                "WhoId": mock_contacts[0].id,
                "WhatId": mock_account["Id"],
                "Subject": "Existing Mock Event",
                "StartDateTime": get_salesforce_compatible_datetime_now(),
                "EndDateTime": get_salesforce_compatible_datetime_hours_from_now(1),
            }

            # Add a mock opportunity
            mock_opportunity = get_mock_opportunity_for_account(mock_account["Id"])
            mock_opportunity["Amount"] = 15000
            mock_opportunity["CreatedDate"] = get_salesforce_compatible_datetime_now()

            set_mock_contacts_for_map(mock_contacts)
            # compute activation flow
            add_mock_response("fetch_all_matching_tasks", mock_tasks)
            add_mock_response(
                "fetch_salesforce_users",
                [{"Id": mock_user_id, "FirstName": "Mock", "LastName": "User"}],
            )
            # compute activation flow
            add_mock_response("fetch_events_by_contact_ids_from_date", [mock_event])
            # compute activation flow
            add_mock_response(
                "fetch_opportunities_by_account_ids_from_date", [mock_opportunity]
            )

            # Create initial activation
            response = await asyncio.to_thread(
                self.client.post, "/fetch_prospecting_activity", headers=self.api_header
            )
            initial_activations = self.assert_and_return_payload(response)

            # Assertions
            assert len(initial_activations) == 1, "Expected one initial activation"
            activation = initial_activations[0]

            assert (
                activation["status"] == "Opportunity Created"
            ), "Activation status should be 'Opportunity Created' since an opportunity was added"
            assert len(activation["event_ids"]) == 1, "Activation should have one event"
            assert (
                activation["event_ids"][0] == "mock_event_id"
            ), "Event ID should match the mock event"
            assert (
                activation["opportunity"] is not None
            ), "Activation should have an opportunity"
            assert (
                activation["opportunity"]["amount"] == 15000
            ), "Opportunity amount should be 15000"
            assert (
                activation["opportunity"]["id"] == mock_opportunity["Id"]
            ), "Opportunity ID should match the mock opportunity"


    async def _create_initial_activation(self):
        response = await asyncio.to_thread(
            self.client.post, "/fetch_prospecting_activity", headers=self.api_header
        )
        initial_activations = self.assert_and_return_payload(response)
        assert len(initial_activations) == 1, "Expected one initial activation"
        initial_activation = initial_activations[0]
        assert (
            initial_activation["status"] == "Activated"
        ), "Initial activation status should be 'Activated'"
        return initial_activation

    async def _fetch_updated_activation(self):
        response = await asyncio.to_thread(
            self.client.post, "/fetch_prospecting_activity", headers=self.api_header
        )
        updated_activations = self.assert_and_return_payload(response)
        assert (
            len(updated_activations) == 1
        ), "Expected one activation after adding meeting or opportunity"
        return updated_activations[0]

    @staticmethod
    def assert_and_return_payload(response):
        assert response.status_code == 200
        data = response.get_json()
        return data["data"][0]["raw_data"]

    @staticmethod
    def setup_mock_user():
        add_mock_response("fetch_logged_in_salesforce_user", {"Id": mock_user_id})
