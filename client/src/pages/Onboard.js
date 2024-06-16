/**
 * // fetch("http://localhost:8000/fetch_tasks_for_wizard")
    //   .then((response) => response.json())
    //   .then((data) => setTasks(data.tasks))
    //   .catch((error) => console.error("Error fetching tasks:", error));
 * 
 * [
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
  ]
 */

import React, { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  Box,
  IconButton,
  Typography,
  Fade,
} from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import { useNavigate } from "react-router-dom";
import AnimatedIconButton from "../components/AnimatedIconButton/AnimatedIconButton";
import CategoryForm from "../components/ProspectingCategoryForm/ProspectingCategoryForm";
import CategoryOverview from "../components/ProspectingCategoryOverview/ProspectingCategoryOverview";

const Onboard = () => {
  const navigate = useNavigate();
  const [step, setStep] = useState(0); // Initialize step to 0 for the introduction step
  const [categories, setCategories] = useState(new Map());
  const [tasks, setTasks] = useState([]);

  useEffect(() => {
    // Add event listener for 'Enter' keydown
    window.addEventListener("keydown", handleKeyPress);

    // Clean up the event listener
    return () => {
      window.removeEventListener("keydown", handleKeyPress);
    };
  }, []);

  const handleReturnToLogin = () => {
    navigate("/"); // Navigate to the login route
  };

  const handleClose = () => {
    // Function to handle closing the wizard, if needed
  };

  const handleNext = () => {
    setStep(step + 1);
  };

  const handleKeyPress = (event) => {
    if (event.key === "Enter") {
      handleNext();
    }
  };

  const addCategory = (category, tasks) => {
    if (categories.has(category)) {
      alert("Category already exists!");
      return;
    }
    setCategories(new Map(categories.set(category, tasks)));
    handleNext();
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
              style={{ fontWeight: "lighter", paddingRight: "5rem", marginBottom: ".5rem" }}
            >
              Help us categorize the different types of prospecting activities
              in your organization
            </Typography>
            <AnimatedIconButton onClick={handleNext} />
          </Box>
        );
      case 1:
        return <CategoryForm onAddCategory={addCategory} tasks={tasks} />;
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
      <DialogContent>{renderStep()}</DialogContent>
    </Dialog>
  );
};

export default Onboard;
