import pytest
import os
import asyncio
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
    add_mock_response,
    clear_mocks,
)
from app.tests.test_helpers import do_onboarding_flow  # Import the new helper
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
class TestActivationLogic:
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

            do_onboarding_flow(self.client, self.api_header)  # Use the new helper
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
            add_mock_response(
                "fetch_salesforce_users",
                [{"Id": mock_user_id, "FirstName": "Mock", "LastName": "User"}],
            )
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
        data = response.get_json()
        return data["data"][0]["raw_data"]