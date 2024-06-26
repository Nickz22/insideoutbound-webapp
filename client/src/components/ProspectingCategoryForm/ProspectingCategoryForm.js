import React, { useState } from "react";
import { TextField, Button, Typography, Box } from "@mui/material";
import CustomTable from "../CustomTable/CustomTable"; // Adjust the path as necessary

const ProspectingCategoryForm = ({
  tasks,
  onAddCategory,
  onDone,
  placeholder,
}) => {
  const [categoryName, setCategoryName] = useState("");
  const [selectedTaskIds, setSelectedTaskIds] = useState(new Set());

  const handleTaskToggle = (task) => {
    const newSelectedTaskIds = new Set(selectedTaskIds);
    if (newSelectedTaskIds.has(task.Id)) {
      newSelectedTaskIds.delete(task.Id);
    } else {
      newSelectedTaskIds.add(task.Id);
    }
    setSelectedTaskIds(newSelectedTaskIds);
  };

  const handleCreateCategory = () => {
    if (categoryName.trim() === "") {
      alert("Please enter a category name.");
      return;
    }
    if (selectedTaskIds.size === 0) {
      alert("Please select at least one task.");
      return;
    }
    onAddCategory(categoryName, selectedTaskIds);
    setCategoryName("");
    setSelectedTaskIds(new Set());
  };

  return (
    <Box sx={{ p: 1 }}>
      <Typography gutterBottom>
        Create a prospecting category and select example tasks. We'll use these
        to set up automatic detection for similar activities.
      </Typography>
      <TextField
        label="Category Name"
        value={categoryName}
        onChange={(e) => setCategoryName(e.target.value)}
        placeholder={placeholder}
        fullWidth
        margin="normal"
      />
      <CustomTable
        columns={[
          { id: "Subject", label: "Subject" },
          { id: "Who", label: "Who" },
          { id: "Priority", label: "Priority" },
          { id: "Status", label: "Status" },
          { id: "Type", label: "Type" },
          { id: "TaskSubtype", label: "Task Subtype" },
          { id: "select", label: "Select", selectedIds: selectedTaskIds },
        ]}
        data={tasks}
        onToggle={handleTaskToggle}
      />
      <Box sx={{ mt: 2, display: "flex", justifyContent: "flex-start" }}>
        <Button
          onClick={handleCreateCategory}
          variant="contained"
          color="primary"
          sx={{ mr: 2 }}
        >
          Create New
        </Button>
        <Button onClick={onDone} variant="outlined" color="primary">
          Done
        </Button>
      </Box>
    </Box>
  );
};

export default ProspectingCategoryForm;
