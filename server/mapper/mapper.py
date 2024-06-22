from models import Task
from datetime import datetime


def convert_sobjects_to_task_models(tasks):
    task_instances = []
    for task_dict in tasks:
        created_date = datetime.strptime(task_dict["created_date"], "%Y-%m-%d").date()
        task_instance = Task(
            id=task_dict["Id"],
            created_date=created_date,
            who_id=task_dict["WhoId"],
            subject=task_dict["Subject"],
            status=task_dict["Status"],
            task_subtype=task_dict.get("TaskSubtype"),
        )
        task_instances.append(task_instance)

    return task_instances
