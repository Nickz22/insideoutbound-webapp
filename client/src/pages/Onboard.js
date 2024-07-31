import React, { useState, useEffect, useRef, useCallback } from "react";
import {
  CircularProgress,
  Dialog,
  DialogContent,
  Box,
  Typography,
  Paper,
} from "@mui/material";
import { useNavigate } from "react-router-dom";
import CategoryForm from "../components/ProspectingCategoryForm/ProspectingCategoryForm";
import CategoryOverview from "../components/ProspectingCategoryOverview/ProspectingCategoryOverview";
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

import {
  PROSPECTING_ACTIVITY_FILTER_TITLE_PLACEHOLDERS,
  ONBOARD_WIZARD_STEPS,
} from "../utils/c";

/**
 * @param {{ categoryFormTableData: TableData, setSelectedColumns: Function, onAddCategory: Function, onDone: React.MouseEventHandler}} props
 */
const CategoryFormWithHeader = ({
  categoryFormTableData,
  setSelectedColumns,
  onAddCategory,
  onDone,
}) => {
  return (
    <Box>
      <Typography variant="h5" gutterBottom sx={{ mb: 3 }}>
        Prospecting Activity Criteria
      </Typography>
      <CategoryForm
        initialTableData={categoryFormTableData}
        setSelectedColumns={setSelectedColumns}
        onAddCategory={onAddCategory}
        onDone={onDone}
      />
    </Box>
  );
};

const Onboard = () => {
  const navigate = useNavigate();
  const [step, setStep] = useState(1); // Start from step 1
  /** {@type {[Map<string, List<SObject>, Function]}} */
  const [categories, setCategories] = useState(new Map());
  /** @type {[FilterContainer[], Function]} */
  const [filters, setFilters] = useState([]);
  /** @type {[{ [key: string]: any }, function]} */
  const [gatheringResponses, setGatheringResponses] = useState({});
  const placeholderIndexRef = useRef(0);
  const [isLargeDialog, setIsLargeDialog] = useState(false);
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
  const [isProcessingCategories, setIsProcessingCategories] = useState(false);

  useEffect(() => {
    const setInitialCategoryFormTableData = async () => {
      taskSObjectFields.current =
        taskSObjectFields.current.length > 0
          ? taskSObjectFields.current
          : (await fetchTaskFields()).data.map(
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
          settings.salesforceUserId,
        ];
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

  useEffect(() => {
    const processCategories = async () => {
      if (categories.size === 4 && isProcessingCategories) {
        try {
          const selectedColumns = categoryFormTableData.columns;
          const filterContainersPromises = Array.from(categories.entries()).map(
            async ([category, tasks]) => {
              try {
                const response = await generateCriteria(tasks, selectedColumns);
                return {
                  ...response.data[0],
                  name: category,
                  direction: category.toLowerCase().includes("inbound")
                    ? "Inbound"
                    : "Outbound",
                };
              } catch (error) {
                console.error("Error processing category:", category, error);
                return {
                  name: category,
                  filters: [{ field: "", operator: "", value: "" }],
                  direction: category.toLowerCase().includes("inbound")
                    ? "Inbound"
                    : "Outbound",
                };
              }
            }
          );

          const filterContainers = await Promise.all(filterContainersPromises);
          setFilters(filterContainers);
          setGatheringResponses((prev) => ({
            ...prev,
            criteria: { value: filterContainers },
          }));
        } finally {
          setIsProcessingCategories(false);
          handleNext();
        }
      }
    };

    processCategories();
  }, [categories, isProcessingCategories]);

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
   * @returns {Object} The formatted settings data matching the Supabase Settings table structure.
   */
  const getSettingsFromResponses = () => {
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
  const handleProspectingFilterChanged = (filterContainer) => {
    setFilters(
      /** @param {FilterContainer[]} prev */
      (prev) =>
        prev.map((prevFilterContainer) => {
          const isSameFilter =
            prevFilterContainer?.name === filterContainer.name;
          return isSameFilter ? filterContainer : prevFilterContainer;
        })
    );
    try {
      setGatheringResponses(
        /** @param {{ [key: string]: any }} prev */
        (prev) => {
          const newResponses = { ...prev };
          newResponses["criteria"].value = prev["criteria"].value.map(
            /**
             * @param {FilterContainer} prevCriteria
             */
            (prevCriteria) => {
              const isSameCriteria =
                prevCriteria?.name === filterContainer.name;
              return isSameCriteria ? filterContainer : prevCriteria;
            }
          );
          return newResponses;
        }
      );
    } catch (e) {
      console.error("Error updating criteria", e);
    }
  };

  const setSelectedColumns = useCallback(
    /** @param {TableColumn[]} newColumns */
    (newColumns) => {
      setCategoryFormTableData(
        /** @param {TableData} prev */
        (prev) => ({ ...prev, columns: newColumns })
      );
    },
    []
  );

  /**
   *
   * @param {string} category
   * @param {Set<string>} selectedTaskIds
   * @returns
   */
  const addCategory = (category, selectedTaskIds) => {
    return new Promise((resolve) => {
      const newCategories = new Map(categories);
      const selectedTasks = tasks.filter((task) =>
        selectedTaskIds.has(task.id)
      );
      newCategories.set(category, selectedTasks);

      const remainingTasks = tasks.filter(
        (task) => !selectedTaskIds.has(task.id)
      );

      setCategories(newCategories);
      setTasks(remainingTasks);
      setCategoryFormTableData((prev) => {
        const newData = {
          ...prev,
          data: remainingTasks,
          selectedIds: new Set(),
        };
        resolve(newData);
        return newData;
      });
    });
  };

  const handleProspectingCategoriesComplete = async () => {
    setIsProcessingCategories(true);
  };

  const renderStep = () => {
    if (isProcessingCategories) {
      return (
        <Box
          sx={{
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            height: "100%",
          }}
        >
          <CircularProgress />
          <Typography variant="h6" sx={{ ml: 2 }}>
            Processing categories...
          </Typography>
        </Box>
      );
    }

    if (step <= ONBOARD_WIZARD_STEPS.length) {
      return (
        <InfoGatheringStep
          key={step}
          stepData={ONBOARD_WIZARD_STEPS[step - 1]}
          onTableDisplay={handleTableDisplay}
          onComplete={handleInfoGatheringComplete}
          settings={getSettingsFromResponses()}
        />
      );
    } else if (step === ONBOARD_WIZARD_STEPS.length + 1) {
      return (
        <CategoryFormWithHeader
          categoryFormTableData={categoryFormTableData}
          setSelectedColumns={setSelectedColumns}
          onAddCategory={addCategory}
          onDone={handleProspectingCategoriesComplete}
        />
      );
    } else if (step === ONBOARD_WIZARD_STEPS.length + 2) {
      return (
        <CategoryOverview
          proposedFilterContainers={filters}
          onSave={saveSettings}
          taskFilterFields={taskFilterFields.current}
          onFilterChange={handleProspectingFilterChanged}
        />
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

  const getPlaceholder = () => {
    const placeholder =
      PROSPECTING_ACTIVITY_FILTER_TITLE_PLACEHOLDERS[
        placeholderIndexRef.current
      ];
    placeholderIndexRef.current =
      (placeholderIndexRef.current + 1) %
      PROSPECTING_ACTIVITY_FILTER_TITLE_PLACEHOLDERS.length;
    return placeholder;
  };

  const isLargeDialogStep = () => {
    return isLargeDialog || step > ONBOARD_WIZARD_STEPS.length;
  };

  const dialogStyle = {
    transition: "all 0.3s ease-in-out",
    boxShadow: "0 4px 20px rgba(0,0,0,0.1)",
    border: "1px solid #e0e0e0",
    ...(isLargeDialogStep()
      ? {
          maxWidth: "60vw",
          width: "60vw",
          maxHeight: "90vh",
          height: "90vh",
        }
      : {
          maxWidth: "600px", // Adjust as needed for small dialog
          width: "100%",
          maxHeight: "80vh",
          height: "auto",
        }),
  };

  /**
   * @param {boolean} isDisplayed
   */
  const handleTableDisplay = (isDisplayed) => {
    setIsTransitioning(true);
    setIsLargeDialog(isDisplayed);
  };

  return (
    <Box sx={{ display: "flex", height: "100vh" }}>
      <Paper
        elevation={3}
        sx={{
          width: "250px",
          height: "100vh",
          position: "fixed",
          left: 0,
          top: 0,
          zIndex: 1301,
          padding: "16px",
          backgroundColor: "rgba(255, 255, 255, 0.9)",
          backdropFilter: "blur(5px)",
          overflowY: "auto",
        }}
      >
        <ProgressTracker
          steps={getProgressSteps()}
          currentStep={step}
          onStepClick={handleStepClick}
          orientation="vertical"
        />
      </Paper>
      <Box sx={{ flexGrow: 1, marginLeft: "250px" }}>
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
      </Box>
    </Box>
  );
};

export default Onboard;
