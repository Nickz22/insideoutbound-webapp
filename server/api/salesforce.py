import requests
from models import Filter, FilterContainer

# Group operators by data type
operator_mapping = {
    "string": {
        "contains": "LIKE",
        "equals": "=",
        "not equals": "!="
    },
    "number": {
        "equals": "=",
        "not equals": "!=",
        "less than": "<",
        "less than or equal": "<=",
        "greater than": ">",
        "greater than or equal": ">="
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
        "next year": "= NEXT_YEAR"
    }
}

def map_operator(operator, data_type):
    return operator_mapping[data_type].get(operator, operator)

def construct_condition(filter_obj):
    field = filter_obj.field
    value = filter_obj.value

    operator = map_operator(filter_obj.operator, filter_obj.data_type)

    if filter_obj.data_type == "string" and operator == "LIKE":
        value = f" '%{value}%'"
    elif filter_obj.data_type == "string":
        value = f"'{value}'"
    elif filter_obj.data_type == "date" or filter_obj.data_type == "number":
        value = f"{value}"

    return f"{field} {operator}{value}"



# Main function to construct the WHERE clause and fetch tasks
def fetch_tasks_by_criteria(criteria, instance_url, access_token):
    """
    criteria - list(FilterContainer): 
    """
    soql_query = f"SELECT Id, WhoId, WhatId, Subject, Status FROM Task WHERE"
    soql_queries = []

    for filter_container in criteria:
        conditions = [construct_condition(f) for f in filter_container.filters]
        
        # Create a mapping of index to condition
        index_to_condition = {str(index + 1): condition for index, condition in enumerate(conditions)}
        
        # Replace each index in the filterLogic with the corresponding condition
        combined_conditions = filter_container.filterLogic
        for index, condition in index_to_condition.items():
            combined_conditions = combined_conditions.replace(index, condition)
        
        soql_queries.append(f"{soql_query} {combined_conditions}")
    
    # SOQL query
    tasks = []
    
    for soql_query in soql_queries:
        print("SOQL Query:", soql_query)  # For debugging
        tasks.extend(fetch_tasks(soql_query, instance_url, access_token))
    
def fetch_tasks(soql_query, instance_url, access_token):
    headers = { "Authorization": f"Bearer {access_token}" }
    response = requests.get(f"{instance_url}/services/data/v52.0/query", headers=headers, params={"q": soql_query})
    if response.status_code == 200:
        return response.json()["records"]
    else:
        print("Error fetching tasks:", response.status_code, response.text)
        return []