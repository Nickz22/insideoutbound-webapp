import React, { useState } from "react";
import { TextField, Button } from "@mui/material";
import CustomTable from "../CustomTable/CustomTable"; // Adjust the path as necessary

const ProspectingCategoryForm = ({ tasks, onAddCategory, onDone }) => {
  const [categoryName, setCategoryName] = useState("");
  const [selectedTaskIds, setSelectedTaskIds] = useState(new Set());

  const handleTaskToggle = (task) => {
    const newSelectedTaskIds = new Set(selectedTaskIds);
    if (newSelectedTaskIds.has(task.id)) {
      newSelectedTaskIds.delete(task.id);
    } else {
      newSelectedTaskIds.add(task.id);
    }
    setSelectedTaskIds(newSelectedTaskIds);
  };

  const handleCreateCategory = () => {
    if (categoryName.trim() === "") {
      alert("Please enter a category name.");
      return;
    }
    onAddCategory(categoryName, selectedTaskIds);
    setCategoryName("");
    setSelectedTaskIds(new Set());
  };

  return (
    <div>
      <TextField
        label="Category"
        value={categoryName}
        onChange={(e) => setCategoryName(e.target.value)}
        placeholder="Outbound Calls"
        fullWidth
        margin="normal"
      />
      <CustomTable
        columns={[
          { id: "subject", label: "Subject" },
          { id: "who", label: "Who" },
          { id: "priority", label: "Priority" },
          { id: "status", label: "Status" },
          { id: "type", label: "Type" },
          { id: "taskSubtype", label: "Task Subtype" },
          { id: "select", label: "", selectedIds: selectedTaskIds },
        ]}
        data={tasks}
        onToggle={handleTaskToggle}
      />
      <Button
        onClick={handleCreateCategory}
        variant="contained"
        color="primary"
        style={{ marginTop: 20 }}
      >
        Create New
      </Button>
      <Button
        onClick={onDone}
        variant="outlined"
        color="primary"
        style={{ marginTop: 20, marginLeft: 20 }}
      >
        Done
      </Button>
    </div>
  );
};

export default ProspectingCategoryForm;
