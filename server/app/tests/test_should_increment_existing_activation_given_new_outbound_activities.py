import pytest
import os
import asyncio
import uuid
from unittest.mock import patch
from app import create_app
from app.data_models import TokenData
from app.database.dml import save_session, delete_session
from app.database.supabase_connection import get_supabase_admin_client
from app.tests.mocks import (
    mock_fetch_contact_by_id_map,
    mock_fetch_contacts_by_account_ids,
    response_based_on_query,
    get_five_mock_accounts,
    get_two_mock_contacts_per_account,
    get_n_mock_tasks_for_contacts_for_unique_values_content_criteria_query,
    add_mock_response,
    clear_mocks,
    set_mock_contacts_for_map,
)
from app.tests.test_helpers import (
    do_onboarding_flow,
    assert_and_return_payload_async,
    get_mock_token_data,
    get_salesforce_compatible_datetime_now,
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
class TestIncrementExistingActivationWithNewOutboundActivities:
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

            do_onboarding_flow(self.client, self.api_header)
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

    @staticmethod
    def setup_mock_user():
        add_mock_response("fetch_logged_in_salesforce_user", {"Id": mock_user_id})

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
    async def test_should_increment_existing_activation_given_new_outbound_activities(
        self,
        mock_sobject_fetch,
        mock_fetch_contact_composite,
        mock_fetch_contacts_by_account_ids,
    ):
        with self.app.app_context():
            # Set up initial activation
            mock_account = get_five_mock_accounts()[0]
            mock_contacts = get_two_mock_contacts_per_account([mock_account])
            initial_tasks = (
                get_n_mock_tasks_for_contacts_for_unique_values_content_criteria_query(
                    3, mock_contacts, mock_user_id
                )
            )

            # set created_date to iso now
            for task in initial_tasks:
                task["CreatedDate"] = get_salesforce_compatible_datetime_now()
                task["Id"] = str(uuid.uuid4())

            # Setup mock responses for initial fetch
            set_mock_contacts_for_map(mock_contacts)
            add_mock_response("fetch_all_matching_tasks", initial_tasks)
            add_mock_response("fetch_opportunities_by_account_ids_from_date", [])
            add_mock_response("fetch_events_by_contact_ids_from_date", [])

            add_mock_response(
                "fetch_salesforce_users",
                [{"Id": mock_user_id, "FirstName": "Mock", "LastName": "User"}],
            )

            # Fetch initial prospecting activity
            initial_activations = await assert_and_return_payload_async(
                asyncio.to_thread(
                    self.client.post,
                    "/process_new_prospecting_activity",
                    headers=self.api_header,
                )
            )

            activation_ids = [initial_activations[0]["id"]]
            query_params = "&".join([f"activation_ids[]={id}" for id in activation_ids])
            database_activations_response = await asyncio.to_thread(
                self.client.get,
                f"/get_full_prospecting_activities_filtered_by_ids?{query_params}",
                headers=self.api_header,
            )
            database_activations = database_activations_response.get_json()["data"][0][
                "raw_data"
            ]

            initial_activation = database_activations[0]

            assert len(initial_activations) == 1, "Expected one activation"
            assert initial_activation["status"] == "Activated"

            # Set up new outbound activities
            new_tasks = (
                get_n_mock_tasks_for_contacts_for_unique_values_content_criteria_query(
                    2, mock_contacts, mock_user_id
                )
            )

            # set created_date to iso now
            for task in new_tasks:
                task["CreatedDate"] = get_salesforce_compatible_datetime_now()
                task["Id"] = str(uuid.uuid4())

            # Setup mock responses for the second fetch
            add_mock_response(
                "fetch_all_matching_tasks", new_tasks
            )  # increment existing activations flow
            add_mock_response(
                "fetch_all_matching_tasks", new_tasks
            )  # unresponsive flow
            add_mock_response(
                "fetch_all_matching_tasks", new_tasks
            )  # compute new activations flowå
            add_mock_response(
                "fetch_opportunities_by_account_ids_from_date", []
            )  # increment existing activations flow
            add_mock_response(
                "fetch_events_by_contact_ids_from_date", []
            )  # increment existing activations flow
            add_mock_response(
                "fetch_opportunities_by_account_ids_from_date", []
            )  # compute new activations flow
            add_mock_response(
                "fetch_events_by_contact_ids_from_date", []
            )  # compute new activations flow
            add_mock_response(
                "fetch_salesforce_users",
                [{"Id": mock_user_id, "FirstName": "Mock", "LastName": "User"}],
            )

            # Fetch updated prospecting activity
            updated_activations = await assert_and_return_payload_async(
                asyncio.to_thread(
                    self.client.post,
                    "/process_new_prospecting_activity",
                    headers=self.api_header,
                )
            )

            assert len(updated_activations) == 1, "Still expected one activation"

            activation_ids = [updated_activations[0]["id"]]
            query_params = "&".join([f"activation_ids[]={id}" for id in activation_ids])
            database_activations_response = await asyncio.to_thread(
                self.client.get,
                f"/get_full_prospecting_activities_filtered_by_ids?{query_params}",
                headers=self.api_header,
            )
            database_activations = database_activations_response.get_json()["data"][0][
                "raw_data"
            ]

            updated_activation = database_activations[0]

            # Assert status is still "Activated"
            assert (
                updated_activation["status"] == "Activated"
            ), "Status should still be Activated"

            # Check prospecting metadata
            metadata = updated_activation["prospecting_metadata"]
            assert len(metadata) == 1, "Expected one metadata entry"
            assert metadata[0]["name"] == "Unique Content"
            assert (
                metadata[0]["total"] == 10
            ), "Expected 10 total activities (6 initial + 4 new)"

            # Check prospecting effort
            efforts = updated_activation["prospecting_effort"]
            assert len(efforts) == 1, "Expected one effort entry"
            activated_effort = efforts[0]
            assert activated_effort["status"] == "Activated"
            assert len(activated_effort["task_ids"]) == 10, "Expected 10 task IDs"
