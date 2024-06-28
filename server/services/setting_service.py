from server.models import FilterContainerModel, FilterModel, TaskSObject
from server.utils import format_error_message
from typing import List


filter_blacklist = ["Id", "CreatedDate", "WhoId"]


def define_criteria_from_tasks(tasks: List[TaskSObject]) -> FilterContainerModel:
    try:
        common_keys = set(tasks[0].to_dict().keys())
        for task in tasks[1:]:
            common_keys.intersection_update(task.to_dict().keys())

        common_keys = common_keys - set(filter_blacklist)

        filters = []
        for key in common_keys:
            values = [task.to_dict()[key] for task in tasks]
            unique_values = set(values)

            if all(isinstance(v, str) for v in values):
                if len(unique_values) == 1:
                    filters.append(
                        FilterModel(
                            field=key,
                            operator="equals",
                            value=next(iter(unique_values)),
                            dataType="string",
                        )
                    )
                else:
                    substring_counts = {}
                    for value in values:
                        parts = value.split()
                        for part in parts:
                            substring_counts[part] = substring_counts.get(part, 0) + 1

                    threshold = len(tasks) * 0.75
                    for substring, count in substring_counts.items():
                        if count >= threshold:
                            filters.append(
                                FilterModel(
                                    field=key,
                                    operator="contains",
                                    value=substring,
                                    dataType="string",
                                )
                            )
            elif all(isinstance(v, (int, float)) for v in values):
                if len(unique_values) == 1:
                    filters.append(
                        FilterModel(
                            field=key,
                            operator="equals",
                            value=next(iter(unique_values)),
                            dataType="number",
                        )
                    )
                else:
                    median_value = sorted(unique_values)[len(unique_values) // 2]
                    above_median_count = sum(1 for v in values if v > median_value)
                    below_median_count = sum(1 for v in values if v < median_value)
                    if above_median_count >= len(values) * 0.5:
                        filters.append(
                            FilterModel(
                                field=key,
                                operator="greater than",
                                value=median_value,
                                dataType="number",
                            )
                        )
                    if below_median_count >= len(values) * 0.5:
                        filters.append(
                            FilterModel(
                                field=key,
                                operator="less than",
                                value=median_value,
                                dataType="number",
                            )
                        )

        filter_logic = " AND ".join([f"{i+1}" for i in range(len(filters))])
        return FilterContainerModel(
            name="Common Task Criteria", filters=filters, filterLogic=filter_logic
        )
    except Exception as e:
        raise Exception(format_error_message(e))
