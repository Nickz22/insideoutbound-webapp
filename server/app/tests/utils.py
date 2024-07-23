import re


def is_valid_salesforce_query(query: str) -> bool:
    # Remove any leading/trailing whitespace
    query = query.strip()

    # Check if the query starts with SELECT
    if not query.upper().startswith("SELECT"):
        return False

    # Check if the query contains FROM
    if " FROM " not in query.upper():
        return False

    # Split the query into its main parts
    try:
        select_part, from_part = query.split(" FROM ", 1)
    except ValueError:
        return False

    # Validate SELECT part
    if not validate_select_part(select_part):
        return False

    # Validate FROM part (including WHERE and ORDER BY if present)
    if not validate_from_part(from_part):
        return False

    return True


def validate_select_part(select_part: str) -> bool:
    # Remove "SELECT " from the beginning
    fields_part = select_part[7:].strip()

    # Check for consecutive commas (including those separated by spaces)
    if re.search(r",\s*,", fields_part):
        return False

    # Split the fields
    fields = [field.strip() for field in fields_part.split(",")]

    # Check if there's at least one non-empty field
    if not fields or all(field == "" for field in fields):
        return False

    # Check each field for valid characters and structure
    for field in fields:
        # Check for empty field (this catches cases of leading/trailing commas too)
        if not field:
            return False
        # Check for valid characters (letters, numbers, underscore, dot)
        if not re.match(r"^[a-zA-Z0-9_\.]+$", field):
            return False
        # Check for valid structure (e.g., allow one dot for relationship queries)
        if "." in field and field.count(".") > 1:
            return False

    return True


def validate_from_part(from_part: str) -> bool:
    # Split into object name and the rest (WHERE, ORDER BY, etc.)
    parts = from_part.split(" WHERE ", 1)

    # Validate object name
    object_name = parts[0].strip()
    if not re.match(r"^[a-zA-Z0-9_]+$", object_name):
        return False

    # If there's a WHERE clause, validate it
    if len(parts) > 1:
        where_part = parts[1]
        if not validate_where_part(where_part):
            return False

    return True


def validate_where_part(where_part: str) -> bool:
    # Basic check for balanced parentheses
    if where_part.count("(") != where_part.count(")"):
        return False

    # Remove ORDER BY clause if present
    order_by_parts = where_part.split(" ORDER BY ")
    where_part = order_by_parts[0]

    # Check for CreatedDate conditions
    created_date_pattern = r"CreatedDate\s*(>=|>|<|<=)\s*'?([^'\s]+)'?"
    created_date_matches = re.finditer(created_date_pattern, where_part, re.IGNORECASE)

    for match in created_date_matches:
        date_value = match.group(2)
        if date_value.lower() != "none":
            # If it's not 'None', it should be a valid datetime
            if not re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", date_value):
                return False

    # Check for valid operators - order is important
    valid_operators = [
        "!=",
        "<=",
        ">=",
        "=",
        "<",
        ">",
        "NOT IN",
        "IN",
        "INCLUDES",
        "EXCLUDES",
        "LIKE",
    ]
    for op in valid_operators:
        where_part = where_part.replace(op, " ")

    # Remove AND, OR
    where_part = where_part.replace(" AND ", " ").replace(" OR ", " ")

    # Remove any valid date literals
    date_literals = [
        "TODAY",
        "YESTERDAY",
        "TOMORROW",
        "LAST_WEEK",
        "THIS_WEEK",
        "NEXT_WEEK",
        "LAST_MONTH",
        "THIS_MONTH",
        "NEXT_MONTH",
        "LAST_90_DAYS",
        "NEXT_90_DAYS",
        "THIS_QUARTER",
        "LAST_QUARTER",
        "NEXT_QUARTER",
        "THIS_YEAR",
        "LAST_YEAR",
        "NEXT_YEAR",
    ]
    for literal in date_literals:
        where_part = where_part.replace(literal, " ")

    # Remove any ISO8601 date strings
    where_part = re.sub(
        r"\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}:\d{2}(?:\.\d{3})?Z?)?", " ", where_part
    )

    # Remove string literals
    where_part = re.sub(r"'[^']*'", " ", where_part)

    # Remove numeric literals
    where_part = re.sub(r"\b\d+\b", " ", where_part)

    # Remove null and None
    where_part = re.sub(r"\b(null|none)\b", " ", where_part, flags=re.IGNORECASE)

    # Remove extra spaces
    where_part = " ".join(where_part.split())

    # If we've removed all valid parts, what remains should only be field names, parentheses and commas
    if re.search(r"[^a-zA-Z0-9_\s(),]", where_part):
        return False

    return True
