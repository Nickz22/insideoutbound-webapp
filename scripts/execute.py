from services.setting_service import define_criteria_from_tasks

tasks = [
    {
        "Id": 1,
        "Subject": "Call John Doe",
        "Who": "John Doe",
        "Priority": "High",
        "Status": "Not Started",
        "Type": "Call",
        "TaskSubType": "Outbound",
    },
    {
        "Id": 2,
        "Subject": "Email Jane Doe",
        "Who": "Jane Doe",
        "Priority": "Medium",
        "Status": "Not Started",
        "Type": "Email",
        "TaskSubType": "Outbound",
    },
    {
        "Id": 3,
        "Subject": "Call John Smith",
        "Who": "John Smith",
        "Priority": "Low",
        "Status": "Not Started",
        "Type": "Call",
        "TaskSubtype": "Inbound",
    },
    {
        "Id": 4,
        "Subject": "Email Jane Smith",
        "Who": "Jane Smith",
        "Priority": "High",
        "Status": "Not Started",
        "Type": "Email",
        "TaskSubtype": "Inbound",
    },
]

filter_container = define_criteria_from_tasks(tasks)
print(filter_container)
