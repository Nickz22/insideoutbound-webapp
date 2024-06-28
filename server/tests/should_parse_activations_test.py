from flask import Flask
import unittest, json, sys, os

os.environ["APP_ENV"] = "test"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from server.models import SettingsModel, FilterContainerModel, FilterModel, TaskSObject
from server.app import app
from c import (
    mock_tasks_for_criteria_with_contains_content,
    mock_tasks_for_criteria_with_unique_values_content,
)

##
## Figure out how to mock REST return results via SObject API query
## Insert 1 unresponsive Activation
## Increment 1 current Activation
## Create 1 new activation
##


class TestActivationLogic(unittest.TestCase):
    def setUp(self):
        # Creates a test client
        self.app = app.test_client()
        # Propagate the exceptions to the test client
        self.app.testing = True

        self.do_onboarding_flow()
        settings_model = self.fetch_settings_model_from_db()

        self.assertEqual(settings_model.activitiesPerContact, 7)
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

    def test_activation_scenario(self):
        pass
        # Define tasks that meet the activation criteria
        # today = datetime.today().date()
        # self.contacts = {
        #     "contact1": {
        #         "id": "contact1",
        #         "account_id": "account1",
        #         "account": {"name": "mock_account_1"},
        #     },
        #     "contact2": {
        #         "id": "contact2",
        #         "account_id": "account1",
        #         "account": {"name": "mock_account_1"},
        #     },
        #     "contact3": {
        #         "id": "contact3",
        #         "account_id": "account1",
        #         "account": {"name": "mock_account_1"},
        #     },
        # }
        # self.tasks_by_criteria["inbound_calls"] = [
        #     {
        #         "id": "task1",
        #         "created_date": today - timedelta(days=2),
        #         "who_id": "contact1",
        #     },
        #     {
        #         "id": "task2",
        #         "created_date": today - timedelta(days=2),
        #         "who_id": "contact1",
        #     },
        #     {
        #         "id": "task3",
        #         "created_date": today - timedelta(days=3),
        #         "who_id": "contact2",
        #     },
        # ]
        # self.tasks_by_criteria["outbound_calls"] = [
        #     {
        #         "id": "task4",
        #         "created_date": today - timedelta(days=3),
        #         "who_id": "contact2",
        #     },
        #     {
        #         "id": "task5",
        #         "created_date": today - timedelta(days=4),
        #         "who_id": "contact3",
        #     },
        #     {
        #         "id": "task6",
        #         "created_date": today - timedelta(days=4),
        #         "who_id": "contact3",
        #     },
        # ]

        # # Run the function under test
        # response = compute_activated_accounts(
        #     self.tasks_by_criteria, self.contacts, self.settings
        # )

        # # Check if the account is activated
        # self.assertEqual(len(response.data), 1)
        # self.assertTrue(response.success)
        # self.assertEqual(response.data[0].account.id, "account1")

        # two_days_ago = datetime.now() - timedelta(days=2)
        # two_days_ago_date = two_days_ago.date()
        # self.assertEqual(response.data[0].activated_date, two_days_ago_date)
        # self.assertEqual(response.data[0].active_contacts, 3)

    # helpers
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

    def do_onboarding_flow(self):
        """
        constructs a settings model and saves it via the save_settings API
        """

        contains_content_filter_model = self.get_filter_response(
            mock_tasks_for_criteria_with_contains_content
        )
        contains_content_filter_model.name = "Contains Content"

        unique_values_content_filter_model = self.get_filter_response(
            mock_tasks_for_criteria_with_unique_values_content
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
            activitiesPerContact=7,
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

    def get_filter_response(self, tasks) -> FilterContainerModel:
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
