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