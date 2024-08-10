import unittest, json, os, sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from unittest.mock import patch
from typing import List
from datetime import datetime, timedelta

from app.data_models import (
    Activation,
    ProspectingMetadata,
    ProspectingEffort,
    SettingsModel,
    FilterContainerModel,
    FilterModel,
    TokenData,
    TableColumn,
    DataType,
)
from app.database.supabase_connection import get_supabase_admin_client
from app.database.dml import save_session, delete_session
from server import app
from server.app import create_app
from app.database.activation_selector import (
    load_active_activations_order_by_first_prospecting_activity_asc,
    load_inactive_activations,
)
from app.database.dml import upsert_activations
from app.utils import add_days, group_by
from app.tests.c import (
    mock_tasks_for_criteria_with_contains_content,
    mock_tasks_for_criteria_with_unique_values_content,
)
from app.tests.mocks import (
    MOCK_CONTACT_IDS,
    MOCK_ACCOUNT_IDS,
    add_mock_response,
    clear_mocks,
    response_based_on_query,
    get_n_mock_contacts_for_account,
    get_three_mock_tasks_per_two_contacts_for_contains_content_criteria_query,
    get_one_mock_task_per_contact_for_contains_content_criteria_query,
    get_thirty_mock_tasks_across_ten_contacts_for_contains_content_criteria_query,
    get_thirty_mock_tasks_across_ten_contacts_for_unique_values_content_criteria_query,
    get_ten_mock_contacts_spread_across_five_accounts,
    get_mock_opportunity_for_account,
    get_mock_event_for_contact,
    get_five_mock_accounts,
    get_two_mock_contacts_per_account,
    get_one_mock_task_per_contact_for_contains_content_criteria_query_x,
)

mock_user_id = "mock_user_id"


class TestActivationLogic(unittest.TestCase):

    api_header = None

    def setUp(self):
        os.environ["FLASK_ENV"] = "testing"
        self.app = create_app()
        self.app.testing = True
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()

        self.setup_mock_user()
        # save dummy access tokens because the OAuth flow is pretty hard to write a test for right now
        mock_token_data = TokenData(
            access_token="mock_access_token",
            refresh_token="mock_refresh_token",
            instance_url="mock_instance_url",
            id=mock_user_id,
            token_type="mock_token_type",
            issued_at="mock_issued_at",
        )
        self.api_header = {"X-Session-Token": save_session(mock_token_data, True)}

        self.do_onboarding_flow()
        settings_model = self.fetch_settings_model_from_db()

        self.assertEqual(settings_model.activitiesPerContact, 3)
        self.assertEqual(settings_model.contactsPerAccount, 2)
        self.assertEqual(settings_model.trackingPeriod, 5)
        self.assertEqual(settings_model.activateByMeeting, True)
        self.assertEqual(settings_model.activateByOpportunity, True)
        self.assertEqual(settings_model.inactivityThreshold, 10)
        self.assertEqual(settings_model.meetingObject, "Event")
        self.assertEqual(settings_model.meetingsCriteria.name, "Meetings")
        self.assertEqual(settings_model.meetingsCriteria.filterLogic, "1")
        self.assertEqual(len(settings_model.criteria), 2)
        contains_content_criteria = settings_model.criteria[0]
        self.assertEqual(contains_content_criteria.name, "Contains Content")
        self.assertEqual(contains_content_criteria.filterLogic, "1 AND 2 AND 3 AND 4")
        self.assertEqual(contains_content_criteria.direction, "inbound")
        unique_content_criteria = settings_model.criteria[1]
        self.assertEqual(unique_content_criteria.name, "Unique Content")
        self.assertEqual(unique_content_criteria.filterLogic, "((1 OR 2) AND 3)")
        self.assertEqual(unique_content_criteria.direction, "outbound")
        contains_content_filters = contains_content_criteria.filters
        unique_content_filters = unique_content_criteria.filters
        # Assuming FilterModel instances are in contains_content_filters list
        subject_filters = [
            f
            for f in contains_content_filters
            if f.field == "Subject"
            and f.operator == "contains"
            and f.value in ["task", "subject"]
        ]

        status_filters = [
            f
            for f in contains_content_filters
            if f.field == "Status"
            and f.operator == "contains"
            and f.value in ["Mock", "Status"]
        ]

        # Assert that exactly two FilterModel instances match the criteria
        assert (
            len(subject_filters) == 2
        ), "There should be exactly two FilterModels with field='Subject' and operator='contains' and value of 'mock' or 'subject'"
        assert (
            len(status_filters) == 2
        ), "There should be exactly two FilterModels with field='Status' and operator='contains' and value of 'mock' or 'status'"

        # Assuming FilterModel instances are in unique_content_filters list
        status_filters = [
            f
            for f in unique_content_filters
            if f.field == "Status"
            and f.operator == "contains"
            and f.value in ["Unique", "Other"]
        ]

        subject_filters = [
            f
            for f in unique_content_filters
            if f.field == "Subject"
            and f.operator == "contains"
            and f.value in ["Unique Subject"]
        ]

        # Assert that exactly two FilterModel instances match the criteria
        assert (
            len(status_filters) == 2
        ), "There should be exactly two FilterModels with field='Status' and operator='contains' and value of 'Unique' or 'Other'"
        assert (
            len(subject_filters) == 1
        ), "There should be exactly one FilterModel with field='Subject' and operator='contains' and value of 'Unique Subject'"

    def tearDown(self):
        delete_session(self.api_header["X-Session-Token"])
        supabase = get_supabase_admin_client()
        supabase.table("Activations").delete().in_(
            "activated_by_id", [mock_user_id]
        ).execute()
        self.app_context.pop()
        # clear any mock api responses setup by last test
        clear_mocks()

    @patch("requests.get")
    def test_should_create_new_activation_when_sufficient_prospecting_activities_are_in_salesforce(
        self, mock_sobject_fetch
    ):

        self.setup_thirty_tasks_across_ten_contacts_and_five_accounts()

        mock_sobject_fetch.side_effect = response_based_on_query
        activations = self.assert_and_return_payload(
            self.client.post("/fetch_prospecting_activity", headers=self.api_header)
        )[0]["raw_data"]

        self.assertEqual(5, len(activations))
        self.assertTrue(
            any(
                activation["status"] == "Opportunity Created"
                for activation in activations
            ),
            "No Activation with Status 'Opportunity Created' found",
        )

    @patch("requests.get")
    def test_should_create_new_activation_when_one_activity_per_contact_and_one_meeting_or_one_opportunity_is_in_salesforce(
        self, mock_sobject_fetch
    ):
        # setup mock api responses
        self.setup_one_activity_per_contact_with_staggered_created_dates_and_one_event_under_a_single_account_and_one_opportunity_for_a_different_account()

        mock_sobject_fetch.side_effect = response_based_on_query
        activations = self.assert_and_return_payload(
            self.client.post("/fetch_prospecting_activity", headers=self.api_header)
        )[0].get("raw_data")
        self.assertEqual(2, len(activations))

        # Isolate activations with specific statuses
        meeting_set_activation: Activation = [
            activation
            for activation in activations
            if activation["status"] == "Meeting Set"
        ][0]

        self.assertEqual(len(meeting_set_activation["event_ids"]), 1)

        opportunity_created_activation: Activation = [
            activation
            for activation in activations
            if activation["status"] == "Opportunity Created"
        ][0]

        self.assertEqual(
            opportunity_created_activation["opportunity"]["amount"], 1733.42
        )

        # Check if there are any activations with the status "Meeting Set"
        self.assertIsNotNone(
            meeting_set_activation, "No Activation with Status 'Meeting Set' found"
        )

        # Check if there are any activations with the status "Opportunity Created"
        self.assertIsNotNone(
            opportunity_created_activation,
            "No Activation with Status 'Opportunity Created' found",
        )

        meeting_set_prospecting_metadata: ProspectingMetadata = meeting_set_activation[
            "prospecting_metadata"
        ]
        self.assertEqual(len(meeting_set_prospecting_metadata), 1)
        self.assertEqual(
            meeting_set_prospecting_metadata[0]["name"], "Contains Content"
        )
        self.assertEqual(meeting_set_prospecting_metadata[0]["total"], 2)

        ## check that the prospecting metadata have staggered first and last occurrence dates
        first_date = datetime.strptime(
            meeting_set_prospecting_metadata[0]["first_occurrence"], "%Y-%m-%d"
        )
        last_date = datetime.strptime(
            meeting_set_prospecting_metadata[0]["last_occurrence"], "%Y-%m-%d"
        )

        self.assertEqual((last_date - first_date).days, 1)

        opportunity_created_prospecting_metadata: ProspectingMetadata = (
            opportunity_created_activation["prospecting_metadata"]
        )
        self.assertEqual(len(opportunity_created_prospecting_metadata), 1)
        self.assertEqual(
            opportunity_created_prospecting_metadata[0]["name"], "Contains Content"
        )
        self.assertEqual(opportunity_created_prospecting_metadata[0]["total"], 2)

        first_date = datetime.strptime(
            opportunity_created_prospecting_metadata[0]["first_occurrence"], "%Y-%m-%d"
        )
        last_date = datetime.strptime(
            opportunity_created_prospecting_metadata[0]["last_occurrence"], "%Y-%m-%d"
        )

        self.assertEqual((last_date - first_date).days, 1)

                ## the event will have 2 prospecting efforts because the Tasks under the same Activation
        ## were created before the Event...if no Tasks are created while the Activation is in a certain Status
        ### the Activation won't get a Prospecting Effort created for that status
        meeting_set_activation_prospecting_effort: List[ProspectingEffort] = (
            meeting_set_activation["prospecting_effort"]
        )
        
        self.assertEqual(len(meeting_set_activation_prospecting_effort), 2)
        
        meeting_prospecting_effort_for_activated_status = [
            pe
            for pe in meeting_set_activation_prospecting_effort
            if pe["status"] == "Activated"
        ]
        meeting_prospecting_effort_for_engaged_status = [
            pe
            for pe in meeting_set_activation_prospecting_effort
            if pe["status"] == "Engaged"
        ]
        
        exactly_one_activated_prospecting_effort_for_activated_status = (
            len(meeting_prospecting_effort_for_activated_status) == 1
        )
        self.assertTrue(exactly_one_activated_prospecting_effort_for_activated_status)
        
        exactly_one_engaged_prospecting_effort_for_engaged_status = (
            len(meeting_prospecting_effort_for_engaged_status) == 1
        )
        self.assertTrue(exactly_one_engaged_prospecting_effort_for_engaged_status)
        
        meeting_prospecting_effort_for_activated_status = (
            meeting_prospecting_effort_for_activated_status[0]
        )
        
        ## Since the activating Task was "Inbound", the activation was immediately set to "Engaged" and no
        ### no Tasks were attributed to the "Activated" status
        self.assertEqual(
            len(meeting_prospecting_effort_for_activated_status["task_ids"]), 0
        )
        
        meeting_prospecting_effort_for_engaged_status = (
            meeting_prospecting_effort_for_engaged_status[0]
        )
        self.assertEqual(
            len(meeting_prospecting_effort_for_engaged_status["task_ids"]), 2
        )
        
        ## the opportunity will have 3 prospecting efforts because
        ### it has tasks spanning the "Engaged" and "Opportunity Created" statuses - "Activated" status automatically gets a prospecting effort
        
        opportunity_created_activation_prospecting_effort: List[ProspectingEffort] = (
            opportunity_created_activation["prospecting_effort"]
        )
        self.assertEqual(len(opportunity_created_activation_prospecting_effort), 3)
        
        opportunity_prospecting_effort_for_activated_status = [
            pe
            for pe in opportunity_created_activation_prospecting_effort
            if pe["status"] == "Activated"
        ]
        opportunity_prospecting_effort_for_engaged_status = [
            pe
            for pe in opportunity_created_activation_prospecting_effort
            if pe["status"] == "Engaged"
        ]
        opportunity_prospecting_effort_for_opportunity_created_status = [
            pe
            for pe in opportunity_created_activation_prospecting_effort
            if pe["status"] == "Opportunity Created"
        ]
        
        exactly_one_activated_prospecting_effort_for_opportunity = (
            len(opportunity_prospecting_effort_for_activated_status) == 1
        )
        self.assertTrue(exactly_one_activated_prospecting_effort_for_opportunity)
        
        exactly_one_engaged_prospecting_effort_for_opportunity = (
            len(opportunity_prospecting_effort_for_engaged_status) == 1
        )
        self.assertTrue(exactly_one_engaged_prospecting_effort_for_opportunity)
        
        exactly_one_opportunity_created_prospecting_effort_for_opportunity = (
            len(opportunity_prospecting_effort_for_opportunity_created_status) == 1
        )
        self.assertTrue(exactly_one_opportunity_created_prospecting_effort_for_opportunity)
        
        opportunity_prospecting_effort_for_activated_status = (
            opportunity_prospecting_effort_for_activated_status[0]
        )
        ## Since the activating Task was "Inbound", the activation was immediately set to "Engaged" and
        ### no Tasks were attributed to the "Activated" status
        self.assertEqual(
            len(opportunity_prospecting_effort_for_activated_status["task_ids"]), 0
        )
        
        ## Since one of the activating Tasks was created before the Opportunity, it was attributed to the "Engaged" status
        opportunity_prospecting_effort_for_engaged_status = (
            opportunity_prospecting_effort_for_engaged_status[0]
        )
        
        self.assertEqual(
            len(opportunity_prospecting_effort_for_engaged_status["task_ids"]), 1
        )
        
        ## Since one of the activating Tasks was created after the Opportunity, it was attributed to the "Opportunity Created" status
        opportunity_prospecting_effort_for_opportunity_created_status = (
            opportunity_prospecting_effort_for_opportunity_created_status[0]
        )
        self.assertEqual(
            len(opportunity_prospecting_effort_for_opportunity_created_status["task_ids"]), 1
        )
        
        
        
        

    # @patch("requests.get")
    # def test_should_increment_existing_activation_to_opportunity_created_status_when_opportunity_is_created_under_previously_activated_account(
    #     self, mock_sobject_fetch
    # ):
    #     # setup mock api responses for one account activated via meeting set and another via opportunity created
    #     self.setup_one_activity_per_contact_with_staggered_created_dates_and_one_event_under_a_single_account_and_one_opportunity_for_a_different_account()
    #     mock_sobject_fetch.side_effect = response_based_on_query

    #     activations = self.assert_and_return_payload(
    #         self.client.post("/fetch_prospecting_activity", headers=self.api_header)
    #     )

    #     meeting_set_activation = next(
    #         a for a in activations if a["status"] == "Meeting Set"
    #     )

    #     add_mock_response("fetch_contacts_by_account_ids", [])
    #     add_mock_response(
    #         "fetch_opportunities_by_account_ids_from_date",
    #         [get_mock_opportunity_for_account(meeting_set_activation["account"]["id"])],
    #     )
    #     add_mock_response("fetch_contacts_by_account_ids", [])
    #     add_mock_response(
    #         "fetch_events_by_account_ids_from_date",
    #         [],
    #     )
    #     add_mock_response("fetch_accounts_not_in_ids", [])

    #     increment_activations_response = self.client.post(
    #         "/fetch_prospecting_activity", headers=self.api_header
    #     )
    #     payload = json.loads(increment_activations_response.data)
    #     self.assertEqual(
    #         increment_activations_response.status_code, 200, payload["message"]
    #     )

    #     self.assertTrue(
    #         any(
    #             activation["status"] == "Opportunity Created"
    #             and activation["event_ids"]
    #             for activation in payload["data"]
    #         ),
    #         "No Activation with Status 'Opportunity Created' and non-empty 'event_ids' found",
    #     )

    # @patch("requests.get")
    # def test_should_set_activations_without_prospecting_activities_past_inactivity_threshold_as_unresponsive(
    #     self, mock_sobject_fetch
    # ):
    #     # setup mock api responses
    #     self.setup_thirty_tasks_across_ten_contacts_and_five_accounts()

    #     mock_sobject_fetch.side_effect = response_based_on_query
    #     self.assert_and_return_payload(
    #         self.client.post("/fetch_prospecting_activity", headers=self.api_header)
    #     )

    #     activations = (
    #         load_active_activations_order_by_first_prospecting_activity_asc().data
    #     )
    #     self.assertEqual(5, len(activations))

    #     activation = activations[0]
    #     activation.last_prospecting_activity = add_days(
    #         activation.last_prospecting_activity, -11
    #     )
    #     upsert_activations([activation])

    #     self.setup_zero_new_prospecting_activities_and_zero_new_opportunities_and_zero_new_events()

    #     self.assert_and_return_payload(
    #         self.client.post("/fetch_prospecting_activity", headers=self.api_header)
    #     )

    #     inactive_activations = load_inactive_activations().data

    #     self.assertEqual(1, len(inactive_activations))

    # @patch("requests.get")
    # def test_should_create_new_activations_for_previously_activated_accounts_after_inactivity_threshold_is_reached(
    #     self, mock_sobject_fetch
    # ):
    #     # setup mock api responses
    #     self.setup_thirty_tasks_across_ten_contacts_and_five_accounts()
    #     mock_sobject_fetch.side_effect = response_based_on_query
    #     # initial account activation
    #     self.assert_and_return_payload(
    #         self.client.post("/fetch_prospecting_activity", headers=self.api_header)
    #     )

    #     activations = (
    #         load_active_activations_order_by_first_prospecting_activity_asc().data
    #     )

    #     self.assertEqual(5, len(activations))

    #     # set last_prospecting_activity of first activation to 1 day over threshold
    #     activation = activations[0]
    #     activation.last_prospecting_activity = add_days(
    #         activation.last_prospecting_activity, -11
    #     )
    #     upsert_activations([activation])

    #     # setup no prospecting activity to come back from Salesforce to force inactivation of Activation
    #     self.setup_zero_new_prospecting_activities_and_zero_new_opportunities_and_zero_new_events()

    #     # inactivate the Accounts
    #     self.assert_and_return_payload(
    #         self.client.post("/fetch_prospecting_activity", headers=self.api_header)
    #     )

    #     inactive_activations = load_inactive_activations().data

    #     self.assertEqual(1, len(inactive_activations))
    #     self.assertEqual(inactive_activations[0].id, activation.id)

    #     # setup prospecting activities to come back from Salesforce on the new attempt
    #     self.setup_six_tasks_across_two_contacts_and_one_account(
    #         inactive_activations[0].account.id
    #     )

    #     # assert that new activations are created for the previously activated accounts
    #     self.assert_and_return_payload(
    #         self.client.post("/fetch_prospecting_activity", headers=self.api_header)
    #     )

    #     active_activations = (
    #         load_active_activations_order_by_first_prospecting_activity_asc().data
    #     )

    #     is_inactive_account_reactivated = any(
    #         activation.account.id == inactive_activations[0].account.id
    #         for activation in active_activations
    #     )

    #     self.assertTrue(is_inactive_account_reactivated)

    # helpers

    def assert_and_return_payload(self, test_api_response):
        payload = json.loads(test_api_response.data)
        self.assertEqual(test_api_response.status_code, 200, payload["message"])
        return payload["data"]

    def setup_zero_new_prospecting_activities_and_zero_new_opportunities_and_zero_new_events(
        self,
    ):
        add_mock_response("fetch_contacts_by_account_ids", [])
        add_mock_response("fetch_opportunities_by_account_ids_from_date", [])
        add_mock_response("fetch_events_by_account_ids_from_date", [])
        add_mock_response("fetch_accounts_not_in_ids", [])
        add_mock_response("fetch_contacts_by_account_ids", [])
        add_mock_response("fetch_contacts_by_account_ids", [])

    def setup_six_tasks_across_two_contacts_and_one_account(self, account_id):
        add_mock_response(
            "contains_content_criteria_query",
            get_three_mock_tasks_per_two_contacts_for_contains_content_criteria_query(
                mock_user_id
            ),
        )
        add_mock_response("unique_values_content_criteria_query", [])
        add_mock_response(
            "fetch_accounts_not_in_ids",
            get_five_mock_accounts(),
        )
        add_mock_response(
            "fetch_contacts_by_account_ids",
            get_n_mock_contacts_for_account(2, account_id),
        )
        add_mock_response(
            "fetch_contacts_by_account_ids",
            get_n_mock_contacts_for_account(2, account_id),
        )
        add_mock_response(
            "contains_content_criteria_query",
            get_three_mock_tasks_per_two_contacts_for_contains_content_criteria_query(
                mock_user_id
            ),
        )
        add_mock_response("unique_values_content_criteria_query", [])
        add_mock_response(
            "fetch_contacts_by_ids_and_non_null_accounts",
            get_n_mock_contacts_for_account(2, account_id),
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
            get_n_mock_contacts_for_account(2, account_id),
        )
        add_mock_response(
            "fetch_contacts_by_account_ids",
            get_n_mock_contacts_for_account(2, account_id),
        )

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

    def setup_mock_user(self):
        add_mock_response("fetch_logged_in_salesforce_user", {"Id": mock_user_id})

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

        self.assertEqual(unique_values_content_filter_model.filterLogic, "")

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
        self.assertEqual(response.status_code, 200, response.data)

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

    def fetch_settings_model_from_db(self) -> SettingsModel:
        """
        gets settings json from file db and converts it to a SettingsModel object
        """
        get_settings_response = self.client.get(
            "/get_settings", headers=self.api_header
        )
        self.assertEqual(
            get_settings_response.status_code, 200, get_settings_response.data
        )
        settings_model = SettingsModel(
            **(json.loads(get_settings_response.data)["data"][0])
        )

        return settings_model
