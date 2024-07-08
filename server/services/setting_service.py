from server.models import FilterContainerModel, FilterModel, TableColumn
from server.utils import format_error_message
from typing import List


filter_blacklist = ["Id", "CreatedDate", "WhoId"]


def define_criteria_from_tasks(
    tasks, columns: List[TableColumn]
) -> FilterContainerModel:
    column_ids = {column.id for column in columns}  # Set of column IDs to filter by

    if not tasks:
        return FilterContainerModel(
            name="Common Task Criteria", filters=[], filterLogic=""
        )

    try:
        common_keys = column_ids.intersection(tasks[0].keys())
        for task in tasks[1:]:
            common_keys.intersection_update(task.keys())

        common_keys = common_keys - set(filter_blacklist)

        filters = []
        for key in common_keys:
            values = [task[key] for task in tasks if key in task]
            try:
                unique_values = set(values)
            except Exception as e:
                raise Exception(
                    f"Error while processing key {key}: {format_error_message(e)}"
                )

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
