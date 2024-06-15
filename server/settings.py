from models import Filter, FilterContainer

settings = {
    "activities_per_contact": 5,
    "contacts_per_account": 2,
    "tracking_period": 10,
    "criteria": [
        FilterContainer(
            name="Inbound Emails",
            filters=[
                Filter(
                    field="Subject",
                    data_type="string",
                    operator="contains",
                    value="[Disposition 1a]",
                ),
                Filter(
                    field="Subject",
                    data_type="string",
                    operator="contains",
                    value="[Disposition 2a]",
                ),
                Filter(
                    field="Subject",
                    data_type="string",
                    operator="contains",
                    value="[Disposition 3a]",
                ),
                Filter(
                    field="Subject",
                    data_type="string",
                    operator="contains",
                    value="[Disposition 4a]",
                ),
                Filter(
                    field="Subject",
                    data_type="string",
                    operator="contains",
                    value="[Disposition 5a]",
                ),
            ],
            filterLogic="((_1_ OR _2_ OR _3_) AND _4_ AND _5_)",
        ),
        FilterContainer(
            name="Outbound Emails",
            filters=[
                Filter(
                    field="Priority",
                    data_type="string",
                    operator="equals",
                    value="High",
                ),
                Filter(
                    field="Status",
                    data_type="string",
                    operator="not equals",
                    value="Completed",
                ),
                Filter(
                    field="CreatedDate",
                    data_type="date",
                    operator="last n days",
                    value="30",
                ),
            ],
            filterLogic="_1_ AND _2_ AND _3_",
        ),
        FilterContainer(
            name="Inbound Calls",
            filters=[
                Filter(
                    field="OwnerId",
                    data_type="string",
                    operator="equals",
                    value="005RK000005pIWHYA2",
                ),
                Filter(
                    field="ActivityDate",
                    data_type="date",
                    operator="on or after",
                    value="2022-01-01",
                ),
                Filter(
                    field="ActivityDate",
                    data_type="date",
                    operator="on or before",
                    value="2022-12-31",
                ),
            ],
            filterLogic="_1_ AND (_2_ OR _3_)",
        ),
        FilterContainer(
            name="Outbound Calls",
            filters=[
                Filter(
                    field="OwnerId",
                    data_type="string",
                    operator="equals",
                    value="005RK000005pIWHYA2",
                ),
                Filter(
                    field="ActivityDate",
                    data_type="date",
                    operator="on or after",
                    value="2022-01-01",
                ),
                Filter(
                    field="ActivityDate",
                    data_type="date",
                    operator="on or before",
                    value="2022-12-31",
                ),
            ],
            filterLogic="_1_ AND (_2_ OR _3_)",
        ),
    ],
}
