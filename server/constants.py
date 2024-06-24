SESSION_EXPIRED = "session expired"
WHO_ID = "who_id"
FILTER_OPERATOR_MAPPING = {
    "string": {
        "contains": "LIKE",
        "equals": "=",
        "not equals": "!=",
        "starts with": "LIKE",
        "ends with": "LIKE",
    },
    "number": {
        "equals": "=",
        "not equals": "!=",
        "less than": "<",
        "less than or equal": "<=",
        "greater than": ">",
        "greater than or equal": ">=",
    },
    "date": {
        "equals": "=",
        "not equals": "!=",
        "before": "<",
        "on or before": "<=",
        "after": ">",
        "on or after": ">=",
        "last n days": "= LAST_N_DAYS:",
        "next n days": "= NEXT_N_DAYS:",
        "this month": "= THIS_MONTH",
        "last month": "= LAST_MONTH",
        "next month": "= NEXT_MONTH",
        "this year": "= THIS_YEAR",
        "last year": "= LAST_YEAR",
        "next year": "= NEXT_YEAR",
    },
}

GPT_FILTER_GENERATION_PROMPT = [
    {
        "role": "system",
        "content": """
    You are a filter generating machine. You excel at receiving Task SObjects and generating FilterContainer instances to match the Tasks you received. The definition for a FilterContainer is: 
    
    // Filter
    {
        field: "",    // Salesforce SObject field to filter on
        operator: "", // String ("contains" | "equals" | "not equals")
                      // Number ("less than" | "less than or equal to" | "greater than" | "greater than or equal to")
                      // Date ("equals" | "not equals" | "before" | "on or before" | "on or after" | "last n days" | "next n days" | "this month" | "last month" | "next month" | "this year" | "last year" | "next year")
        value: "",    // Value to filter on
        dataType: ""  // String ("string" | "number" | "date")
    }
    
    // FilterContainer
    {
        filters: [], // Array of Filter instances
        filter_logic: ""  // String (i.e. 1 AND (2 OR 3) AND 4)
    }

    """,
    },
    {
        "role": "system",
        "content": "You respond only with FilterContainer instantiations. Don't include anything other than the object resembling the FilterContainer whose filters match the given Tasks. Questions marked with 'TRAINING_DATA:' should only be considered for training purposes, do not consider them for net new questions. Questios marked as 'THIS_IS_REAL:' are net new questions to be answered.",
    },
    {
        "role": "user",
        "content": """TRAINING_DATA: 
        Do not consider these Tasks for any future answers. 
        Given these Tasks, generate a FilterContainer which captures as many of their common attributes as possible. 
        Please only respond with a FilterContainer object.
      
      [{'id': 1, 'Subject': 'foo bar', 'Who': 'Sam English', 'Priority': 'High', 'Status': 'Not Started', 'Type': 'Call', 'Duration': 25, 'ActivityDate' : '2024-01-02', 'TaskSubType': 'Outbound'}, {'id': 2, 'Subject': 'foo pop', 'Who': 'John Doe', 'Priority': 'Medium', 'Status': 'Not Started', 'Type': 'Call', 'Duration': 13, 'ActivityDate' : '2024-01-04', 'TaskSubType': 'Outbound'}, {'id': 3, 'Subject': 'foo man', 'Who': 'Sarah Dempsey', 'Priority': 'Low', 'Status': 'Not Started', 'Type': 'Call', 'Duration': 17, 'ActivityDate' : '01-28-24', 'TaskSubType': 'Inbound'}]
      """,
    },
    {
        "role": "assistant",
        "content": """TRAINING_DATA:
            ```json
            {
                filters : [
                    {field: "Subject", operator: "contains", value: "foo", dataType: "string"},
                    {field: "Status", operator: "equals", value: "Not Started", dataType: "string"},
                    {field: "Duration", operator: "greater than", value: 13, dataType: "number"},
                    {field: "ActivityDate", operator: "on or after", value: "2024-01-02", dataType: "date"},
                    {field: "TaskSubType", operator: "equals", value: "Outbound", dataType: "string"},
                    {field: "TaskSubType", operator: "equals", value: "Inbound", dataType: "string"},
                ],
                filter_logic: "1 AND 2 AND 3 AND 4 AND (5 OR 6)"
            }
            ```
        """,
    },
    {
        "role": "user",
        "content": """THIS_IS_REAL:
            Given the below Tasks, generate a FilterContainer which captures as many of their common attributes as possible. Please only respond with a FilterContainer object. Do not consider the previous conversation for this question.
        
            __INSERT_TASKS__
            """,
    },
    {
        "role": "user",
        "content": """
        THIS_IS_REAL: Double check to ensure your answer has absolutely no other content than the exact FilterContainer object.
        """,
    },
]

FILTER_TASK_FIELDS = [
    "Subject",
    "Priority",
    "Status",
    "CallDurationInSeconds",
    "TaskSubtype",
]

FILTER_EVENT_FIELDS = ["Subject", "EventSubtype"]
