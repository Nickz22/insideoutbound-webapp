// src/Api.js

import axios from "axios";
import config from "../../config";

const api = axios.create({
  baseURL: config.apiBaseUrl,
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (
      error.response.status === 401 &&
      error.response.data.code === "TOKEN_EXPIRED" &&
      !originalRequest._retry
    ) {
      originalRequest._retry = true;
      try {
        await axios.post(`${config.apiBaseUrl}/refresh_token`);
        return api(originalRequest);
      } catch (error) {
        // Redirect to login page if refresh fails
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

api.defaults.withCredentials = true;
/**
 * @typedef {import('types').ApiResponse} ApiResponse
 * @typedef {import('types').TableColumn} TableColumn
 */

/**
 * @param {string} codeVerifier
 * @param {boolean} isSandbox
 * @returns {Promise<ApiResponse>}
 */
export const storeCodeVerifier = async (codeVerifier, isSandbox) => {
  await api.post(`${config.apiBaseUrl}/store_code_verifier`, {
    code_verifier: codeVerifier,
    is_sandbox: isSandbox,
  });

  return { data: [], success: true, message: "", statusCode: 200 };
};

/**
 * Fetches filter fields for the Task table, filtered by a Python constants file
 * @returns {Promise<ApiResponse>}
 */
export const fetchTaskFilterFields = async () => {
  const response = await api.get("/get_criteria_fields", {
    params: { object: "Task" },
    validateStatus: () => true,
  });
  return { ...response.data, statusCode: response.status };
};

/**
 * Fetches filter fields for the Event table, filtered by a Python constants file
 * @returns {Promise<ApiResponse>}
 */
export const fetchEventFilterFields = async () => {
  const response = await api.get("/get_criteria_fields", {
    params: { object: "Event" },
    validateStatus: () => true,
  });
  return { ...response.data, statusCode: response.status };
};

/**
 * Fetches Salesforce users from the Salesforce API
 * @returns {Promise<ApiResponse>}
 */
export const fetchSalesforceUsers = async () => {
  const response = await api.get("/get_salesforce_users", {
    validateStatus: () => true,
  });
  return { ...response.data, statusCode: response.status };
};

/**
 * Fetches Salesforce tasks from the Salesforce API
 * @param {string[]} userIds
 * @returns {Promise<ApiResponse>}
 */
export const fetchSalesforceTasksByUserIds = async (userIds) => {
  const response = await api.get("/get_salesforce_tasks_by_user_ids", {
    params: { user_ids: userIds },
    validateStatus: () => true,
  });
  return { ...response.data, statusCode: response.status };
};

/**
 * Fetches Salesforce events from the Salesforce API
 * @param {string[]} userIds
 * @returns {Promise<ApiResponse>}
 */
export const fetchSalesforceEventsByUserIds = async (userIds) => {
  const response = await api.get("/get_salesforce_events_by_user_ids", {
    params: { user_ids: userIds },
    validateStatus: () => true,
  });
  return { ...response.data, statusCode: response.status };
};

/**
 * Fetches the logged in Salesforce user's ID
 * @returns {Promise<ApiResponse>}
 */
export const fetchLoggedInSalesforceUserId = async () => {
  const response = await api.get("/get_salesforce_user_id", {
    validateStatus: () => true,
  });
  return { ...response.data, statusCode: response.status };
};

/**
 * Fetches the logged in Salesforce user's team members
 * @returns {Promise<ApiResponse>}
 */
export const fetchTaskFields = async () => {
  const response = await api.get("/get_task_fields", {
    validateStatus: () => true,
  });
  return { ...response.data, statusCode: response.status };
};

/**
 * Fetches the logged in Salesforce user's team members
 * @returns {Promise<ApiResponse>}
 */
export const fetchEventFields = async () => {
  const response = await api.get("/get_event_fields", {
    validateStatus: () => true,
  });
  return { ...response.data, statusCode: response.status };
};

/**
 * Fetches the logged in Salesforce user's team members
 * @param {Record<string, string>[]} tasksOrEvents
 * @param {TableColumn[]} columns
 * @returns {Promise<ApiResponse>}
 */
export const generateCriteria = async (tasksOrEvents, columns) => {
  const response = await api.post(
    "/generate_filters",
    {
      tasksOrEvents: tasksOrEvents,
      selectedColumns: columns,
    },
    {
      validateStatus: () => true,
    }
  );
  return { ...response.data, statusCode: response.status };
};

/**
 * Summarizes a list of activations in a shape that the Prospecting page can use to show metric cards
 * @param {string[]} activation_ids
 * @returns {Promise<ApiResponse>}
 */
export const generateActivationSummary = async (activation_ids) => {
  const response = await api.get(
    "/get_prospecting_activities_filtered_by_ids",
    {
      params: { activation_ids: activation_ids },
      validateStatus: () => true,
    }
  );
  return { ...response.data, statusCode: response.status };
};
