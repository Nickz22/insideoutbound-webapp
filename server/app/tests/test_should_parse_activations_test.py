import unittest, json, os, sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from unittest.mock import patch
from typing import List
from datetime import datetime
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
from app import create_app
from app.tests.c import (
    mock_tasks_for_criteria_with_contains_content,
    mock_tasks_for_criteria_with_unique_values_content,
)
from app.tests.mocks import (
    MOCK_ACCOUNT_IDS,
    add_mock_response,
    clear_mocks,
    response_based_on_query,
    get_n_mock_contacts_for_account,
    get_three_mock_tasks_per_two_contacts_for_contains_content_criteria_query,
    get_thirty_mock_tasks_across_ten_contacts_for_contains_content_criteria_query,
    get_thirty_mock_tasks_across_ten_contacts_for_unique_values_content_criteria_query,
    get_ten_mock_contacts_spread_across_five_accounts,
    get_mock_opportunity_for_account,
    get_five_mock_accounts
)

mock_user_id = "mock_user_id"


@patch("app.salesforce_api._fetch_sobjects_async")
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
            instance_url="https://mock_instance_url.com",
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
        self.assertTrue(
            exactly_one_opportunity_created_prospecting_effort_for_opportunity
        )

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
            len(
                opportunity_prospecting_effort_for_opportunity_created_status[
                    "task_ids"
                ]
            ),
            1,
        )
        
    @patch("requests.get")
    def test_should_update_activation_status_to_opportunity_created_without_additional_task(
        self, mock_sobject_fetch
    ):
        # Set up the initial activation
        self.setup_one_activity_per_contact_with_staggered_created_dates_and_one_event_under_a_single_account_and_one_opportunity_for_a_different_account()
        mock_sobject_fetch.side_effect = response_based_on_query

        initial_activations = self.assert_and_return_payload(
            self.client.post("/fetch_prospecting_activity", headers=self.api_header)
        )[0].get("raw_data")

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
        updated_activations = self.assert_and_return_payload(
            self.client.post("/fetch_prospecting_activity", headers=self.api_header)
        )[0].get("raw_data")

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
        self.assertIsNotNone(updated_activation, "The activation should still exist")
        self.assertEqual(
            updated_activation["status"],
            "Opportunity Created",
            "Status should be 'Opportunity Created'",
        )
        self.assertEqual(
            updated_activation["opportunity"]["amount"],
            6969.42,
            "Opportunity amount should be updated",
        )

        # Check that no new prospecting effort was added
        self.assertEqual(
            len(updated_activation["prospecting_effort"]),
            len(meeting_set_activation["prospecting_effort"]),
            "No new prospecting effort should be added",
        )

    # helpers

    def assert_and_return_payload(self, test_api_response):
        payload = json.loads(test_api_response.data)
        self.assertEqual(test_api_response.status_code, 200, payload["message"])
        return payload["data"]

    async def assert_and_return_payload_async(self, test_api_response):
        response = await test_api_response
        payload = json.loads(response.data)
        self.assertEqual(response.status_code, 200, payload["message"])
        return payload["data"][0]["raw_data"]

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
