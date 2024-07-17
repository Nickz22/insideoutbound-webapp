from server.models import (
    Task,
    Settings,
    FilterContainer,
    Filter,
    FilterContainerModel,
    FilterModel,
    SettingsModel,
)
from datetime import datetime
from server.utils import (
    surround_numbers_with_underscores,
    remove_underscores_from_numbers,
)


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


def convert_filter_model_to_filter(fm: FilterModel) -> Filter:
    return Filter(
        field=fm.field,
        operator=fm.operator,
        value=fm.value,
        data_type=fm.dataType,
    )


def convert_filter_to_filter_model(f: dict) -> FilterModel:
    return FilterModel(
        field=f.field,
        operator=f.operator,
        value=f.value,
        dataType=f.data_type,
    )


def convert_filter_container_model_to_filter_container(
    fcm: FilterContainerModel,
) -> FilterContainer:
    if fcm is None or (isinstance(fcm, dict) and not fcm):
        return FilterContainer(name="", filters=[], filter_logic="")

    return FilterContainer(
        name=fcm.name,
        filters=[convert_filter_model_to_filter(FilterModel(**f)) for f in fcm.filters],
        filter_logic=surround_numbers_with_underscores(fcm.filterLogic),
    )


def convert_filter_container_to_filter_container_model(
    fc: dict,
) -> FilterContainerModel:
    return FilterContainerModel(
        name=fc.name,
        filters=[convert_filter_to_filter_model(f) for f in fc.filters],
        filterLogic=remove_underscores_from_numbers(fc.filter_logic),
    )


def convert_settings_model_to_settings(sm: SettingsModel) -> Settings:
    return Settings(
        inactivity_threshold=sm.inactivityThreshold,
        criteria=(
            [
                convert_filter_container_model_to_filter_container(
                    FilterContainerModel(**fc)
                )
                for fc in sm.criteria
            ]
            if len(sm.criteria) > 0
            else [FilterContainer(name="", filters=[], filter_logic="")]
        ),
        meeting_object=sm.meetingObject,
        meetings_criteria=(
            convert_filter_container_model_to_filter_container(
                FilterContainerModel(**sm.meetingsCriteria)
            )
            if sm.meetingsCriteria is not None
            else FilterContainer(name="", filters=[], filter_logic="")
        ),
        activities_per_contact=sm.activitiesPerContact,
        contacts_per_account=sm.contactsPerAccount,
        tracking_period=sm.trackingPeriod,
        activate_by_meeting=sm.activateByMeeting,
        activate_by_opportunity=sm.activateByOpportunity,
    )
