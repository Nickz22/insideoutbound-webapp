import React, { useState, useEffect, useRef } from "react";
import { Box, Paper, Typography, Divider } from "@mui/material";
import { useNavigate } from "react-router-dom";
import ProspectingCriteriaSelector from "../components/ProspectingCriteriaSelector/ProspectingCriteriaSelector";
import InfoGatheringStep from "../components/InfoGatheringStep/InfoGatheringStep";
import ProgressTracker from "../components/ProgressTracker/ProgressTracker";
import {
  fetchLoggedInSalesforceUser,
  fetchSalesforceTasksByUserIds,
  fetchTaskFields,
  fetchTaskFilterFields,
  generateCriteria,
  saveSettings as saveSettingsToSupabase,
} from "../components/Api/Api";

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

import { ONBOARD_WIZARD_STEPS } from "../utils/c";
import Logo from "src/components/Logo/Logo";

const REQUIRED_PROSPECTING_CATEGORIES = [
  "Inbound Call",
  "Outbound Call",
  "Inbound Email",
  "Outbound Email",
];

const Onboard = () => {
  const navigate = useNavigate();
  const [step, setStep] = useState(1); // Start from step 1
  const [inputValues, setInputValues] = useState({ userRole: "" });
  const [tableData, setTableData] = useState(/** @type {TableData | null} */(null));
  /** @type {[FilterContainer[], Function]} */
  const [filters, setFilters] = useState(
    REQUIRED_PROSPECTING_CATEGORIES.map((category) => ({
      name: category,
      filters: [],
      filterLogic: "",
      direction: category.toLowerCase().includes("inbound")
        ? "Inbound"
        : "Outbound",
    }))
  );
  /** @type {[{ [key: string]: any }, function]} */
  const [gatheringResponses, setGatheringResponses] = useState({});
  const [isTransitioning, setIsTransitioning] = useState(false);
  /** @type {[TableData, Function]} */
  const [categoryFormTableData, setCategoryFormTableData] = useState({
    availableColumns: [],
    columns: [],
    data: [],
    selectedIds: new Set(),
  });
  /** @type {[SObject[], Function]} */
  const [tasks, setTasks] = useState([]);
  const taskSObjectFields = useRef([]);
  const taskFilterFields = useRef([]);

  useEffect(() => {
    const setInitialCategoryFormTableData = async () => {
      taskSObjectFields.current =
        taskSObjectFields.current.length > 0
          ? taskSObjectFields.current
          : (await fetchTaskFields()).data?.map(
            /** @param {SObjectField} field */
            (field) => ({
              id: field.name,
              label: field.label,
              dataType: field.type,
            })
          );
      setCategoryFormTableData({
        availableColumns: taskSObjectFields.current,
        columns:
          categoryFormTableData.columns.length > 0
            ? categoryFormTableData.columns
            : [
              {
                id: "select",
                label: "Select",
                dataType: "select",
              },
              {
                id: "Subject",
                label: "Subject",
                dataType: "string",
              },
              {
                id: "Status",
                label: "Status",
                dataType: "string",
              },
              {
                id: "TaskSubtype",
                label: "TaskSubtype",
                dataType: "string",
              },
            ],
        data: tasks,
        selectedIds: new Set(),
      });
    };
    setInitialCategoryFormTableData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tasks]);

  useEffect(() => {
    const setTaskFilterFields = async () => {
      taskFilterFields.current =
        taskFilterFields.current.length > 0
          ? taskFilterFields.current
          : (await fetchTaskFilterFields()).data;
    };
    setTaskFilterFields();
  }, []);

  useEffect(() => {
    const setSalesforceTasks = async () => {
      try {
        if (tasks.length > 0) return;

        const settings = getSettingsFromResponses();
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

  /** @param {number} clickedStep */
  const handleStepClick = (clickedStep) => {
    if (clickedStep < step) {
      setStep(clickedStep);
    }
  };

  const saveSettings = async () => {
    try {
      /** @type {Settings} */
      let settings = getSettingsFromResponses();
      settings = Object.keys(settings).reduce((acc, key) => {
        acc[key] =
          settings[key] === "Yes"
            ? true
            : settings[key] === "No"
              ? false
              : settings[key];
        return acc;
      }, {});

      const result = await saveSettingsToSupabase(settings);

      if (!result.success) {
        throw new Error(result.message);
      }

      console.log("Settings saved successfully");
      navigate("/app/settings");
    } catch (error) {
      console.error("Error saving settings:", error);
    }
  };

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
      userRole: gatheringResponses["userRole"]?.value
    };
  };

  const handleNext = () => {
    setStep(step + 1);
  };

  /**
   * Corresponds to the onboarding wizard step question, if the question is composed of an array of questions,
   * `responses` will be an array of responses, else it will be a single response
   * @param {[{label: string, value: string}]} response
   * @returns {void}
   */
  const handleInfoGatheringComplete = (response) => {
    setGatheringResponses(
      /**
       * @param {{ [key: string]: any }} prev
       */
      (prev) => {
        const newResponses = { ...prev };
        // Handle the case where we have multiple responses
        response.forEach((res) => {
          newResponses[res.label] = { value: res.value };
        });
        return newResponses;
      }
    );
    handleNext();
  };

  /**
   * @param {FilterContainer} filterContainer
   */
  const handleProspectingFilterChanged = (updatedFilter) => {
    setFilters((prev) =>
      prev.map((filter) =>
        filter.name === updatedFilter.name ? updatedFilter : filter
      )
    );

    setGatheringResponses((prev) => {
      const newResponses = { ...prev };
      if (!newResponses.criteria) {
        newResponses.criteria = { value: [] };
      }
      const criteriaIndex = newResponses.criteria.value.findIndex(
        (criteria) => criteria.name === updatedFilter.name
      );
      if (criteriaIndex !== -1) {
        newResponses.criteria.value[criteriaIndex] = updatedFilter;
      } else {
        newResponses.criteria.value.push(updatedFilter);
      }
      return newResponses;
    });
  };

  const handleTaskSelection = async (selectedTaskIds) => {
    try {
      const selectedTasks = tasks.filter((task) =>
        selectedTaskIds.includes(task.id)
      );
      const response = await generateCriteria(
        selectedTasks,
        categoryFormTableData.columns
      );
      return response.data[0];
    } catch (error) {
      console.error("Error generating criteria:", error);
    }
  };

  const renderStep = () => {
    if (step <= ONBOARD_WIZARD_STEPS.length) {
      return (
        <InfoGatheringStep
          key={step}
          step={step}
          stepData={ONBOARD_WIZARD_STEPS[step - 1]}
          onTableDisplay={handleTableDisplay}
          onComplete={handleInfoGatheringComplete}
          settings={getSettingsFromResponses()}
          inputValues={inputValues}
          setInputValues={setInputValues}
          tableData={tableData}
          setTableData={setTableData}
        />
      );
    } else if (step === ONBOARD_WIZARD_STEPS.length + 1) {
      return (
        <>
          <Typography
            variant="h4"
            component="h2"
            gutterBottom
            sx={{
              fontWeight: "500",
              fontSize: "40px",
              lineHeight: "1.78",
              letterSpacing: "-1.2px",
            }}
          >
            Prospecting Categories
          </Typography>
          <Typography variant="body1" paragraph>
            Define criteria by which we will recognize an Inbound Call, Outbound
            Call, Inbound Email and Outbound Email.
          </Typography>
          <ProspectingCriteriaSelector
            title="Prospecting Activity Criteria"
            initialFilterContainers={filters}
            filterFields={taskFilterFields.current}
            tableData={categoryFormTableData}
            onFilterChange={handleProspectingFilterChanged}
            onTaskSelection={handleTaskSelection}
            onSave={saveSettings}
          />
        </>
      );
    } else {
      return <div>Invalid step</div>;
    }
  };

  const getProgressSteps = () => {
    return [
      ...ONBOARD_WIZARD_STEPS,
      { title: "Prospecting Categories" },
      { title: "Review" },
    ];
  };

  const handleTableDisplay = () => {
    setIsTransitioning(true);
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
          boxSizing: "border-box"
        }}
      >
        <div style={{ display: "flex", flexDirection: "row", justifyContent: "center", width: "100%", marginBottom: "36px" }}>
          <Logo />
        </div>

        <Divider sx={{ backgroundColor: "rgba(135, 159, 202, 0.5)", marginBottom: "41px" }} />
        <ProgressTracker
          steps={getProgressSteps()}
          currentStep={step}
          onStepClick={handleStepClick}
          orientation="vertical"
        />
      </Paper>
      {/* <Box sx={{ flexGrow: 1, marginLeft: "250px" }}>
        <Dialog
          open
          onClose={() => {
            console.log("closing");
          }}
          PaperProps={{
            style: dialogStyle,
          }}
          fullWidth
          maxWidth={false}
        >
          <DialogContent
            style={{
              padding: isLargeDialogStep() ? "24px" : "16px",
              transition: "padding 0.3s ease-in-out",
              height: "100%",
              overflow: "auto",
            }}
          >
            {renderStep()}
          </DialogContent>
        </Dialog>
      </Box> */}
      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
          flex: 1,
          backgroundColor: "white",
          width: "calc(100% - 369px)",
          maxWidth: "calc(100% - 369px)",
          overflow: "auto",
          marginLeft: "369px",
          position: "relative",
          alignItems: "start",
          justifyContent: "start",
          paddingTop: "37px",
          paddingBottom: "37px",
          paddingLeft: "68px",
          paddingRight: "68px",
          boxSizing: "border-box"
        }}
      >
        <div
          style={{
            width: "100%",
            boxSizing: "border-box"
          }}
        >
          {renderStep()}
        </div>
      </Box>
    </Box>
  );
};

export default Onboard;