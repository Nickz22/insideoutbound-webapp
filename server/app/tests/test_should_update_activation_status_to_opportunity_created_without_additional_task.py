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
    get_mock_opportunity_for_account,
    get_n_mock_contacts_for_account,
    add_mock_response,
    clear_mocks,
)
from app.tests.test_helpers import (
    do_onboarding_flow,
    assert_and_return_payload_async,
    setup_one_activity_per_contact_with_staggered_created_dates_and_one_event_under_a_single_account_and_one_opportunity_for_a_different_account,
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
class TestUpdateActivationStatusToOpportunityCreated:
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
    async def test_should_update_activation_status_to_opportunity_created_without_additional_task(
        self, mock_sobject_fetch, async_mock_sobject_fetch
    ):
        with self.app.app_context():
            # Set up the initial activation
            setup_one_activity_per_contact_with_staggered_created_dates_and_one_event_under_a_single_account_and_one_opportunity_for_a_different_account(
                mock_user_id
            )

            initial_activations = await assert_and_return_payload_async(
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
            updated_activations = await assert_and_return_payload_async(
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

            # Check that new prospecting effort was added
            assert (
                len(updated_activation["prospecting_effort"])
                == len(meeting_set_activation["prospecting_effort"]) + 1
            ), "New prospecting effort should be added since 'Opportunity Created' status is newly reached"
