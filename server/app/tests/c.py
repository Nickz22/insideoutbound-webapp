from server.app.models import TaskSObject
from datetime import datetime

today = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000+0000")

mock_tasks_for_criteria_with_contains_content = [
    TaskSObject(
        Id="mock_task_id_for_criteria",
        CreatedDate=today,
        WhoId="mock_contact_id",
        Subject="mock task subject",
        Status="Mock Task Status",
        TaskSubtype="Call",
    ).to_dict(),
    TaskSObject(
        Id="mock_task_id_for_criteria",
        CreatedDate=today,
        WhoId="mock_contact_id",
        Subject="task subject",
        Status="Another Mock Status",
        TaskSubtype="Call",
    ).to_dict(),
    TaskSObject(
        Id="mock_task_id_for_criteria",
        CreatedDate=today,
        WhoId="mock_contact_id",
        Subject="some other task subject",
        Status="Mock Task Status",
        TaskSubtype="Email",
    ).to_dict(),
]

mock_tasks_for_criteria_with_unique_values_content = [
    TaskSObject(
        Id="mock_task_id_for_criteria",
        CreatedDate=today,
        WhoId="mock_contact_id",
        Subject="first subject",
        Status="first status",
        TaskSubtype="LinkedIn",
    ).to_dict(),
    TaskSObject(
        Id="mock_task_id_for_criteria",
        CreatedDate=today,
        WhoId="mock_contact_id",
        Subject="and another",
        Status="and another",
        TaskSubtype="Call",
    ).to_dict(),
    TaskSObject(
        Id="mock_task_id_for_criteria",
        CreatedDate=today,
        WhoId="mock_contact_id",
        Subject="yet one more",
        Status="yet one more",
        TaskSubtype="Email",
    ).to_dict(),
]
