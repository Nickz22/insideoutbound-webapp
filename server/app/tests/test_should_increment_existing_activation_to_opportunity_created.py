import uuid
import pytest
import os
import asyncio
from unittest.mock import patch
from app import create_app
from app.data_models import Contact, TokenData, Activation, ProspectingEffort, Account
from app.database.dml import save_session, delete_session
from app.database.supabase_connection import get_supabase_admin_client
from app.tests.mocks import (
    get_mock_contacts_for_map,
    mock_fetch_contact_by_id_map,
    mock_fetch_contacts_by_account_ids,
    response_based_on_query,
    get_mock_opportunity_for_account,
    add_mock_response,
    clear_mocks,
    get_n_mock_tasks_per_contact_for_contains_content_crieria_query,
    set_mock_contacts_for_map,
)
from app.tests.test_helpers import (
    do_onboarding_flow,
    assert_and_return_payload_async,
    get_mock_token_data,
    setup_one_activity_per_contact_with_staggered_created_dates_and_one_event_under_a_single_account_and_one_opportunity_for_a_different_account,
)
from contextlib import contextmanager
import logging
from typing import List

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
class TestIncrementExistingActivationToOpportunityCreated:
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
    @patch("app.salesforce_api.fetch_contact_by_id_map", side_effect=mock_fetch_contact_by_id_map)
    @patch(
        "app.services.activation_service.fetch_contacts_by_account_ids",
        side_effect=mock_fetch_contacts_by_account_ids,
    )
    async def test_should_increment_existing_activation_to_opportunity_created_status_when_opportunity_is_created_under_previously_activated_account(
        self, mock_sobject_fetch, mock_fetch_contact_composite, mock_fetch_contacts_by_account_ids
    ):
        with self.app.app_context():
            # setup mock api responses for one account activated via meeting set and another via opportunity created
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

            meeting_set_activation: Activation = next(
                a for a in activations if a["status"] == "Meeting Set"
            )

            mock_contacts_for_more_tasks = [
                Contact(
                    id=contact_id,
                    first_name="FirstName",
                    last_name="LastName",
                    account_id=meeting_set_activation["account"]["id"],
                    account=Account(
                        id=meeting_set_activation["account"]["id"],
                        name="Mock Account Name"
                    )
                )
                for contact_id in meeting_set_activation["active_contact_ids"]
            ]
                
            set_mock_contacts_for_map(get_mock_contacts_for_map()+mock_contacts_for_more_tasks)
            # setup mock api response to return an opportunity for the account activated via meeting set
            mock_opportunity = get_mock_opportunity_for_account(
                meeting_set_activation["account"]["id"]
            )
            # increment flow
            add_mock_response(
                "fetch_opportunities_by_account_ids_from_date",
                [mock_opportunity],
            )
            # new activation flow
            add_mock_response(
                "fetch_opportunities_by_account_ids_from_date",
                [],
            )
            # unresponsive flow
            add_mock_response("fetch_events_by_contact_ids_from_date", [])
            # activation flow
            add_mock_response("fetch_events_by_contact_ids_from_date", [])
            mock_tasks = (
                get_n_mock_tasks_per_contact_for_contains_content_crieria_query(
                    1, mock_contacts_for_more_tasks, mock_user_id
                )
            )
            for mock_task in mock_tasks:
                mock_task["Id"] = str(uuid.uuid4())

            # unresponsive flow
            add_mock_response(
                "fetch_all_matching_tasks",
                mock_tasks,
            )
            # increment flow
            add_mock_response(
                "fetch_all_matching_tasks",
                mock_tasks,
            )
            # activation flow
            add_mock_response(
                "fetch_all_matching_tasks",
                mock_tasks,
            )
            updated_activations = await assert_and_return_payload_async(
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
