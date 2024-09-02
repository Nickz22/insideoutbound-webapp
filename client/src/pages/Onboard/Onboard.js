import React, { useEffect } from "react";
import { Box, Paper, Divider } from "@mui/material";
import ProgressTracker from "../../components/ProgressTracker/ProgressTracker";
import {
  fetchLoggedInSalesforceUser,
  fetchSalesforceTasksByUserIds,
} from "../../components/Api/Api";

/**
 * @typedef {import('types').SObject} SObject
 * @typedef {import('types').SObjectField} SObjectField
 * @typedef {import('types').Settings} Settings
 * @typedef {import('types').FilterContainer} FilterContainer
 * @typedef {import('types').ApiResponse} ApiResponse
 * @typedef {import('types').TableData} TableData
 * @typedef {import('types').TableColumn} TableColumn
 * @typedef {import('types').SalesforceUser} SalesforceUser
 */

import Logo from "src/components/Logo/Logo";
import RoleStep from "./RoleStep";
import { useOnboard } from "./OnboardProvider";
import { PROGRESS_STEP } from "./OnboardConstant";

const Onboard = () => {
  // const navigate = useNavigate();
  const {
    step,
    filters,
    gatheringResponses,
    isTransitioning,
    tasks,
    setGatheringResponses,
    setIsTransitioning,
    setTasks,
    handleStepClick
  } = useOnboard();

  useEffect(() => {
    const setSalesforceTasks = async () => {
      try {
        if (tasks.length > 0) return;

        const settings = getSettingsFromResponses();

        /** @type {(string)[]}  */
        const salesforceUserIds = [
          ...(settings.teamMemberIds || []),
        ];

        if (settings.salesforceUserId) {
          salesforceUserIds.push(settings.salesforceUserId)
        }

        if (salesforceUserIds.length === 0 || !salesforceUserIds[0]) return;
        const response = await fetchSalesforceTasksByUserIds(salesforceUserIds);
        if (!response.success) {
          console.error(`Error fetching Salesforce tasks ${response.message}`);
          return;
        }
        setTasks(
          response.data.map(
            /** @param {SObject} task */
            (task) => ({ ...task, id: task.Id })
          )
        );
      } catch (error) {
        console.error("Error fetching Salesforce tasks", error);
      }
    };
    setSalesforceTasks();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [gatheringResponses]);

  useEffect(() => {
    const setLoggedInSalesforceUser = async () => {
      const sfResponse = await fetchLoggedInSalesforceUser();
      if (!sfResponse.success) {
        console.error(`Error fetching Salesforce User: ${sfResponse.message}`);
        return;
      }
      /** @type {SalesforceUser} */
      const salesforceUser = sfResponse.data[0];

      // Update gatheringResponses with Salesforce user ID
      setGatheringResponses((prev) => ({
        ...prev,
        salesforceUserId: { value: salesforceUser.id },
      }));
    };
    setLoggedInSalesforceUser();
  }, []);

  useEffect(() => {
    if (isTransitioning) {
      const timer = setTimeout(() => setIsTransitioning(false), 300); // Match this with transition duration
      return () => clearTimeout(timer);
    }
  }, [isTransitioning]);


  /**
   * Formats the settings data from the form responses.
   * @returns {Settings} The formatted settings data matching the Supabase Settings table structure.
   */
  const getSettingsFromResponses = () => {
    const now = new Date();
    const threeMonthsAgo = new Date(now.setMonth(now.getMonth() - 3));
    return {
      inactivityThreshold: parseInt(
        gatheringResponses["inactivityThreshold"]?.value,
        10
      ), // Tracking Period
      criteria: filters,
      meetingObject: gatheringResponses["meetingObject"]?.value
        .toLowerCase()
        .includes("task")
        ? "Task"
        : "Event",
      meetingsCriteria: gatheringResponses["meetingsCriteria"]?.value,
      activitiesPerContact: parseInt(
        gatheringResponses["activitiesPerContact"]?.value,
        10
      ),
      contactsPerAccount: parseInt(
        gatheringResponses["contactsPerAccount"]?.value,
        10
      ),
      trackingPeriod: parseInt(gatheringResponses["trackingPeriod"]?.value, 10),
      activateByMeeting: gatheringResponses["activateByMeeting"]?.value,
      activateByOpportunity: gatheringResponses["activateByOpportunity"]?.value,
      teamMemberIds: gatheringResponses["teamMemberIds"]?.value?.map(
        (salesforceUser) => salesforceUser.id
      ),
      salesforceUserId: gatheringResponses["salesforceUserId"]?.value,
      latestDateQueried: threeMonthsAgo.toISOString(),
    };
  };

  return (
    <Box sx={{ display: "flex", height: "100vh", width: "100vw" }}>
      {/* Sidebar */}
      <Paper
        elevation={3}
        sx={{
          width: "369px",
          height: "100vh",
          position: "fixed",
          left: 0,
          top: 0,
          zIndex: 1301,
          padding: "28px",
          paddingTop: "47px",
          backgroundColor: "rgba(30, 36, 47, 1)",
          backdropFilter: "blur(5px)",
          overflowY: "auto",
        }}
      >
        <div style={{ display: "flex", flexDirection: "row", justifyContent: "center", width: "100%", marginBottom: "36px" }}>
          <Logo />
        </div>

        <Divider sx={{ backgroundColor: "rgba(135, 159, 202, 0.5)", marginBottom: "41px" }} />
        <ProgressTracker
          steps={PROGRESS_STEP}
          currentStep={step}
          onStepClick={handleStepClick}
          orientation="vertical"
        />
      </Paper>
      {step === 1 && (<RoleStep />)}
    </Box>
  );
};

export default Onboard;
