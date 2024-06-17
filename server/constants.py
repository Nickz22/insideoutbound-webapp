MISSING_ACCESS_TOKEN = "missing access token"
WHO_ID = "who_id"
FILTER_OPERATOR_MAPPING = {
    "string": {
        "contains": "LIKE",
        "equals": "=",
        "not equals": "!=",
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
        "role": "user",
        "content": """
    You are a filter generating machine. You excel at receiving Task SObjects and generating FilterContainer instances to match the Tasks you received. The definition for a FilterContainer is: 

    /**
    * Filter instance
    * @param field - Salesforce SObject field to filter on
    * @param operator - String ("contains" | "equals" | "not equals")
    *                   Number ("less than" | "less than or equal to" | "greater than" | "greater than or equal to")
    *                   Date ("equals" | "not equals" | "before" | "on or before" | "on or after" | "last n days" | "next n days" | "this month" | "last month" | "next month" | "this year" | "last year" | "next year")
    * @param value - Value to filter on
    * @param dataType - String ("string" | "number" | "date")
    */
    {
        field: "",
        operator: "",
        value: "",
        dataType: ""
    }
    /**
    * Filter container
    * @param name - Name of the filter container
    * @param filters - Array of Filter instances
    * @param filterLogic - String (i.e. 1 AND (2 OR 3) AND 4)
    */
    {
        filters: [],
        filterLogic: ""    
    }

    """,
    },
    {
        "role": "system",
        "content": "You respond only with FilterContainer instantiations. Don't speak english, or include anything other than the direct instantiation of a single object resembling the FilterContainer whose filters match the given Tasks. Questions marked with TRAINING_DATA: should be considered as inspiration for future questions. Questios marked as THIS_IS_REAL: are to be answered.",
    },
    {
        "role": "user",
        "content": """TRAINING_DATA: Given these Tasks, generate a FilterContainer which captures as many of their common attributes as possible. Please only respond with a FilterContainer object.
      
      [{'id': 1, 'subject': 'foo bar', 'who': 'Sam English', 'priority': 'High', 'status': 'Not Started', 'type': 'Call', 'duration': 25, 'due_date' : '2024-01-02', 'task_subtype': 'Outbound'}, {'id': 2, 'subject': 'foo pop', 'who': 'John Doe', 'priority': 'Medium', 'status': 'Not Started', 'type': 'Call', 'duration': 13, 'due_date' : '2024-01-04', 'task_subtype': 'Outbound'}, {'id': 3, 'subject': 'foo man', 'who': 'Sarah Dempsey', 'priority': 'Low', 'status': 'Not Started', 'type': 'Call', 'duration': 17, 'due_date' : '01-28-24', 'task_subtype': 'Inbound'}]
      """,
    },
    {
        "role": "assistant",
        "content": """TRAINING_DATA:
            ```javascript
            {
                filters : [
                    {field: "subject", operator: "contains", value: "foo", dataType: "string"},
                    {field: "status", operator: "equals", value: "Not Started", dataType: "string"},
                    {field: "duration", operator: "greater than", value: 13, dataType: "number"},
                    {field: "due_date", operator: "on or after", value: "2024-01-02", dataType: "date"},
                    {field: "task_subtype", operator: "equals", value: "Outbound", dataType: "string"},
                    {field: "task_subtype", operator: "equals", value: "Inbound", dataType: "string"},
                ],
                filter_logic: "1 AND 2 AND 3 AND 4 AND (5 OR 6)"
            }
            ```
        """,
    },
    {
        "role": "user",
        "content": """THIS_IS_REAL:
            Given these Tasks, generate a FilterContainer which captures as many of their common attributes as possible. Please only respond with a FilterContainer object.
        
            __INSERT_TASKS__
            """,
    },
]
