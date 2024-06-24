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
from utils import surround_numbers_with_underscores, remove_underscores_from_numbers


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


def convert_filter_to_filter_model(f: dict) -> FilterModel:
    return FilterModel(
        field=f.field,
        operator=f.operator,
        value=f.value,
        dataType=f.data_type,
    )


def convert_filter_container_model_to_filter_container(fcm: dict) -> FilterContainer:
    if fcm is None or (isinstance(fcm, dict) and not fcm):
        return FilterContainer(name="", filters=[], filter_logic="")

    return FilterContainer(
        name=fcm["name"],
        filters=[convert_filter_model_to_filter(f) for f in fcm["filters"]],
        filter_logic=surround_numbers_with_underscores(fcm["filterLogic"]),
    )


def convert_filter_container_to_filter_container_model(
    fc: dict,
) -> FilterContainerModel:
    return FilterContainerModel(
        name=fc.name,
        filters=[convert_filter_to_filter_model(f) for f in fc.filters],
        filterLogic=remove_underscores_from_numbers(fc.filter_logic),
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


def convert_settings_to_settings_model(settings: Settings) -> SettingsModel:
    return SettingsModel(
        inactivityThreshold=settings["inactivity_threshold"],
        cooloffPeriod=settings["cooloff_period"],
        criteria=[
            convert_filter_container_to_filter_container_model(fc)
            for fc in settings["criteria"]
        ],
        meetingObject="Task",
        meetingsCriteria=convert_filter_container_to_filter_container_model(
            settings["meetings_criteria"]
        ),
        skipAccountCriteria=(
            convert_filter_container_to_filter_container_model(
                settings["skip_account_criteria"]
            )
            if settings["skip_account_criteria"]
            else FilterContainerModel(name="", filters=[], filterLogic="")
        ),
        skipOpportunityCriteria=(
            convert_filter_container_to_filter_container_model(
                settings["skip_opportunity_criteria"]
            )
            if settings["skip_opportunity_criteria"]
            else FilterContainerModel(name="", filters=[], filterLogic="")
        ),
        activitiesPerContact=settings["activities_per_contact"],
        contactsPerAccount=settings["contacts_per_account"],
        trackingPeriod=settings["tracking_period"],
        activateByMeeting=settings["activate_by_meeting"],
        activateByOpportunity=settings["activate_by_opportunity"],
    )
