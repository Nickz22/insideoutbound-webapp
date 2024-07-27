import { supabase } from "./SupabaseServices";
import { getRefreshToken } from "src/components/Api/Api";
/**
 * @typedef {import('types').ApiResponse} ApiResponse
 */

let authenticatedUserId = "";

/**
 * Set the authenticated user ID for supabase operations
 * @param {string} userId
 */
export const setAuthenticatedUserId = (userId) => {
  authenticatedUserId = userId;
};

export const getAuthenticatedUserId = () => {
  return authenticatedUserId;
};

export const refreshAuth = async () => {
  try {
    /** @type {ApiResponse} */
    const response = await getRefreshToken();
    if (response.statusCode !== 200) {
      window.location.href = "/";
      return false;
    }

    // Refresh Supabase session
    const { data, error } = await supabase.auth.refreshSession();
    if (error) throw error;

    setAuthenticatedUserId(data.user.id);
    return true;
  } catch (error) {
    console.error("Error refreshing authentication:", error);
    throw error;
  }
};

export const checkAuthentication = async () => {
  if (!getAuthenticatedUserId()) {
    const refreshed = await refreshAuth();
    if (!refreshed) {
      throw new Error("Authentication failed. Please sign in again.");
    }
  }
};

export const handleAuthError = async () => {
  const refreshed = await refreshAuth();
  if (!refreshed) {
    // Redirect to login page if refresh fails
    window.location.href = "/";
    return false;
  }
  return true;
};
