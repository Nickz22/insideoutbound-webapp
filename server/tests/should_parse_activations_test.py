import unittest
from datetime import datetime, timedelta
import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from server.engine.activation_engine import compute_activated_accounts


class TestActivationLogic(unittest.TestCase):
    def setUp(self):
        # This method will run before each test
        self.settings = {
            "activities_per_contact": 2,
            "contacts_per_account": 3,
            "tracking_period": 6,
            "cooloff_period": 30,
            "account_inactivity_threshold": 10,
        }
        self.tasks_by_criteria = {"inbound_calls": {}, "outbound_calls": {}}

    def test_activation_scenario(self):
        # Define tasks that meet the activation criteria
        today = datetime.today().date()
        self.contacts = {
            "contact1": {
                "id": "contact1",
                "account_id": "account1",
                "account": {"name": "mock_account_1"},
            },
            "contact2": {
                "id": "contact2",
                "account_id": "account1",
                "account": {"name": "mock_account_1"},
            },
            "contact3": {
                "id": "contact3",
                "account_id": "account1",
                "account": {"name": "mock_account_1"},
            },
        }
        self.tasks_by_criteria["inbound_calls"] = [
            {
                "id": "task1",
                "created_date": today - timedelta(days=2),
                "who_id": "contact1",
            },
            {
                "id": "task2",
                "created_date": today - timedelta(days=2),
                "who_id": "contact1",
            },
            {
                "id": "task3",
                "created_date": today - timedelta(days=3),
                "who_id": "contact2",
            },
        ]
        self.tasks_by_criteria["outbound_calls"] = [
            {
                "id": "task4",
                "created_date": today - timedelta(days=3),
                "who_id": "contact2",
            },
            {
                "id": "task5",
                "created_date": today - timedelta(days=4),
                "who_id": "contact3",
            },
            {
                "id": "task6",
                "created_date": today - timedelta(days=4),
                "who_id": "contact3",
            },
        ]

        # Run the function under test
        response = compute_activated_accounts(
            self.tasks_by_criteria, self.contacts, self.settings
        )

        # Check if the account is activated
        self.assertEqual(len(response.data), 1)
        self.assertTrue(response.success)
        self.assertEqual(response.data[0].account.id, "account1")

        two_days_ago = datetime.now() - timedelta(days=2)
        two_days_ago_date = two_days_ago.date()
        self.assertEqual(response.data[0].activated_date, two_days_ago_date)
        self.assertEqual(response.data[0].active_contacts, 3)


# Add more tests as necessary
