import pytest
import os
import asyncio
from unittest.mock import patch
from app import create_app
from app.data_models import TokenData
from app.database.dml import save_session, delete_session, save_settings
from app.database.settings_selector import load_settings
from app.database.supabase_connection import (
    get_supabase_admin_client,
    set_session_state,
)
from app.tests.mocks import (
    mock_fetch_contact_by_id_map,
    response_based_on_query,
    add_mock_response,
    clear_mocks,
)
from app.tests.test_helpers import (
    do_onboarding_flow,
    setup_one_activity_per_contact_with_staggered_created_dates_and_one_event_under_a_single_account_and_one_opportunity_for_a_different_account,
    setup_one_activity_per_contact_with_staggered_created_dates_and_one_task_meeting_under_a_single_account_and_one_opportunity_for_a_different_account,
    assert_and_return_payload_async,
    validate_prospecting_metadata,
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
class TestNewActivationWithMeetingOrOpportunity:
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
    @patch("requests.get", side_effect=response_based_on_query)
    @patch(
        "app.salesforce_api.fetch_contact_by_id_map",
        side_effect=mock_fetch_contact_by_id_map,
    )
    async def test_should_create_new_activation_when_one_activity_per_contact_and_one_meeting_or_one_opportunity_is_in_salesforce(
        self, mock_sobject_fetch, mock_fetch_contact_by_id_map
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
            assert (
                len(activations) == 2
            ), "Expected two activations to be created since two Accounts were setup with an Event and Opportunity respectively"

            meeting_set_activation = next(
                a for a in activations if a["status"] == "Meeting Set"
            )
            opportunity_created_activation = next(
                a for a in activations if a["status"] == "Opportunity Created"
            )

            assert len(meeting_set_activation["event_ids"]) == 1
            assert opportunity_created_activation["opportunity"]["amount"] == 1733.42

            validate_prospecting_metadata(meeting_set_activation)
            validate_prospecting_metadata(opportunity_created_activation)

            validate_prospecting_effort(
                meeting_set_activation, expected_efforts=2, expected_activated_effort=2
            )
            validate_prospecting_effort(
                opportunity_created_activation,
                expected_efforts=2,
                expected_activated_effort=1,
                expected_opportunity_created_effort=1,
            )

    @pytest.mark.asyncio
    @patch("requests.get", side_effect=response_based_on_query)
    @patch(
        "app.salesforce_api.fetch_contact_by_id_map",
        side_effect=mock_fetch_contact_by_id_map,
    )
    async def test_should_create_new_activation_when_one_activity_per_contact_and_one_task_meeting_or_one_opportunity_is_in_salesforce(
        self, mock_sobject_fetch, mock_fetch_contact_by_id_map
    ):
        with self.app.app_context():
            set_session_state(
                {
                    "salesforce_id": mock_user_id,
                    "access_token": "access_token",
                    "refresh_token": "refresh_token",
                    "instance_url": "instance_url",
                    "org_id": "org_id",
                    "is_sandbox": "is_sandbox",
                }
            )
            settings = load_settings()
            settings.meeting_object = "Task"
            save_settings(settings)
            setup_one_activity_per_contact_with_staggered_created_dates_and_one_task_meeting_under_a_single_account_and_one_opportunity_for_a_different_account(
                mock_user_id, settings
            )

            activations = await assert_and_return_payload_async(
                asyncio.to_thread(
                    self.client.post,
                    "/fetch_prospecting_activity",
                    headers=self.api_header,
                )
            )
            assert (
                len(activations) == 2
            ), "Expected two activations to be created since two Accounts were setup with an Event and Opportunity respectively"

            meeting_set_activation = next(
                a for a in activations if a["status"] == "Meeting Set"
            )
            opportunity_created_activation = next(
                a for a in activations if a["status"] == "Opportunity Created"
            )

            assert len(meeting_set_activation["event_ids"]) == 1
            assert opportunity_created_activation["opportunity"]["amount"] == 1733.42

            validate_prospecting_metadata(meeting_set_activation)
            validate_prospecting_metadata(opportunity_created_activation)

            validate_prospecting_effort(
                meeting_set_activation, expected_efforts=2, expected_activated_effort=2
            )
            validate_prospecting_effort(
                opportunity_created_activation,
                expected_efforts=2,
                expected_activated_effort=1,
                expected_opportunity_created_effort=1,
            )
