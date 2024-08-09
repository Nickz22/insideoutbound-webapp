import axios from "axios";
import config from "../../config";
import { handleAuthError } from "./../../services/AuthServices";

/**
 * @typedef {import('types').Settings} Settings
 */

const api = axios.create({
  baseURL: config.apiBaseUrl,
});

/**
 * the history replace looks very strange here
 */
const getSessionToken = () => {
  try {
    const urlParams = new URLSearchParams(window.location.search);
    const sessionToken = urlParams.get("session_token");

    if (sessionToken) {
      localStorage.setItem("sessionToken", sessionToken);
      // Clean up the URL
      window.history.replaceState({}, document.title, "/app/prospecting");
    }

    return localStorage.getItem("sessionToken");
  } catch (e) {
    window.location.href = "/";
  }
};

api.interceptors.request.use((config) => {
  try {
    const sessionToken = getSessionToken();

    if (sessionToken) {
      config.headers["X-Session-Token"] = sessionToken;
    }

    return config;
  } catch (error) {
    console.error("Error in request interceptor:", error);
    return Promise.reject(error);
  }
});

api.interceptors.response.use(
  async (response) => {
    // Check if the response contains authentication error information
    if (response.data && response.data.type === "AuthenticationError") {
      const originalRequest = response.config;
      if (!originalRequest._retry) {
        originalRequest._retry = true;
        const refreshed = await handleAuthError();
        if (refreshed) {
          return api(originalRequest);
        } else {
          // Redirect to login page if refresh failed
          window.location.href = "/";
          return Promise.reject(response.data);
        }
      }
      // If this is already a retry, redirect to login page
      window.location.href = "/";
      return Promise.reject(response.data);
    }
    return response;
  },
  (error) => {
    // For actual errors (network issues, etc.), just log them
    console.error("Axios error:", error);
    return Promise.reject(error);
  }
);

api.defaults.withCredentials = true;
/**
 * @typedef {import('types').ApiResponse} ApiResponse
 * @typedef {import('types').TableColumn} TableColumn
 */

export const logout = async () => {
  const response = await api.post("/logout");
  if (response.data.success) {
    localStorage.removeItem("sessionToken");
    window.location.href = "/";
  }
};

// getInstanceUrl
/**
 * @returns {Promise<ApiResponse>}
 */
export const getInstanceUrl = async () => {
  const response = await api.get("/get_instance_url");
  return { ...response.data, statusCode: response.status };
};

export const getLoggedInUser = async () => {
  const response = await api.get("/get_salesforce_user");
  return { ...response.data, statusCode: response.status };
};

/**
 * @returns {Promise<ApiResponse>}
 */
export const getRefreshToken = async () => {
  const response = await api.post(`${config.apiBaseUrl}/refresh_token`);
  localStorage.setItem("sessionToken", response.data.data[0].session_token);
  return { ...response.data, statusCode: response.status };
};

/**
 * Fetches prospecting activities
 * @returns {Promise<ApiResponse>}
 */
export const fetchProspectingActivities = async () => {
  const response = await api.get("/get_prospecting_activities");
  return { ...response.data, statusCode: response.status };
};

/**
 * Fetches settings
 * @returns {Promise<ApiResponse>}
 */
export const fetchSettings = async () => {
  const response = await api.get("/get_settings");
  return { ...response.data, statusCode: response.status };
};

/**
 * saves settings
 * @param {Settings} settings
 * @returns {Promise<ApiResponse>}
 */
export const saveSettings = async (settings) => {
  const response = await api.post("/save_settings", settings);
  return { ...response.data, statusCode: response.status };
};

/**
 * Fetches and updates prospecting activity data
 * @returns {Promise<ApiResponse>}
 */
export const fetchAndUpdateProspectingActivity = async () => {
  try {
    const response = await api.post("/fetch_prospecting_activity");
    return { ...response.data, statusCode: response.status };
  } catch (error) {
    // This will catch any errors that weren't handled by the interceptor
    console.error("Error in fetchAndUpdateProspectingActivity:", error);
    throw error;
  }
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
 * Fetches task query count from the Salesforce API
 * @param {Object} criteria - The criteria for the query
 * @param {String[]} salesforceUserIds - The Salesforce user IDs
 * @returns {Promise<ApiResponse>}
 */
export const getTaskQueryCount = async (criteria, salesforceUserIds) => {
  try {
    const response = await api.post(
      "/get_task_query_count",
      {
        criteria,
        salesforce_user_ids: salesforceUserIds,
      },
      {
        headers: {
          "Content-Type": "application/json",
          "X-Session-Token": localStorage.getItem("sessionToken"),
        },
        validateStatus: () => true,
      }
    );
    return { ...response.data, statusCode: response.status };
  } catch (error) {
    console.error("Error in getTaskQueryCount:", error);
    throw error;
  }
};

/**
 * Retrieves the JWT from the server
 * @returns {Promise<ApiResponse>}
 */
export const fetchJwt = async () => {
  const response = await api.get("/get_jwt", {
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
export const fetchLoggedInSalesforceUser = async () => {
  const response = await api.get("/get_salesforce_user", {
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
  const response = await api.post("/generate_filters", {
    tasksOrEvents: tasksOrEvents,
    selectedColumns: columns,
  });
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
    }
  );
  return { ...response.data, statusCode: response.status };
};

/**
 * Deletes all of the logged in user's activations
 * @returns {Promise<ApiResponse>}
 */
export const deleteAllActivations = async () => {
  const response = await api.post("/delete_all_prospecting_activity");
  return { ...response.data, statusCode: response.status };
};
