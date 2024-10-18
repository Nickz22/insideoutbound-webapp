from typing import List, Optional
from app.data_models import Activation
from app.data_models import ApiResponse
from app.database.supabase_connection import get_supabase_admin_client
from app.mapper.mapper import supabase_dict_to_python_activation
from app.database.settings_selector import load_settings
from app.utils import get_salesforce_team_ids, format_error_message

from app.database.supabase_retry import retry_on_temporary_unavailable
import logging
from math import ceil


@retry_on_temporary_unavailable()
def load_active_activations_order_by_first_prospecting_activity_asc() -> ApiResponse:
    supabase_client = get_supabase_admin_client()
    team_member_ids = get_salesforce_team_ids(load_settings())

    page_size = 50
    current_page = 0
    all_activations = []

    while True:
        response = (
            supabase_client.table("Activations")
            .select("*")
            .neq("status", "Unresponsive")
            .in_("activated_by_id", team_member_ids)
            .order("first_prospecting_activity", desc=False)
            .range(current_page * page_size, (current_page + 1) * page_size - 1)
            .execute()
        )
        print(f"current page of activation query results: {current_page}")
        if not response.data:
            break

        all_activations.extend(
            supabase_dict_to_python_activation(row) for row in response.data
        )
        current_page += 1

        if len(response.data) < page_size:
            break

    return ApiResponse(data=all_activations, success=True)


@retry_on_temporary_unavailable()
def load_inactive_activations() -> ApiResponse:
    try:
        supabase_client = get_supabase_admin_client()
        team_member_ids = get_salesforce_team_ids(load_settings())

        response = (
            supabase_client.table("Activations")
            .select("*")
            .eq("status", "Unresponsive")
            .in_("activated_by_id", team_member_ids)
            .execute()
        )

        activations: List[Activation] = []
        for row in response.data:
            activation = supabase_dict_to_python_activation(row)
            activations.append(activation)

        return ApiResponse(data=activations if activations else [], success=True)
    except Exception as e:
        error_msg = format_error_message(e)
        return ApiResponse(
            success=False, message=f"Failed to load activations: {str(error_msg)}"
        )


from datetime import datetime, timedelta


@retry_on_temporary_unavailable()
def load_activations_by_period(period: str) -> ApiResponse:
    supabase_client = get_supabase_admin_client()
    team_member_ids = get_salesforce_team_ids(load_settings())

    now = datetime.utcnow()

    if period == "All":
        start_date = None
    elif period == "Today":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "Yesterday":
        start_date = (now - timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        end_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "This Week":
        start_date = now - timedelta(days=now.weekday())
    elif period == "Last Week":
        start_date = now - timedelta(days=now.weekday() + 7)
        end_date = start_date + timedelta(days=7)
    elif period == "This Month":
        start_date = now.replace(day=1)
    elif period == "Last Month":
        last_month = now.replace(day=1) - timedelta(days=1)
        start_date = last_month.replace(day=1)
        end_date = now.replace(day=1)
    elif period == "This Quarter":
        start_date = now.replace(month=(now.month - 1) // 3 * 3 + 1, day=1)
    elif period == "Last Quarter":
        this_quarter_start = now.replace(month=(now.month - 1) // 3 * 3 + 1, day=1)
        start_date = this_quarter_start - timedelta(days=1)
        start_date = start_date.replace(
            month=(start_date.month - 1) // 3 * 3 + 1, day=1
        )
        end_date = this_quarter_start
    else:
        return ApiResponse(success=False, message=f"Invalid period: {period}")

    query = (
        supabase_client.table("Activations")
        .select(
            "id, activated_by_id, status, activated_by, activated_date, account, first_prospecting_activity, prospecting_effort, prospecting_metadata, last_prospecting_activity, active_contact_ids, opportunity, task_ids, event_ids"
        )
        .in_("activated_by_id", team_member_ids)
        .order("first_prospecting_activity", desc=False)
    )

    if start_date:
        query = query.gte("first_prospecting_activity", start_date.isoformat())
    if "end_date" in locals():
        query = query.lt("first_prospecting_activity", end_date.isoformat())

    response = query.execute()

    activations = [
        supabase_dict_to_python_activation(row) for row in response.data
    ] or []
    return ApiResponse(data=activations, success=True)


@retry_on_temporary_unavailable()
def load_active_activations_minimal_by_ids(activation_ids: List[str]) -> ApiResponse:
    supabase_client = get_supabase_admin_client()
    team_member_ids = get_salesforce_team_ids(load_settings())

    try:
        response = (
            supabase_client.table("Activations")
            .select(
                "id, activated_by_id, activated_by, activated_date, account, first_prospecting_activity, prospecting_effort, prospecting_metadata, last_prospecting_activity, active_contact_ids, opportunity, task_ids, event_ids"
            )
            .in_("activated_by_id", team_member_ids)
            .in_("id", activation_ids)
            .order("first_prospecting_activity", desc=False)
            .execute()
        )

        minimal_activations = [
            supabase_dict_to_python_activation(row) for row in response.data
        ] or []

        return ApiResponse(data=minimal_activations, success=True)
    except Exception as e:
        error_msg = format_error_message(e)
        return ApiResponse(
            success=False,
            message=f"Failed to load minimal activations: {str(error_msg)}",
        )


@retry_on_temporary_unavailable()
def load_active_activations_paginated_by_ids(
    page: int,
    rows_per_page: int,
    filter_ids: List[str],
    sort_column: str,
    sort_order: str,
) -> ApiResponse:
    supabase_client = get_supabase_admin_client()
    team_member_ids = get_salesforce_team_ids(load_settings())

    try:
        # Create a set of filter_ids for faster lookup
        filter_id_set = set(filter_ids)

        # Build the query to get sorted IDs
        id_query = (
            supabase_client.table("Activations")
            .select("id")
            .in_("activated_by_id", team_member_ids)
            .neq("status", "Unresponsive")
        )

        # Add sorting
        if sort_column:
            if "." in sort_column:
                json_field, json_key = sort_column.split(".")
                id_query = id_query.order(
                    f"{json_field}->>{json_key}", desc=(sort_order.lower() == "desc")
                )
            else:
                id_query = id_query.order(
                    sort_column, desc=(sort_order.lower() == "desc")
                )
        else:
            id_query = id_query.order("first_prospecting_activity", desc=False)

        # Execute the ID query
        id_response = id_query.execute()

        # Filter and paginate IDs
        filtered_ids = [
            row["id"] for row in id_response.data if row["id"] in filter_id_set
        ]
        total_count = len(filtered_ids)
        start = page * rows_per_page
        end = start + rows_per_page
        paginated_ids = filtered_ids[start:end]

        # Fetch full data for paginated IDs
        if paginated_ids:
            data_query = (
                supabase_client.table("Activations")
                .select("*")
                .in_("id", paginated_ids)
            )
            if sort_column:
                if "." in sort_column:
                    json_field, json_key = sort_column.split(".")
                    data_query = data_query.order(
                        f"{json_field}->>{json_key}",
                        desc=(sort_order.lower() == "desc"),
                    )
                else:
                    data_query = data_query.order(
                        sort_column, desc=(sort_order.lower() == "desc")
                    )
            else:
                data_query = data_query.order("first_prospecting_activity", desc=False)

            data_response = data_query.execute()
            paginated_activations = [
                supabase_dict_to_python_activation(row) for row in data_response.data
            ]
        else:
            paginated_activations = []

        return ApiResponse(
            data={"activations": paginated_activations, "total_count": total_count},
            success=True,
        )
    except Exception as e:
        error_msg = format_error_message(e)
        logging.error(f"Error in load_active_activations_paginated_by_ids: {error_msg}")
        return ApiResponse(
            success=False, message=f"Failed to load activations: {str(error_msg)}"
        )


@retry_on_temporary_unavailable()
def load_active_activations_paginated_with_search(
    page: int,
    rows_per_page: int,
    filter_ids: List[str],
    search_term: str,
    sort_column: str,
    sort_order: str,
) -> ApiResponse:
    supabase_client = get_supabase_admin_client()
    team_member_ids = get_salesforce_team_ids(load_settings())

    try:
        # Create a set of filter_ids for faster lookup
        filter_id_set = set(filter_ids)

        # Build the query to get sorted and searched IDs
        id_query = (
            supabase_client.table("Activations")
            .select("id")
            .in_("activated_by_id", team_member_ids)
            .neq("status", "Unresponsive")
            .ilike("account->>name", f"%{search_term}%")
        )

        # Add sorting
        if sort_column:
            if "." in sort_column:
                json_field, json_key = sort_column.split(".")
                id_query = id_query.order(
                    f"{json_field}->>{json_key}", desc=(sort_order.lower() == "desc")
                )
            else:
                id_query = id_query.order(
                    sort_column, desc=(sort_order.lower() == "desc")
                )
        else:
            id_query = id_query.order("first_prospecting_activity", desc=False)

        # Execute the ID query
        id_response = id_query.execute()

        # Filter and paginate IDs
        filtered_ids = [
            row["id"] for row in id_response.data if row["id"] in filter_id_set
        ]
        total_count = len(filtered_ids)
        start = page * rows_per_page
        end = start + rows_per_page
        paginated_ids = filtered_ids[start:end]

        # Fetch full data for paginated IDs
        if paginated_ids:
            data_query = (
                supabase_client.table("Activations")
                .select("*")
                .in_("id", paginated_ids)
            )
            if sort_column:
                if "." in sort_column:
                    json_field, json_key = sort_column.split(".")
                    data_query = data_query.order(
                        f"{json_field}->>{json_key}",
                        desc=(sort_order.lower() == "desc"),
                    )
                else:
                    data_query = data_query.order(
                        sort_column, desc=(sort_order.lower() == "desc")
                    )
            else:
                data_query = data_query.order("first_prospecting_activity", desc=False)

            data_response = data_query.execute()
            paginated_activations = [
                supabase_dict_to_python_activation(row) for row in data_response.data
            ]
        else:
            paginated_activations = []

        return ApiResponse(
            data={"activations": paginated_activations, "total_count": total_count},
            success=True,
        )
    except Exception as e:
        error_msg = format_error_message(e)
        logging.error(
            f"Error in load_active_activations_paginated_with_search: {error_msg}"
        )
        return ApiResponse(
            success=False, message=f"Failed to load activations: {str(error_msg)}"
        )

def load_single_activation_by_id(activation_id: str) -> ApiResponse:
    supabase_client = get_supabase_admin_client()

    try:
        response = (
            supabase_client.table("Activations")
            .select("*")
            .eq("id", activation_id)
            .limit(1)
            .execute()
        )
        if response.data:
            activation = supabase_dict_to_python_activation(response.data[0])
            return ApiResponse(data=[activation], success=True)
        else:
            return ApiResponse(data=[], success=False, message="Activation not found")
    except Exception as e:
        error_msg = format_error_message(e)
        logging.error(f"Error in load_single_activation_by_id: {error_msg}")
        return ApiResponse(
            success=False, message=f"Failed to load activation: {str(error_msg)}"
        )
    