import axios from "axios";
import config from "../../config";
import { handleAuthError } from "./../../services/AuthServices";

/**
 * @typedef {import('types').Settings} Settings
 */

const api = axios.create({
    baseURL: config.apiBaseUrl,
});

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
            if (response.data.error.toLowerCase().includes("session")) {
                window.location.href = "/";
                return Promise.reject(response.data);
            }

            const originalRequest = response.config;
            const refreshed = await handleAuthError();
            if (refreshed) {
                return api(originalRequest);
            } else {
                // Redirect to login page if refresh failed
                window.location.href = "/";
                return Promise.reject(response.data);
            }
        }
        return response;
    },
    async (error) => {
        if (error.response) {
            if (error.response.data.message.toLowerCase().includes("session")) {
                window.location.href = "/";
                return Promise.reject(error.response.data);
            }
            // The server responded with a status code outside the 2xx range
            console.error(
                "Server error:",
                error.response.status,
                error.response.data
            );
            return Promise.reject(error.response.data);
        } else if (error.request) {
            // The request was made but no response was received
            console.error("No response received:", error.request);
            return Promise.reject(new Error("No response from server"));
        } else {
            // Something happened in setting up the request that triggered an Error
            console.error("Request setup error:", error.message);
            return Promise.reject(error);
        }
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

export const getUserTimezone = async () => {
    return Promise.resolve({
        success: true,
        data: Intl.DateTimeFormat().resolvedOptions().timeZone,
    });
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
 * @param {"Today" | "Yesterday" | "This Week" | "Last Week" | "This Month" | "Last Month" | "This Quarter" | "Last Quarter"} period
 * @param {string[]} filterIds
 * @returns {Promise<ApiResponse>}
 */
export const fetchProspectingActivities = async (period, filterIds = []) => {
    const response = await api.post("/get_prospecting_activities_by_ids", {
        period,
        filterIds,
    });
    return { ...response.data, statusCode: response.status };
};

/**
 * Fetches paginated prospecting activities filtered by IDs
 * @param {string[]} filterIds - Array of IDs to filter by
 * @param {number} page - Page number (0-indexed)
 * @param {number} rowsPerPage - Number of rows per page
 * @param {string} searchTerm - Search term
 * @param {string} sortColumn - Column to sort by
 * @param {string} sortOrder - Sort order ('asc' or 'desc')
 * @returns {Promise<ApiResponse>}
 */
export const getPaginatedProspectingActivities = async (
    filterIds = [],
    page = 0,
    rowsPerPage = 10,
    searchTerm = "",
    sortColumn = "",
    sortOrder = "asc"
) => {
    const response = await api.post("/get_paginated_prospecting_activities", {
        filterIds,
        page,
        rowsPerPage,
        searchTerm,
        sortColumn,
        sortOrder,
    });
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
 * @param {string} timezone
 * @returns {Promise<{ statusCode: number }>}
 */
export const processNewProspectingActivity = async (timezone) => {
    try {
        const response = await api.post("/process_new_prospecting_activity", {
            timezone,
        });
        return { statusCode: response.status };
    } catch (error) {
        console.error("Error in processNewProspectingActivity:", error);
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
 * Fetches the Salesforce users who have been designated as team members in settings
 * @returns {Promise<ApiResponse>}
 */
export const fetchSalesforceTeam = async () => {
    const response = await api.post(
        "/get_salesforce_team",
        {
            headers: {
                "Content-Type": "application/json",
                "X-Session-Token": localStorage.getItem("sessionToken"),
            },
            validateStatus: () => true,
        }
    );
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

/**
 * @returns {Promise<ApiResponse>}
 */
export const createPaymentIntent = async () => {
    const response = await api.post("/create-payment-intent");
    return { ...response.data, statusCode: response.status };
};

/**
 * @param {string} userEmail
 * @returns {Promise<ApiResponse>}
 */
export const startStripePaymentSchedule = async (userEmail) => {
    const response = await api.post("/start_stripe_payment_schedule", {
        userEmail,
    });
    return { ...response.data, statusCode: response.status };
};

/**
 * @param {string} userId
 * @returns {Promise<ApiResponse>}
 */
export const setSupabaseUserStatusToPaid = async (userId) => {
    const response = await api.post("/set_supabase_user_status_to_paid", {
        userId,
    });
    return { ...response.data, statusCode: response.status };
};

/**
 * @param {string} userId
 * @param {string} email
 * @returns {Promise<ApiResponse>}
 */
export const pauseStripePaymentSchedule = async (userId, email) => {
    const response = await api.post("/pause_stripe_payment_schedule", {
        userId,
        email,
    });
    return { ...response.data, statusCode: response.status };
};

/**
 * Performs an admin login with the given user ID
 * @param {string} userId - The ID of the user to login as
 * @returns {Promise<ApiResponse>}
 */
export const adminLogin = async (userId) => {
    try {
        const response = await api.post("/admin_login", { userId });
        return { ...response.data, statusCode: response.status };
    } catch (error) {
        console.error("Error during admin login:", error);
        throw error;
    }
};
