import pytest
import os
import asyncio
import random
from datetime import datetime, timedelta
from unittest.mock import patch
from app import create_app
from app.data_models import TokenData
from app.database.dml import save_session, delete_session
from app.database.supabase_connection import get_supabase_admin_client
from app.tests.mocks import (
    mock_fetch_sobjects_async,
    response_based_on_query,
    get_five_mock_accounts,
    get_two_mock_contacts_per_account,
    get_n_mock_tasks_for_contacts_for_unique_values_content_criteria_query,
    get_n_mock_tasks_per_contact_for_contains_content_crieria_query,
    add_mock_response,
    clear_mocks,
)
from app.tests.test_helpers import (
    do_onboarding_flow,
    assert_and_return_payload,
    validate_prospecting_effort,
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
class TestActivationWithEngagedStatus:
    @pytest.fixture(autouse=True)
    async def setup_method(self, request):
        os.environ["FLASK_ENV"] = "testing"
        self.app = create_app()
        self.app.testing = True
        self.client = self.app.test_client()

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
    @patch(
        "app.salesforce_api._fetch_sobjects_async",
        side_effect=mock_fetch_sobjects_async,
    )
    @patch("requests.get", side_effect=response_based_on_query)
    async def test_should_activate_account_with_engaged_status_given_sufficient_outbound_activity_and_a_single_inbound_activity(
        self, mock_sobject_fetch, async_mock_sobject_fetch
    ):
        with self.app.app_context():
            # Setup mock data
            mock_account = get_five_mock_accounts()[0]
            mock_contacts = get_two_mock_contacts_per_account([mock_account])
            mock_outbound_tasks = (
                get_n_mock_tasks_for_contacts_for_unique_values_content_criteria_query(
                    3, mock_contacts, mock_user_id
                )
            )
            for task in mock_outbound_tasks:
                task["Id"] = f"mock_outbound_task_id_{random.randint(1000, 9999)}"
                
            mock_inbound_task = (
                get_n_mock_tasks_per_contact_for_contains_content_crieria_query(
                    1, [mock_contacts[0]], mock_user_id
                )
            )
            # set mock_inbound_task CreatedDate to be 1 hour later than the outbound tasks
            mock_inbound_task[0]["CreatedDate"] = (
                datetime.strptime(mock_outbound_tasks[0]["CreatedDate"], "%Y-%m-%dT%H:%M:%S.000+0000") + timedelta(hours=1)
            ).strftime("%Y-%m-%dT%H:%M:%S.000+0000")
            mock_inbound_task[0]["Id"] = f"mock_inbound_task_id_{random.randint(1000, 9999)}"
            
            # Setup mock responses
            add_mock_response(
                "fetch_salesforce_users",
                [{"Id": mock_user_id, "FirstName": "Mock", "LastName": "User"}],
            )
            add_mock_response("fetch_accounts_not_in_ids", [mock_account])
            add_mock_response("fetch_contacts_by_account_ids", mock_contacts)
            add_mock_response("fetch_contacts_by_account_ids", mock_contacts)
            add_mock_response(
                "unique_values_content_criteria_query", mock_outbound_tasks
            )
            add_mock_response("contains_content_criteria_query", mock_inbound_task)
            add_mock_response("fetch_opportunities_by_account_ids_from_date", [])
            add_mock_response("fetch_events_by_account_ids_from_date", [])
            add_mock_response(
                "fetch_contacts_by_ids_and_non_null_accounts", mock_contacts
            )

            # Fetch prospecting activity
            response = await asyncio.to_thread(
                self.client.post, "/fetch_prospecting_activity", headers=self.api_header
            )
            activations = assert_and_return_payload(response)

            # Assertions
            assert len(activations) == 1, "Expected one activation to be created"
            activation = activations[0]
            assert (
                activation["status"] == "Engaged"
            ), "Activation status should be 'Engaged'"
            assert (
                activation["account"]["id"] == mock_account["Id"]
            ), "Activation should be for the correct account"
            assert (
                len(activation["active_contact_ids"]) == 2
            ), "Activation should have two active contacts"

            # Validate prospecting effort
            validate_prospecting_effort(
                activation,
                expected_efforts=2,
                expected_activated_effort=6,
                expected_engaged_effort=0,
                expected_opportunity_created_effort=0,
            )

            # Validate prospecting metadata
            metadata = activation["prospecting_metadata"]
            assert len(metadata) == 1, "Expected one metadata entry since only one outbound task criteria was met"

            unique_content_metadata = next(
                m for m in metadata if m["name"] == "Unique Content"
            )
            assert (
                unique_content_metadata["total"] == 6
            ), "Expected 6 total activities for Unique Content (3 per contact)"

            assert not any(
                m for m in metadata if m["name"] == "Contains Content"
            ), "There should be no metadata entries for 'Contains Content'"
