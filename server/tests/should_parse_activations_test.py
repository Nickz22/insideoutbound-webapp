from flask import Flask
import unittest, json, sys, os
from datetime import datetime, timedelta

os.environ["APP_ENV"] = "test"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from server.engine.activation_engine import compute_activated_accounts
from server.models import SettingsModel, FilterContainerModel, FilterModel
from server.cache import load_settings
from server.app import app


class TestActivationLogic(unittest.TestCase):
    def setUp(self):
        # Creates a test client
        self.app = app.test_client()
        # Propagate the exceptions to the test client
        self.app.testing = True

        post_data = SettingsModel(
            activateByMeeting=True,
            activateByOpportunity=True,
            activitiesPerContact=7,
            contactsPerAccount=2,
            criteria=[
                FilterContainerModel(
                    name="Inbound Calls",
                    filters=[
                        FilterModel(
                            field="TaskSubtype",
                            dataType="string",
                            operator="contains",
                            value="Inbound",
                        ),
                        FilterModel(
                            field="Type",
                            dataType="string",
                            operator="equals",
                            value="Call",
                        ),
                    ],
                    filterLogic="1 AND 2",
                ),
                FilterContainerModel(
                    name="Outbound Calls",
                    filters=[
                        FilterModel(
                            field="TaskSubtype",
                            dataType="string",
                            operator="contains",
                            value="Outbound",
                        ),
                        FilterModel(
                            field="Type",
                            dataType="string",
                            operator="equals",
                            value="Call",
                        ),
                    ],
                    filterLogic="1 AND 2",
                ),
            ],
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

        get_settings_response = self.app.get("/get_settings")
        self.assertEqual(get_settings_response.status_code, 200, response.data)
        settings_model = SettingsModel(**json.loads(get_settings_response.data))
        settings_model.criteria = [
            FilterContainerModel(**criteria) for criteria in settings_model.criteria
        ]
        settings_model.meetingsCriteria = FilterContainerModel(
            **settings_model.meetingsCriteria
        )

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
        self.assertEqual(settings_model.criteria[0].name, "Inbound Calls")
        self.assertEqual(settings_model.criteria[0].filterLogic, "1 AND 2")
        self.assertEqual(settings_model.criteria[1].name, "Outbound Calls")
        self.assertEqual(settings_model.criteria[1].filterLogic, "1 AND 2")

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
