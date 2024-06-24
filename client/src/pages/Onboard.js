import React, { useState, useEffect, useRef } from "react";
import { Dialog, DialogContent, Box, Typography } from "@mui/material";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import CategoryForm from "../components/ProspectingCategoryForm/ProspectingCategoryForm";
import CategoryOverview from "../components/ProspectingCategoryOverview/ProspectingCategoryOverview";
import InfoGatheringStep from "../components/InfoGatheringStep/InfoGatheringStep";

/**
 * @typedef {import('types').Settings} Settings
 */

import {
  FILTER_OPERATOR_MAPPING,
  PROSPECTING_ACTIVITY_FILTER_TITLE_PLACEHOLDERS,
  MOCK_TASK_DATA,
  ONBOARD_WIZARD_STEPS,
} from "../utils/c";
import {
  fetchEventFilterFields,
  fetchTaskFilterFields,
} from "../components/Api/Api";

const CategoryFormWithHeader = ({
  tasks,
  onAddCategory,
  onDone,
  placeholder,
}) => {
  return (
    <Box>
      <Typography variant="h5" gutterBottom sx={{ mb: 3 }}>
        Prospecting Activity Criteria
      </Typography>
      <CategoryForm
        tasks={tasks}
        onAddCategory={onAddCategory}
        onDone={onDone}
        placeholder={placeholder}
      />
    </Box>
  );
};

const Onboard = () => {
  const navigate = useNavigate();
  const [step, setStep] = useState(1); // Start from step 1
  const [categories, setCategories] = useState(new Map());
  const [filters, setFilters] = useState([]);
  const [taskFilterFields, setTaskFilterFields] = useState();
  const [eventFilterFields, setEventFilterFields] = useState();
  const [meetingObject, setMeetingObject] = useState("Task");
  const [gatheringResponses, setGatheringResponses] = useState({});
  const [categoryFormKey, setCategoryFormKey] = useState(0);
  const placeholderIndexRef = useRef(0);

  const [tasks, setTasks] = useState(MOCK_TASK_DATA);

  /**
   * Formats the settings data from the form responses.
   * @returns {Settings} The formatted settings data.
   */
  const formatSettingsData = () => {
    return {
      inactivityThreshold: parseInt(
        gatheringResponses["inactivityThreshold"].value,
        10
      ), // Tracking Period
      cooloffPeriod: parseInt(gatheringResponses["cooloffPeriod"].value, 10), // Cooloff Period
      criteria: filters,
      meetingObject: gatheringResponses["meetingObject"].value,
      meetingsCriteria: gatheringResponses["meetingsCriteria"].value,
      activitiesPerContact: parseInt(
        gatheringResponses["activitiesPerContact"].value,
        10
      ),
      contactsPerAccount: parseInt(
        gatheringResponses["contactsPerAccount"].value,
        10
      ),
      trackingPeriod: parseInt(gatheringResponses["trackingPeriod"].value, 10),
      activateByMeeting: gatheringResponses["activateByMeeting"].value,
      activateByOpportunity: gatheringResponses["activateByOpportunity"].value,
    };
  };

  useEffect(() => {
    const fetchAndSetFilterFields = async () => {
      try {
        const taskFilterFields = await fetchTaskFilterFields();
        const eventFilterFields = await fetchEventFilterFields();

        setTaskFilterFields(taskFilterFields.data.data);
        setEventFilterFields(eventFilterFields.data.data);
      } catch (error) {
        console.error("Error fetching filter fields:", error);
      }
    };

    fetchAndSetFilterFields();
  }, []);

  const handleNext = () => {
    setStep(step + 1);
  };

  const handleInfoGatheringInputChange = (info) => {
    if (
      info.label?.toLowerCase() === "meetings" &&
      info.value?.toLowerCase() === "event"
    ) {
      setMeetingObject("Event");
    } else if (
      info.label?.toLowerCase() === "meetings" &&
      info.value?.toLowerCase() === "task"
    ) {
      setMeetingObject("Task");
    }
  };

  const handleInfoGatheringComplete = (response) => {
    setGatheringResponses((prev) => {
      const newResponses = { ...prev };
      if (Array.isArray(response) && response[0].label === "meetingObject") {
        // Handle the case where we have multiple responses
        response.forEach((res) => {
          newResponses[res.label] = { value: res.value };
        });
      } else {
        // Handle the case where we just have a simple value
        newResponses[response.label] = { value: response.value };
      }
      return newResponses;
    });
    handleNext();
  };

  const renderStep = () => {
    if (step <= ONBOARD_WIZARD_STEPS.length) {
      return (
        <InfoGatheringStep
          key={step}
          stepData={ONBOARD_WIZARD_STEPS[step - 1]}
          onInputChange={handleInfoGatheringInputChange}
          onComplete={handleInfoGatheringComplete}
          stepIndex={step - 1}
          filterFields={
            meetingObject.toLowerCase() === "task"
              ? taskFilterFields
              : eventFilterFields
          }
          FILTER_OPERATOR_MAPPING={FILTER_OPERATOR_MAPPING}
        />
      );
    } else if (step === ONBOARD_WIZARD_STEPS.length + 1) {
      return (
        <CategoryFormWithHeader
          key={categoryFormKey}
          tasks={tasks}
          onAddCategory={addCategory}
          onDone={handleDone}
          placeholder={`Example: ${getPlaceholder()}`}
        />
      );
    } else if (step === ONBOARD_WIZARD_STEPS.length + 2) {
      return (
        <CategoryOverview
          proposedFilterContainers={filters}
          onSave={saveSettings}
          taskFilterFields={taskFilterFields}
        />
      );
    } else {
      return <div>Invalid step</div>;
    }
  };

  const isLargeDialogStep = () => {
    return step > ONBOARD_WIZARD_STEPS.length;
  };

  const handleClose = () => {
    // Function to handle closing the wizard, if needed
  };

  const addCategory = (category, selectedTaskIds) => {
    if (categories.has(category)) {
      alert("Category already exists!");
      return;
    }

    // Add the new category with selected tasks
    const newCategories = new Map(categories);
    const selectedTasks = tasks.filter((task) => selectedTaskIds.has(task.Id));
    newCategories.set(category, selectedTasks);
    setCategories(newCategories);

    // Remove selected tasks from the available tasks list
    const remainingTasks = tasks.filter(
      (task) => !selectedTaskIds.has(task.Id)
    );
    setTasks(remainingTasks);

    // Reset the CategoryForm by updating its key
    setCategoryFormKey((prevKey) => prevKey + 1);
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

  const handleDone = async () => {
    const filterContainersPromises = Array.from(categories.entries()).map(
      async ([category, tasks]) => {
        try {
          const response = await axios.post(
            "http://localhost:8000/generate_filters",
            { tasks },
            {
              validateStatus: () => true,
            }
          );
          return {
            ...(response.data.data === "error" ? {} : response.data.data),
            name: category,
          };
        } catch (error) {
          console.error("Error processing category:", category, error);
          return {
            name: category,
            filters: [{ field: "", operator: "", value: "" }],
          };
        }
      }
    );

    const filterContainers = await Promise.all(filterContainersPromises);
    setFilters(filterContainers);
    handleNext();
  };

  const saveSettings = async () => {
    try {
      const formattedSettings = formatSettingsData();
      await axios.post(
        "http://localhost:8000/save_settings",
        formattedSettings
      );
      navigate("/app/settings");
    } catch (error) {
      console.error("Error saving settings:", error);
    }
  };

  return (
    <Dialog
      open
      onClose={() => {}} // You might want to handle closing differently now
      PaperProps={{
        style: {
          boxShadow: "0 4px 20px rgba(0,0,0,0.1)",
          border: "1px solid #e0e0e0",
          ...(isLargeDialogStep()
            ? {
                maxWidth: "90vw",
                width: "90vw",
                maxHeight: "90vh",
                height: "90vh",
              }
            : {}),
        },
      }}
      fullWidth
      maxWidth={isLargeDialogStep() ? "lg" : "sm"}
    >
      <DialogContent
        style={{
          padding: isLargeDialogStep() ? "24px" : "16px",
        }}
      >
        {renderStep()}
      </DialogContent>
    </Dialog>
  );
};

export default Onboard;
