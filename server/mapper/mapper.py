from models import (
    Task,
    Settings,
    FilterContainer,
    Filter,
    FilterContainerModel,
    FilterModel,
    SettingsModel,
)
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


def convert_filter_model_to_filter(fm: dict) -> Filter:
    return Filter(
        field=fm["field"],
        operator=fm["operator"],
        value=fm["value"],
        data_type=fm["dataType"],
    )


def convert_filter_container_model_to_filter_container(fcm: dict) -> FilterContainer:
    if fcm is None or (isinstance(fcm, dict) and not fcm):
        return FilterContainer(name="", filters=[], filter_logic="")

    return FilterContainer(
        name=fcm["name"],
        filters=[convert_filter_model_to_filter(f) for f in fcm["filters"]],
        filter_logic=fcm["filterLogic"],
    )


def convert_settings_model_to_settings(sm: dict) -> Settings:
    return Settings(
        inactivity_threshold=(
            sm["inactivityThreshold"] if "inactivityThreshold" in sm else 0
        ),
        cooloff_period=sm["cooloffPeriod"] if "cooloffPeriod" in sm else 0,
        criteria=(
            [
                convert_filter_container_model_to_filter_container(fc)
                for fc in sm["criteria"]
            ]
            if "criteria" in sm and sm["criteria"] is not None
            else []
        ),
        meetings_criteria=convert_filter_container_model_to_filter_container(
            sm["meetingsCriteria"]
        ),
        skip_account_criteria=convert_filter_container_model_to_filter_container(
            sm["skipAccountCriteria"]
        ),
        skip_opportunity_criteria=convert_filter_container_model_to_filter_container(
            sm["skipOpportunityCriteria"]
        ),
        activities_per_contact=(
            sm["activitiesPerContact"] if "activitiesPerContact" in sm else 0
        ),
        contacts_per_account=(
            sm["contactsPerAccount"] if "contactsPerAccount" in sm else 0
        ),
        tracking_period=sm["trackingPeriod"] if "trackingPeriod" in sm else 0,
        activate_by_meeting=sm["activateByMeeting"],
        activate_by_opportunity=sm["activateByOpportunity"],
    )
