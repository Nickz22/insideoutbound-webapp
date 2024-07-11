import React, { useState, useEffect } from "react";
import { TextField, Button, Typography, Box } from "@mui/material";
import CustomTable from "../CustomTable/CustomTable"; // Adjust the path as necessary

/**
 * @typedef {import('types').Task} Task
 * @typedef {import('types').TableData} TableData
 * @typedef {import('types').SObjectField} SObjectField
 */

/**
 * @param {{ initialTableData: TableData, setSelectedColumns: Function,  onAddCategory: Function, onDone: React.MouseEventHandler, placeholder: string }} props
 */
const ProspectingCategoryForm = ({
  initialTableData,
  setSelectedColumns,
  onAddCategory,
  onDone,
  placeholder,
}) => {
  const [categoryName, setCategoryName] = useState("");
  const [selectedTaskIds, setSelectedTaskIds] = useState(new Set());
  const [tableData, setTableData] = useState({ initialTableData });

  useEffect(() => {
    setTableData(initialTableData);
  }, [initialTableData]);

  /**
   * @param {Set<string>} newSelectedIds
   */
  const handleTableSelectionChange = (newSelectedIds) => {
    setTableData(
      /** @param {TableData} prev */
      (prev) => ({ ...prev, selectedIds: newSelectedIds })
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
    tableData.data && (
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
          onColumnsChange={setSelectedColumns}
          paginate={true}
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
