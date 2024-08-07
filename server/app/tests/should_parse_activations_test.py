import unittest, json, sys, os
from unittest.mock import patch

os.environ["APP_ENV"] = "test"
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from app.data_models import SettingsModel, FilterContainerModel, FilterModel, TokenData
from app import app
from app.database.supabase_connection import save_session
from app.database.activation_selector import (
    load_active_activations_order_by_first_prospecting_activity_asc,
    load_inactive_activations,
)
from app.database.dml import upsert_activations
from app.utils import add_days
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
)


class TestActivationLogic(unittest.TestCase):
    def setUp(self):

        # create empty test_activations.json file in the root directory
        with open("test_activations.json", "w") as f:
            f.write("[]")

        # save dummy access tokens because the OAuth flow is pretty hard to write a test for right now
        mock_token_data: TokenData = TokenData(
            access_token="mock_access_token",
            refresh_token="mock_refresh_token",
            instance_url="mock_instance_url",
            id="mock_id",
            token_type="mock_token_type",
            issued_at="mock_issued_at",
        )
        session_id = save_session(mock_token_data, True)

        # Creates a test client
        self.app = app.test_client()
        # Propagate the exceptions to the test client
        self.app.testing = True

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
        self.assertEqual(settings_model.criteria[0].name, "Contains Content")
        self.assertEqual(settings_model.criteria[0].filterLogic, "1 AND 2 AND 3 AND 4")
        contains_content_filters = [
            FilterModel(**f) for f in settings_model.criteria[0].filters
        ]
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

        self.assertEqual(settings_model.criteria[1].name, "Unique Content")
        self.assertEqual(settings_model.criteria[1].filterLogic, "((1 OR 2) AND 3)")

        # assert the filters of the Unique Content filter container
        unique_content_filters = [
            FilterModel(**f) for f in settings_model.criteria[1].filters
        ]
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
        # clear any mock api responses setup by last test
        clear_mocks()
        # clear any activations from last test
        with open("test_activations.json", "w") as f:
            f.write("[]")

    @patch("requests.get")
    def test_should_create_new_activation_when_sufficient_prospecting_activities_are_in_salesforce(
        self, mock_sobject_fetch
    ):

        self.setup_thirty_tasks_across_ten_contacts_and_five_accounts()

        mock_sobject_fetch.side_effect = response_based_on_query
        activations = self.assert_and_return_payload(
            self.app.get("/fetch_prospecting_activity")
        )

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
        self.setup_one_activity_per_contact_and_one_event_under_a_single_account_and_one_opportunity_for_a_different_account()

        mock_sobject_fetch.side_effect = response_based_on_query
        activations = self.assert_and_return_payload(
            self.app.get("/fetch_prospecting_activity")
        )
        self.assertEqual(2, len(activations))

        any_meeting_set = any(
            activation["status"] == "Meeting Set" for activation in activations
        )
        self.assertTrue(
            any_meeting_set, "No Activation with Status 'Meeting Set' found"
        )

        any_opportunity_created = any(
            activation["status"] == "Opportunity Created" for activation in activations
        )
        self.assertTrue(
            any_opportunity_created,
            "No Activation with Status 'Opportunity Created' found",
        )

    @patch("requests.get")
    def test_should_increment_existing_activation_to_opportunity_created_status_when_opportunity_is_created_under_previously_activated_account(
        self, mock_sobject_fetch
    ):
        # setup mock api responses for one account activated via meeting set and another via opportunity created
        self.setup_one_activity_per_contact_and_one_event_under_a_single_account_and_one_opportunity_for_a_different_account()
        mock_sobject_fetch.side_effect = response_based_on_query

        activations = self.assert_and_return_payload(
            self.app.get("/fetch_prospecting_activity")
        )

        meeting_set_activation = next(
            a for a in activations if a["status"] == "Meeting Set"
        )

        add_mock_response("fetch_contacts_by_account_ids", [])
        add_mock_response(
            "fetch_opportunities_by_account_ids_from_date",
            [get_mock_opportunity_for_account(meeting_set_activation["account"]["id"])],
        )
        add_mock_response("fetch_contacts_by_account_ids", [])
        add_mock_response(
            "fetch_events_by_account_ids_from_date",
            [],
        )
        add_mock_response("fetch_accounts_not_in_ids", [])

        increment_activations_response = self.app.get("/fetch_prospecting_activity")
        payload = json.loads(increment_activations_response.data)
        self.assertEqual(
            increment_activations_response.status_code, 200, payload["message"]
        )

        self.assertTrue(
            any(
                activation["status"] == "Opportunity Created"
                and activation["event_ids"]
                for activation in payload["data"]
            ),
            "No Activation with Status 'Opportunity Created' and non-empty 'event_ids' found",
        )

    @patch("requests.get")
    def test_should_set_activations_without_prospecting_activities_past_inactivity_threshold_as_unresponsive(
        self, mock_sobject_fetch
    ):
        # setup mock api responses
        self.setup_thirty_tasks_across_ten_contacts_and_five_accounts()

        mock_sobject_fetch.side_effect = response_based_on_query
        self.assert_and_return_payload(self.app.get("/fetch_prospecting_activity"))

        activations = (
            load_active_activations_order_by_first_prospecting_activity_asc().data
        )
        self.assertEqual(5, len(activations))

        activation = activations[0]
        activation.last_prospecting_activity = add_days(
            activation.last_prospecting_activity, -11
        )
        upsert_activations([activation])

        self.setup_zero_new_prospecting_activities_and_zero_new_opportunities_and_zero_new_events()

        self.assert_and_return_payload(self.app.get("/fetch_prospecting_activity"))

        inactive_activations = load_inactive_activations().data

        self.assertEqual(1, len(inactive_activations))

    @patch("requests.get")
    def test_should_create_new_activations_for_previously_activated_accounts_after_inactivity_threshold_is_reached(
        self, mock_sobject_fetch
    ):
        # setup mock api responses
        self.setup_thirty_tasks_across_ten_contacts_and_five_accounts()
        mock_sobject_fetch.side_effect = response_based_on_query
        # initial account activation
        self.assert_and_return_payload(self.app.get("/fetch_prospecting_activity"))

        activations = (
            load_active_activations_order_by_first_prospecting_activity_asc().data
        )

        self.assertEqual(5, len(activations))

        # set last_prospecting_activity of first activation to 1 day over threshold
        activation = activations[0]
        activation.last_prospecting_activity = add_days(
            activation.last_prospecting_activity, -11
        )
        upsert_activations([activation])

        # setup no prospecting activity to come back from Salesforce to force inactivation of Activation
        self.setup_zero_new_prospecting_activities_and_zero_new_opportunities_and_zero_new_events()

        # inactivate the Accounts
        self.assert_and_return_payload(self.app.get("/fetch_prospecting_activity"))

        inactive_activations = load_inactive_activations().data

        self.assertEqual(1, len(inactive_activations))
        self.assertEqual(inactive_activations[0].id, activation.id)

        # setup prospecting activities to come back from Salesforce on the new attempt
        self.setup_six_tasks_across_two_contacts_and_one_account(
            inactive_activations[0].account.id
        )

        # assert that new activations are created for the previously activated accounts
        self.assert_and_return_payload(self.app.get("/fetch_prospecting_activity"))

        active_activations = (
            load_active_activations_order_by_first_prospecting_activity_asc().data
        )

        is_inactive_account_reactivated = any(
            activation.account.id == inactive_activations[0].account.id
            for activation in active_activations
        )

        self.assertTrue(is_inactive_account_reactivated)

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
            get_three_mock_tasks_per_two_contacts_for_contains_content_criteria_query(),
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
            get_three_mock_tasks_per_two_contacts_for_contains_content_criteria_query(),
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
            get_thirty_mock_tasks_across_ten_contacts_for_contains_content_criteria_query(),
        )
        add_mock_response(
            "unique_values_content_criteria_query",
            get_thirty_mock_tasks_across_ten_contacts_for_unique_values_content_criteria_query(),
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

    def setup_one_activity_per_contact_and_one_event_under_a_single_account_and_one_opportunity_for_a_different_account(
        self,
    ):
        add_mock_response(
            "contains_content_criteria_query",
            get_one_mock_task_per_contact_for_contains_content_criteria_query(),
        )
        add_mock_response("unique_values_content_criteria_query", [])
        add_mock_response(
            "fetch_contacts_by_ids_and_non_null_accounts",
            get_ten_mock_contacts_spread_across_five_accounts(),
        )
        add_mock_response("fetch_accounts_not_in_ids", get_five_mock_accounts())
        add_mock_response(
            "fetch_opportunities_by_account_ids_from_date",
            [get_mock_opportunity_for_account(MOCK_ACCOUNT_IDS[0])],
        )
        add_mock_response(
            "fetch_events_by_account_ids_from_date",
            [get_mock_event_for_contact(MOCK_CONTACT_IDS[3])],
        )
        add_mock_response(
            "fetch_contacts_by_account_ids",
            get_ten_mock_contacts_spread_across_five_accounts(),
        )
        add_mock_response(
            "fetch_contacts_by_account_ids",
            get_ten_mock_contacts_spread_across_five_accounts(),
        )

    def do_onboarding_flow(self):
        """
        constructs a settings model and saves it via the save_settings API
        """

        contains_content_filter_model = (
            self.get_filter_container_via_tasks_from_generate_filters_api(
                mock_tasks_for_criteria_with_contains_content
            )
        )
        contains_content_filter_model.name = "Contains Content"

        unique_values_content_filter_model = (
            self.get_filter_container_via_tasks_from_generate_filters_api(
                mock_tasks_for_criteria_with_unique_values_content
            )
        )
        unique_values_content_filter_model.name = "Unique Content"

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

        response = self.app.post(
            "/save_settings",
            data=json.dumps(post_data),
            content_type="application/json",
        )

        # assert response status code is 200
        self.assertEqual(response.status_code, 200, response.data)

    def get_filter_container_via_tasks_from_generate_filters_api(
        self, tasks
    ) -> FilterContainerModel:
        """
        Hits the `/generate_filters` endpoint with the given tasks and returns the FilterContainerModel
        """
        response = self.app.post(
            "/generate_filters",
            data=json.dumps({"tasks": tasks}),
            content_type="application/json",
        )
        response_json = json.loads(response.data.decode())["data"]
        response_json["filters"] = [
            FilterModel(**filter) for filter in response_json["filters"]
        ]

        return FilterContainerModel(**response_json)

    def fetch_settings_model_from_db(self) -> SettingsModel:
        """
        gets settings json from file db and converts it to a SettingsModel object
        """
        get_settings_response = self.app.get("/get_settings")
        self.assertEqual(
            get_settings_response.status_code, 200, get_settings_response.data
        )
        settings_model = SettingsModel(**json.loads(get_settings_response.data))
        settings_model.criteria = [
            FilterContainerModel(**criteria) for criteria in settings_model.criteria
        ]
        settings_model.meetingsCriteria = FilterContainerModel(
            **settings_model.meetingsCriteria
        )

        return settings_model
