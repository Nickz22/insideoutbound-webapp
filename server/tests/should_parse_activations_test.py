import unittest, json, sys, os
from unittest.mock import patch, MagicMock

os.environ["APP_ENV"] = "test"
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from server.models import SettingsModel, FilterContainerModel, FilterModel
from server.app import app
from server.cache import save_tokens
from server.tests.c import (
    mock_tasks_for_criteria_with_contains_content,
    mock_tasks_for_criteria_with_unique_values_content,
)
from server.tests.mocks import (
    set_mock_response_by_request_key,
    clear_mocks,
    response_based_on_query,
    get_one_mock_task_per_contact_for_contains_content_criteria_query,
    get_thirty_mock_tasks_across_ten_contacts_for_contains_content_criteria_query,
    get_thirty_mock_tasks_across_ten_contacts_for_unique_values_content_criteria_query,
    get_ten_mock_contacts_spread_across_five_accounts,
    get_mock_opportunity_for_account,
    get_mock_event_for_account,
)

##
### Run an activation test and assert that the mock response handler is running
### Then, start to mock responses to
# (1) create an activation,
# (2) increment the same activation,
# (3) set the same activation as unresponsive and
# (4) create a new activation in accordance with inactivity_threshold
##


class TestActivationLogic(unittest.TestCase):
    def setUp(self):

        # create empty test_activations.json file in the root directory
        with open("test_activations.json", "w") as f:
            f.write("[]")

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

        # setup mock api responses
        set_mock_response_by_request_key(
            "contains_content_criteria_query",
            get_thirty_mock_tasks_across_ten_contacts_for_contains_content_criteria_query(),
        )
        set_mock_response_by_request_key(
            "unique_values_content_criteria_query",
            get_thirty_mock_tasks_across_ten_contacts_for_unique_values_content_criteria_query(),
        )
        set_mock_response_by_request_key(
            "fetch_contacts_by_account_ids",
            get_ten_mock_contacts_spread_across_five_accounts(),
        )
        set_mock_response_by_request_key(
            "fetch_opportunities_by_account_ids_from_date",
            [get_mock_opportunity_for_account()],
        )
        set_mock_response_by_request_key("fetch_events_by_account_ids_from_date", [])

        save_tokens("test_access_token", "test_instance_url")
        mock_sobject_fetch.side_effect = response_based_on_query
        load_prospecting_activities_response = self.app.get(
            "/load_prospecting_activities"
        )

        payload = json.loads(load_prospecting_activities_response.data)
        self.assertEqual(
            load_prospecting_activities_response.status_code, 200, payload["message"]
        )
        activations = payload["data"]

        self.assertEqual(5, len(activations))
        self.assertTrue(
            any(
                activation["status"] == "Opportunity Created"
                for activation in activations
            ),
            "No Activation with Status 'Opportunity Created' found",
        )

    @patch("requests.get")
    def test_should_create_new_activation_when_one_activity_per_contact_and_a_meeting_per_contact_is_in_salesforce(
        self, mock_sobject_fetch
    ):
        # setup mock api responses
        set_mock_response_by_request_key(
            "contains_content_criteria_query",
            get_one_mock_task_per_contact_for_contains_content_criteria_query(),
        )
        set_mock_response_by_request_key("unique_values_content_criteria_query", [])
        set_mock_response_by_request_key(
            "fetch_contacts_by_ids_and_non_null_accounts",
            get_ten_mock_contacts_spread_across_five_accounts(),
        )
        set_mock_response_by_request_key(
            "fetch_opportunities_by_account_ids_from_date",
            [get_mock_opportunity_for_account()],
        )
        set_mock_response_by_request_key(
            "fetch_events_by_account_ids_from_date",
            [get_mock_event_for_account()],
        )
        set_mock_response_by_request_key(
            "fetch_contacts_by_account_ids",
            get_ten_mock_contacts_spread_across_five_accounts(),
        )

        save_tokens("test_access_token", "test_instance_url")
        mock_sobject_fetch.side_effect = response_based_on_query
        load_prospecting_activities_response = self.app.get(
            "/load_prospecting_activities"
        )
        payload = json.loads(load_prospecting_activities_response.data)
        self.assertEqual(
            load_prospecting_activities_response.status_code, 200, payload["message"]
        )

        activations = payload["data"]
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

    # helpers

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
