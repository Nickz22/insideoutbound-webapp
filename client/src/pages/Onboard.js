import React, { useState, useEffect, useRef } from "react";
import { Dialog, DialogContent, Box, Typography, Fade } from "@mui/material";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import AnimatedIconButton from "../components/AnimatedIconButton/AnimatedIconButton";
import CategoryForm from "../components/ProspectingCategoryForm/ProspectingCategoryForm";
import CategoryOverview from "../components/ProspectingCategoryOverview/ProspectingCategoryOverview";
import InfoGatheringStep from "../components/InfoGatheringStep/InfoGatheringStep";

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
  const [step, setStep] = useState(0);
  const [categories, setCategories] = useState(new Map());
  const [filters, setFilters] = useState([]);
  const [taskFilterFields, setTaskFilterFields] = useState();
  const [gatheringSteps, setGatheringSteps] = useState([]);
  const [gatheringResponses, setGatheringResponses] = useState({});
  const [categoryFormKey, setCategoryFormKey] = useState(0);
  const placeholderIndexRef = useRef(0);
  const placeholders = [
    "Outbound Calls",
    "LinkedIn Messages",
    "Inbound Calls",
    "Gifts",
    "Outbound Emails",
    "Inbound Emails",
    "LinkedIn Connections",
    "Meetings",
    "Webinars",
    "Conferences",
  ];
  const [tasks, setTasks] = useState([
    {
      Id: 1,
      Subject: "Call John Doe",
      Who: "John Doe",
      Priority: "High",
      Status: "Not Started",
      Type: "Call",
      TaskSubtype: "Email",
    },
    {
      Id: 2,
      Subject: "Email Jane Doe",
      Who: "Jane Doe",
      Priority: "High",
      Status: "Not Started",
      Type: "Email",
      TaskSubtype: "Email",
    },
    {
      Id: 3,
      Subject: "Call John Smith",
      Who: "John Smith",
      Priority: "Low",
      Status: "Not Started",
      Type: "Call",
      TaskSubtype: "Call",
    },
    {
      Id: 4,
      Subject: "Email Jane Smith",
      Who: "Jane Smith",
      Priority: "High",
      Status: "Not Started",
      Type: "Email",
      TaskSubtype: "Call",
    },
  ]);

  const infoGatheringSteps = [
    {
      title: "Tracking Period",
      description: "How long should an Account be actively pursued?",
      inputType: "number",
      inputLabel: "Number of days",
    },
    {
      title: "Cooloff Period",
      description: "How much time should pass before re-engaging?",
      inputType: "number",
      inputLabel: "Number of days",
    },
    {
      title: "Contacts per Account",
      description:
        "How many Contacts under a single Account need to be prospected before the Account is considered to be engaged?",
      inputType: "number",
      inputLabel: "Number of Contacts",
    },
    {
      title: "Acivities per Contact",
      description:
        "How many prospecting activities are needed under a single Contact before it can be considered prospected?",
      inputType: "number",
      inputLabel: "Number of Activities",
    },
    {
      title: "Automatically Engage via Meetings",
      description:
        "Should an Account be immediately considered as engaged when a meeting is booked with one of its Contacts?",
      inputType: "boolean",
      inputLabel: "Automatically Engage via Meetings",
    },
    {
      title: "Automatically Engage via Opportunities",
      description:
        "Should an Account be immediately considered as engaged when an Opportunity is created?",
      inputType: "boolean",
      inputLabel: "Automatically Engage via Opportunities",
    },
  ];

  useEffect(() => {
    const fetchAndSetTaskFilterFields = async () => {
      const taskFilterFields = await axios.get(
        "http://localhost:8000/get_task_criteria_fields",
        {
          validateStatus: () => true,
        }
      );
      setTaskFilterFields(taskFilterFields.data);
    };
    fetchAndSetTaskFilterFields();
  }, []);

  const handleReturnToLogin = () => {
    navigate("/"); // Navigate to the login route
  };

  const handleInfoGatheringComplete = (response) => {
    setGatheringResponses((prev) => ({
      ...prev,
      [step - 1]: response,
    }));
    handleNext();
  };

  const handleNext = () => {
    if (step === 0) {
      setGatheringSteps(infoGatheringSteps);
    }
    setStep(step + 1);
  };

  const renderStep = () => {
    if (step === 0) {
      return (
        <Box
          display="flex"
          alignItems="center"
          justifyContent="center"
          minHeight="5rem"
          width="30rem"
        >
          <Typography
            variant="h6"
            style={{
              fontWeight: "lighter",
              paddingRight: "5rem",
              paddingLeft: "1rem",
              marginBottom: ".5rem",
            }}
          >
            Help us understand how you sell so we can correctly populate your
            prospecting activity dashboard.
          </Typography>
          <AnimatedIconButton onClick={handleNext} />
        </Box>
      );
    } else if (step <= infoGatheringSteps.length) {
      return (
        <InfoGatheringStep
          key={step} // Add this line to ensure a new instance is created for each step
          stepData={infoGatheringSteps[step - 1]}
          onComplete={handleInfoGatheringComplete}
          stepIndex={step - 1} // Pass the current step index
        />
      );
    } else if (step === infoGatheringSteps.length + 1) {
      return (
        <CategoryFormWithHeader
          key={categoryFormKey}
          tasks={tasks}
          onAddCategory={addCategory}
          onDone={handleDone}
          placeholder={`Example: ${getPlaceholder()}`}
        />
      );
    } else if (step === infoGatheringSteps.length + 2) {
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
    const placeholder = placeholders[placeholderIndexRef.current];
    placeholderIndexRef.current =
      (placeholderIndexRef.current + 1) % placeholders.length;
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
      await axios.post("http://localhost:8000/save_settings_criteria", {
        filters,
      });
      navigate("/app");
    } catch (error) {
      console.error("Error saving settings:", error);
    }
  };

  return (
    <Dialog
      open
      onClose={handleClose}
      style={{ backgroundColor: "cyan" }}
      PaperProps={{
        style: {
          boxShadow: "0 4px 20px rgba(0,0,0,0.1)",
          border: "1px solid #e0e0e0",
        },
      }}
      TransitionComponent={Fade}
    >
      {step === 0 && (
        <Typography
          variant="caption"
          onClick={handleReturnToLogin}
          style={{
            position: "absolute",
            left: 5,
            bottom: 5,
            color: "#aaa",
            cursor: "pointer",
            textDecoration: "underline",
          }}
        >
          Return to login
        </Typography>
      )}
      <DialogContent>{renderStep()}</DialogContent>
    </Dialog>
  );
};

export default Onboard;
