import { createClient } from "@supabase/supabase-js";
import {
  checkAuthentication,
  setAuthenticatedUserId,
  getAuthenticatedUserId,
} from "./AuthServices";

const supabaseUrl = process.env.REACT_APP_SUPABASE_URL;
const supabaseAnonKey = process.env.REACT_APP_SUPABASE_ANON_KEY;

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

/**
 * @typedef {import('types').Settings} Settings
 * @typedef {import('types').SalesforceUser} SalesforceUser
 * @typedef {import('types').FilterContainer} FilterContainer
 */

/**
 * @param {SalesforceUser} salesforceUser
 * @returns
 */
export const setupAuthAndUser = async (salesforceUser) => {
  try {
    const { id: salesforceUserId, email, name } = salesforceUser;

    // 2. Attempt to sign in or sign up
    const signInResult = await signInOrSignUp(
      email,
      "generic-password-123",
      salesforceUserId,
      name
    );
    if (!signInResult.success) {
      console.error(
        "Error signing in or signing up user:",
        signInResult.message
      );
      return;
    }

    console.log("Successfully authenticated with Supabase");

    // 3. Upsert custom User table
    const upsertResult = await upsertUser(salesforceUserId, email, name);
    if (!upsertResult.success) {
      console.error(
        "Error upserting User to custom table:",
        upsertResult.message
      );
      return;
    }

    // 4. Now you can proceed with loading or saving settings
    // This is where you'd call your saveSettings function if needed
  } catch (error) {
    console.error("Error in setupAuthAndUser:", error);
  }
};

/**
 * Signs in or signs up a user
 * @param {string} email - User's email
 * @param {string} password - User's password
 * @param {string} salesforceUserId - User's Salesforce ID
 * @param {string} name - User's name
 * @returns {Promise<{ success: boolean, data?: Object, message?: string }>}
 */
export const signInOrSignUp = async (
  email,
  password,
  salesforceUserId,
  name
) => {
  try {
    let { data: signInData, error: signInError } =
      await supabase.auth.signInWithPassword({
        email: email,
        password: password,
      });

    if (signInError && signInError.message === "Invalid login credentials") {
      const { data: signUpData, error: signUpError } =
        await supabase.auth.signUp({
          email: email,
          password: password,
          options: {
            data: {
              salesforce_id: salesforceUserId,
              name: name,
            },
          },
        });

      if (signUpError) throw signUpError;

      signInData = signUpData;
    } else if (signInError) {
      throw signInError;
    }

    setAuthenticatedUserId(signInData.user.id);
    return { success: true, data: signInData };
  } catch (error) {
    console.error("Error in signInOrSignUp:", error);
    return { success: false, message: error.message };
  }
};

/**
 * Saves settings to the database
 * @param {Settings} settings - The settings to save
 * @returns {Promise<{ success: boolean, message: string }>}
 */
export const saveSettings = async (settings) => {
  try {
    await checkAuthentication();
    const formattedSettings = formatSettingsForDatabase(settings);
    const { error } = await supabase
      .from("Settings")
      .upsert(formattedSettings, {
        onConflict: "id",
        returning: "minimal",
      });

    if (error) throw error;

    return { success: true, message: "Settings saved successfully" };
  } catch (error) {
    console.error("Error saving settings:", error);
    return { success: false, message: error.message };
  }
};

/**
 * Retrieves settings from the database
 * @returns {Promise<{ success: boolean, data?: Settings, message?: string }>}
 */
export const fetchSettings = async () => {
  try {
    await checkAuthentication();
    const { data, error } = await supabase
      .from("Settings")
      .select("*")
      .eq("id", getAuthenticatedUserId())
      .single();

    if (error) throw error;

    if (!data) {
      return { success: false, message: "Settings not found" };
    }

    const formattedSettings = formatSettingsForApplication(data);
    return { success: true, data: formattedSettings };
  } catch (error) {
    console.error("Error retrieving settings:", error);
    return { success: false, message: error.message };
  }
};

/**
 * Upserts user data in the database
 * @param {string} salesforceUserId - User's Salesforce ID
 * @param {string} email - User's email
 * @param {string} name - User's name
 * @returns {Promise<{ success: boolean, data?: Object, message?: string }>}
 */
export const upsertUser = async (salesforceUserId, email, name) => {
  try {
    await checkAuthentication();
    const { data, error } = await supabase
      .from("User")
      .upsert(
        {
          id: getAuthenticatedUserId(),
          salesforce_id: salesforceUserId,
          email: email,
          name: name,
        },
        {
          onConflict: "salesforce_id",
          update: {
            email: email,
            name: name,
          },
        }
      )
      .select("id")
      .single();

    if (error) throw error;

    return { success: true, data };
  } catch (error) {
    console.error("Error upserting User:", error);
    return { success: false, message: error.message };
  }
};

// helpers

/**
 * Formats settings from application format to database format
 * @param {Settings} settings - The settings in application format
 * @returns {Object} The formatted settings for database storage
 */
const formatSettingsForDatabase = (settings) => {
  return {
    id: getAuthenticatedUserId(),
    inactivity_threshold: settings.inactivityThreshold ?? 0,
    criteria: JSON.stringify(settings.criteria) ?? "",
    meetings_criteria: JSON.stringify(settings.meetingsCriteria) ?? "",
    meeting_object: settings.meetingObject ?? "",
    activities_per_contact: settings.activitiesPerContact ?? 0,
    contacts_per_account: settings.contactsPerAccount ?? 0,
    tracking_period: settings.trackingPeriod ?? 0,
    activate_by_meeting: settings.activateByMeeting ?? false,
    activate_by_opportunity: settings.activateByOpportunity ?? false,
    salesforce_user_id: settings.salesforceUserId ?? "",
    team_member_ids: JSON.stringify(settings.teamMemberIds) ?? "",
    latest_date_queried: settings.latestDateQueried ?? new Date().toISOString(),
    skip_account_criteria: JSON.stringify(settings.skipAccountCriteria) ?? "",
    skip_opportunity_criteria:
      JSON.stringify(settings.skipOpportunityCriteria) ?? "",
  };
};

/**
 * Formats settings from database format to application format
 * @param {Object} dbSettings - The settings as stored in the database
 * @returns {Settings} The formatted settings for application use
 */
const formatSettingsForApplication = (dbSettings) => {
  return {
    inactivityThreshold: dbSettings.inactivity_threshold,
    criteria: JSON.parse(dbSettings.criteria),
    meetingObject: dbSettings.meeting_object,
    meetingsCriteria: dbSettings.meetings_criteria
      ? JSON.parse(dbSettings.meetings_criteria)
      : dbSettings.meetings_criteria,
    skipAccountCriteria: dbSettings.skip_account_criteria
      ? JSON.parse(dbSettings.skip_account_criteria)
      : undefined,
    skipOpportunityCriteria: dbSettings.skip_opportunity_criteria
      ? JSON.parse(dbSettings.skip_opportunity_criteria)
      : undefined,
    activitiesPerContact: dbSettings.activities_per_contact,
    contactsPerAccount: dbSettings.contacts_per_account,
    trackingPeriod: dbSettings.tracking_period,
    activateByMeeting: dbSettings.activate_by_meeting,
    activateByOpportunity: dbSettings.activate_by_opportunity,
    teamMemberIds: dbSettings.team_member_ids
      ? JSON.parse(dbSettings.team_member_ids)
      : [],
    salesforceUserId: dbSettings.salesforce_user_id,
  };
};
