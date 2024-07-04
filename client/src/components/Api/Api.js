import axios from "axios";

/**
 * @typedef {import('types').ApiResponse} ApiResponse
 */

/**
 * Fetches filter fields for the Task table, filtered by a Python constants file
 * @returns {Promise<ApiResponse>}
 */
export const fetchTaskFilterFields = async () => {
  const response = await axios.get(
    "http://localhost:8000/get_task_criteria_fields",
    {
      validateStatus: () => true,
    }
  );
  return { ...response.data, statusCode: response.status };
};

/**
 * Fetches filter fields for the Event table, filtered by a Python constants file
 * @returns {Promise<ApiResponse>}
 */
export const fetchEventFilterFields = async () => {
  const response = await axios.get(
    "http://localhost:8000/get_event_criteria_fields",
    {
      validateStatus: () => true,
    }
  );
  return { ...response.data, statusCode: response.status };
};

/**
 * Fetches Salesforce users from the Salesforce API
 * @returns {Promise<ApiResponse>}
 */
export const fetchSalesforceUsers = async () => {
  const response = await axios.get(
    "http://localhost:8000/get_salesforce_users",
    {
      validateStatus: () => true,
    }
  );
  return { ...response.data, statusCode: response.status };
};
