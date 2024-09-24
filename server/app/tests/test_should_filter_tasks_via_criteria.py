import pytest
from datetime import datetime
from app.data_models import Filter, FilterContainer

# Fresh mock data
mock_tasks = [
    {
        "Id": "task1",
        "Subject": "Call client about project",
        "Status": "Not Started",
        "Priority": "High",
        "CreatedDate": "2023-05-01T10:00:00.000+0000",
        "DueDate": "2023-05-10",
        "IsCompleted": False,
        "TaskSubtype": "Call",
        "Description": "Follow up on project details",
        "NumberOfEmployees": 50,
    },
    {
        "Id": "task2",
        "Subject": "Send proposal",
        "Status": "In Progress",
        "Priority": "Normal",
        "CreatedDate": "2023-05-02T14:30:00.000+0000",
        "DueDate": "2023-05-15",
        "IsCompleted": False,
        "TaskSubtype": "Email",
        "Description": "Draft and send project proposal",
        "NumberOfEmployees": 100,
    },
    {
        "Id": "task3",
        "Subject": "Client meeting",
        "Status": "Completed",
        "Priority": "High",
        "CreatedDate": "2023-05-03T09:15:00.000+0000",
        "DueDate": "2023-05-03",
        "IsCompleted": True,
        "TaskSubtype": "Meeting",
        "Description": "Discuss timeline",
        "NumberOfEmployees": 75,
    },
    {
        "Id": "task4",
        "Subject": "Internal review",
        "Status": "Not Started",
        "Priority": "Low",
        "CreatedDate": "2023-05-04T11:45:00.000+0000",
        "DueDate": "2023-05-20",
        "IsCompleted": False,
        "TaskSubtype": "Other",
        "Description": "Review project progress with team",
        "NumberOfEmployees": 25,
    },
]


def test_basic_string_filters():
    # Test 'equals' operator
    filter_equals = Filter(
        field="Status", operator="equals", value="Completed", data_type="string"
    )
    assert not filter_equals.matches(mock_tasks[0])
    assert filter_equals.matches(mock_tasks[2])

    # Test 'not_equal' operator
    filter_not_equal = Filter(
        field="Priority", operator="not_equal", value="Normal", data_type="string"
    )
    assert filter_not_equal.matches(mock_tasks[0])
    assert not filter_not_equal.matches(mock_tasks[1])

    # Test 'contains' operator
    filter_contains = Filter(
        field="Subject", operator="contains", value="client", data_type="string"
    )
    assert filter_contains.matches(mock_tasks[0])
    assert filter_contains.matches(mock_tasks[2])
    assert not filter_contains.matches(mock_tasks[1])

    # Test 'does_not_contain' operator
    filter_does_not_contain = Filter(
        field="Description",
        operator="does_not_contain",
        value="project",
        data_type="string",
    )
    assert not filter_does_not_contain.matches(mock_tasks[0])
    assert filter_does_not_contain.matches(mock_tasks[2])


def test_basic_number_filters():
    # Test 'equals' operator
    filter_equals = Filter(
        field="NumberOfEmployees", operator="equals", value="75", data_type="number"
    )
    assert not filter_equals.matches(mock_tasks[0])
    assert filter_equals.matches(mock_tasks[2])

    # Test 'not_equal' operator
    filter_not_equal = Filter(
        field="NumberOfEmployees", operator="not_equal", value="50", data_type="number"
    )
    assert not filter_not_equal.matches(mock_tasks[0])
    assert filter_not_equal.matches(mock_tasks[1])

    # Test 'greater_than' operator
    filter_greater_than = Filter(
        field="NumberOfEmployees",
        operator="greater_than",
        value="60",
        data_type="number",
    )
    assert not filter_greater_than.matches(mock_tasks[0])
    assert filter_greater_than.matches(mock_tasks[1])
    assert filter_greater_than.matches(mock_tasks[2])

    # Test 'less_than' operator
    filter_less_than = Filter(
        field="NumberOfEmployees", operator="less_than", value="80", data_type="number"
    )
    assert filter_less_than.matches(mock_tasks[0])
    assert filter_less_than.matches(mock_tasks[3])
    assert not filter_less_than.matches(mock_tasks[1])


def test_basic_date_filters():
    now = datetime.now()
    mock_tasks = [
        {"ActivityDate": "2023-05-01"},
        {"ActivityDate": "2023-05-02"},
        {"ActivityDate": "2023-05-03"},
        {"ActivityDate": "2023-05-04"},
    ]

    # Test 'equals' operator
    filter_equals = Filter(
        field="ActivityDate", operator="equals", value="2023-05-03", data_type="date"
    )
    assert not filter_equals.matches(mock_tasks[0])
    assert not filter_equals.matches(mock_tasks[1])
    assert filter_equals.matches(mock_tasks[2])
    assert not filter_equals.matches(mock_tasks[3])

    # Test 'not_equal' operator
    filter_not_equal = Filter(
        field="ActivityDate", operator="not_equal", value="2023-05-01", data_type="date"
    )
    assert not filter_not_equal.matches(mock_tasks[0])
    assert filter_not_equal.matches(mock_tasks[1])
    assert filter_not_equal.matches(mock_tasks[2])
    assert filter_not_equal.matches(mock_tasks[3])

    # Test 'greater_than' operator
    filter_greater_than = Filter(
        field="ActivityDate",
        operator="greater_than",
        value="2023-05-02",
        data_type="date",
    )
    assert not filter_greater_than.matches(mock_tasks[0])
    assert not filter_greater_than.matches(mock_tasks[1])
    assert filter_greater_than.matches(mock_tasks[2])
    assert filter_greater_than.matches(mock_tasks[3])

    # Test 'less_than' operator
    filter_less_than = Filter(
        field="ActivityDate", operator="less_than", value="2023-05-03", data_type="date"
    )
    assert filter_less_than.matches(mock_tasks[0])
    assert filter_less_than.matches(mock_tasks[1])
    assert not filter_less_than.matches(mock_tasks[2])
    assert not filter_less_than.matches(mock_tasks[3])

# Filter logic is stored in the database with underscore prepension/appensions to distinguish between "1" and "10"
def test_complex_filter_logic():
    filter_container = FilterContainer(
        name="Complex Filter",
        filters=[
            Filter(
                field="Status",
                operator="equals",
                value="Not Started",
                data_type="string",
            ),
            Filter(
                field="Priority", operator="equals", value="High", data_type="string"
            ),
            Filter(
                field="NumberOfEmployees",
                operator="greater_than",
                value="30",
                data_type="number",
            ),
        ],
        filter_logic="(_1_ AND _2_) OR (_1_ AND _3_)",
    )

    assert filter_container.matches(mock_tasks[0])  # Matches (1 AND 2)
    assert not filter_container.matches(mock_tasks[3]), "expected false because Task priority is 'Low' and 'NumberOfEmployees' is less than 30"
    assert not filter_container.matches(mock_tasks[1])  # Doesn't match either condition
    assert not filter_container.matches(mock_tasks[2])  # Doesn't match either condition

    # Test with more complex logic
    filter_container.filter_logic = "(_1_ OR _2_) AND (_3_ OR (_1_ AND _2_))"
    assert filter_container.matches(mock_tasks[0])  # Matches (1 OR 2) AND (3)
    assert not filter_container.matches(mock_tasks[3]), "expected false because 'NumberOfEmployees' is less than 30 and 'Priority' is 'Low'"  # does not match (1) AND (3)
    assert not filter_container.matches(mock_tasks[1]), "expected false because 'Status' is 'In Progress', and 'Priority' is 'Normal'"
    assert filter_container.matches(mock_tasks[2])


def test_nested_filter_logic():
    filter_container = FilterContainer(
        name="Nested Filter",
        filters=[
            Filter(
                field="Subject", operator="contains", value="client", data_type="string"
            ),
            Filter(
                field="Status",
                operator="not_equal",
                value="Completed",
                data_type="string",
            ),
            Filter(
                field="Priority", operator="equals", value="High", data_type="string"
            ),
            Filter(
                field="NumberOfEmployees",
                operator="greater_than",
                value="60",
                data_type="number",
            ),
        ],
        filter_logic="(_1_ AND _2_) AND (_3_ OR _4_)",
    )

    assert filter_container.matches(mock_tasks[0])  # Matches (1 AND 2) AND 3
    assert not filter_container.matches(mock_tasks[1])  # Doesn't match 1
    assert not filter_container.matches(mock_tasks[2])  # Doesn't match 2
    assert not filter_container.matches(mock_tasks[3])  # Doesn't match 1


def test_edge_cases():

    # Test with empty value
    filter_empty_value = Filter(
        field="Subject", operator="equals", value="", data_type="string"
    )
    assert not filter_empty_value.matches(mock_tasks[0])

    # Test with null value
    mock_tasks.append({"Id": "null_task", "Subject": None})
    filter_null_value = Filter(
        field="Subject", operator="equals", value="null", data_type="string"
    )
    assert not filter_null_value.matches(mock_tasks[-1])


if __name__ == "__main__":
    pytest.main()
