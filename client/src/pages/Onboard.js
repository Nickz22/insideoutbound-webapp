import React, { useState, useEffect } from "react";
import { Dialog, DialogContent, Box, Typography, Fade } from "@mui/material";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import AnimatedIconButton from "../components/AnimatedIconButton/AnimatedIconButton";
import CategoryForm from "../components/ProspectingCategoryForm/ProspectingCategoryForm";
import CategoryOverview from "../components/ProspectingCategoryOverview/ProspectingCategoryOverview";

/**
 * @param field - Salesforce SObject field to filter on
 * @param operator - String ("contains" | "equals" | "not equals")
 *                   Number ("less than" | "less than or equal to" | "greater than" | "greater than or equal to")
 *                   Date ("equals" | "not equals" | "before" | "on or before" | "on or after" | "last n days" | "next n days" | "this month" | "last month" | "next month" | "this year" | "last year" | "next year")
 * @param value - Value to filter on
 * @param dataType - String ("string" | "number" | "date")
 */
class Filter {
  constructor(field, operator, value, dataType) {
    this.field = field;
    this.operator = operator;
    this.value = value;
    this.dataType = dataType;
  }
}
/**
 * @param name - Name of the filter container
 * @param filters - Array of Filter instances
 * @param filterLogic - String (i.e. 1 AND (2 OR 3) AND 4)
 */
class FilterContainer {
  constructor(name, filters, filterLogic) {
    this.name = name;
    this.filters = filters; // This should be an array of Filter instances
    this.filterLogic = filterLogic;
  }
}

const Onboard = () => {
  const navigate = useNavigate();
  const [step, setStep] = useState(0); // Initialize step to 0 for the introduction step
  const [categories, setCategories] = useState(new Map());
  const [tasks, setTasks] = useState([
    {
      id: 1,
      subject: "Call John Doe",
      who: "John Doe",
      priority: "High",
      status: "Not Started",
      type: "Call",
      task_subtype: "Outbound",
    },
    {
      id: 2,
      subject: "Email Jane Doe",
      who: "Jane Doe",
      priority: "Medium",
      status: "Not Started",
      type: "Email",
      task_subtype: "Outbound",
    },
    {
      id: 3,
      subject: "Call John Smith",
      who: "John Smith",
      priority: "Low",
      status: "Not Started",
      type: "Call",
      task_subtype: "Inbound",
    },
    {
      id: 4,
      subject: "Email Jane Smith",
      who: "Jane Smith",
      priority: "High",
      status: "Not Started",
      type: "Email",
      task_subtype: "Inbound",
    },
  ]);

  useEffect(() => {}, []);

  const handleReturnToLogin = () => {
    navigate("/"); // Navigate to the login route
  };

  const handleClose = () => {
    // Function to handle closing the wizard, if needed
  };

  const handleNext = () => {
    setStep(step + 1);
  };

  const addCategory = (category, selectedTaskIds) => {
    if (categories.has(category)) {
      alert("Category already exists!");
      return;
    }

    // Add the new category with selected tasks
    const newCategories = new Map(categories);
    const selectedTasks = tasks.filter((task) => selectedTaskIds.has(task.id));
    newCategories.set(category, selectedTasks);
    setCategories(newCategories);

    // Remove selected tasks from the available tasks list
    const remainingTasks = tasks.filter(
      (task) => !selectedTaskIds.has(task.id)
    );
    setTasks(remainingTasks);
  };

  const handleDone = () => {
    // hit http://localhost:8000/generate_filters
    const filterContainers = [];
    categories.forEach((tasks, category) => {
      axios
        .post("http://localhost:8000/generate_filters", {
          tasks,
        })
        .then((response) => {
          const filter = { ...response.data, name: category };
          filterContainers.push(filter);
        });
    });

    handleNext(); // Move to the overview step
  };

  const renderStep = () => {
    switch (step) {
      case 0:
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
              Help us categorize the different types of prospecting activities
              in your organization
            </Typography>
            <AnimatedIconButton onClick={handleNext} />
          </Box>
        );
      case 1:
        return (
          <CategoryForm
            onAddCategory={addCategory}
            onDone={handleDone}
            tasks={tasks}
          />
        );
      case 2:
        return <CategoryOverview categories={categories} />;
      default:
        return <div>Invalid step</div>;
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
            color: "#aaa", // Light gray color for the text
            cursor: "pointer", // Change cursor to indicate clickable
            textDecoration: "underline", // Underline to suggest it's a link
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
