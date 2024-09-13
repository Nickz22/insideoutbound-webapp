import pytest
import os
import asyncio
from unittest.mock import patch
from datetime import datetime, timedelta
from app import create_app
from app.data_models import TokenData
from app.database.dml import save_session, delete_session, upsert_activations
from app.database.activation_selector import (
    load_active_activations_order_by_first_prospecting_activity_asc,
    load_inactive_activations,
)
from app.database.supabase_connection import get_supabase_admin_client
from app.tests.mocks import (
    mock_fetch_sobjects_async,
    response_based_on_query,
    add_mock_response,
    clear_mocks,
)
from app.tests.test_helpers import (
    do_onboarding_flow,
    setup_thirty_tasks_across_ten_contacts_and_five_accounts,
    setup_zero_new_prospecting_activities_and_zero_new_opportunities_and_zero_new_events,
    assert_and_return_payload,
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
class TestUnresponsiveActivationLogic:
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
    async def test_should_set_activations_without_prospecting_activities_past_inactivity_threshold_as_unresponsive(
        self, mock_sobject_fetch, async_mock_sobject_fetch
    ):
        with self.app.app_context():
            setup_thirty_tasks_across_ten_contacts_and_five_accounts(mock_user_id)
            response = await asyncio.to_thread(
                self.client.post, "/fetch_prospecting_activity", headers=self.api_header
            )
            initial_activations = assert_and_return_payload(response)

            assert len(initial_activations) == 5

            # Set the last_prospecting_activity of the first activation to 11 days ago
            activation_to_inactivate = (
                load_active_activations_order_by_first_prospecting_activity_asc()
            ).data[0]
            activation_to_inactivate.last_prospecting_activity = (
                datetime.now() - timedelta(days=11)
            ).strftime("%Y-%m-%dT%H:%M:%S.000+0000")

            upsert_activations([activation_to_inactivate])

            setup_zero_new_prospecting_activities_and_zero_new_opportunities_and_zero_new_events(
                mock_user_id
            )

            response = await asyncio.to_thread(
                self.client.post, "/fetch_prospecting_activity", headers=self.api_header
            )
            assert_and_return_payload(response)

            unresponsive_activations = load_inactive_activations().data
            assert len(unresponsive_activations) == 1
            assert unresponsive_activations[0].id == activation_to_inactivate.id
