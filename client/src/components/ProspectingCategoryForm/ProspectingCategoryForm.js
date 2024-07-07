import React, { useState, useEffect } from "react";
import { TextField, Button, Typography, Box } from "@mui/material";
import CustomTable from "../CustomTable/CustomTable"; // Adjust the path as necessary

/**
 * @typedef {import('types').Task} Task
 * @typedef {import('types').TableData} TableData
 */

/**
 * @param {{ tasks: Task[], onAddCategory: Function, onDone: React.MouseEventHandler, placeholder: string }} props
 */
const ProspectingCategoryForm = ({
  tasks,
  onAddCategory,
  onDone,
  placeholder,
}) => {
  /** @type {[TableData | null, Function]} */
  const [tableData, setTableData] = useState(
    /** @type {TableData | null} */ (null)
  );
  const [categoryName, setCategoryName] = useState("");
  const [selectedTaskIds, setSelectedTaskIds] = useState(new Set());

  useEffect(() => {
    availableColumns: [];
    setTableData({
      columns: [
        { id: "select", label: "Select", dataType: "select" },
        { id: "subject", label: "Subject", dataType: "string" },
        { id: "priority", label: "Priority", dataType: "string" },
        { id: "status", label: "Status", dataType: "string" },
        { id: "type", label: "Type", dataType: "string" },
        { id: "taskSubtype", label: "Task Subtype", dataType: "string" },
      ],
      data: tasks,
      selectedIds: new Set(),
    });
  }, []);

  /**
   * @param {Set<string>} newSelectedIds
   */
  const handleTableSelectionChange = (newSelectedIds) => {
    setTableData(
      /** @param {TableData} prev */
      (prev) => (prev ? { ...prev, selectedIds: newSelectedIds } : null)
    );
    setSelectedTaskIds(newSelectedIds);
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
    tableData && (
      <Box sx={{ p: 1 }}>
        <Typography gutterBottom>
          Create a prospecting category and select example tasks. We will use
          these to set up automatic detection for similar activities.
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
          tableData={tableData}
          onSelectionChange={handleTableSelectionChange}
          onColumnsChange={() => console.log("")}
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
    )
  );
};

export default ProspectingCategoryForm;
