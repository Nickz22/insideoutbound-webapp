import React, { useState, useEffect } from "react";
import {
  Button,
  Typography,
  Box,
  Stepper,
  Step,
  StepLabel,
} from "@mui/material";
import CustomTable from "../CustomTable/CustomTable";

const CATEGORIES = [
  "Inbound Call",
  "Outbound Call",
  "Inbound Email",
  "Outbound Email",
];

const ProspectingCategoryForm = ({
  initialTableData,
  setSelectedColumns,
  onAddCategory,
  onDone,
}) => {
  const [activeStep, setActiveStep] = useState(0);
  const [selectedTaskIds, setSelectedTaskIds] = useState(new Set());
  const [tableData, setTableData] = useState(initialTableData);
  const [completedCategories, setCompletedCategories] = useState(0);

  useEffect(() => {
    setTableData(initialTableData);
  }, [initialTableData]);

  const handleTableSelectionChange = (newSelectedIds) => {
    setSelectedTaskIds(newSelectedIds);
    setTableData((prev) => ({ ...prev, selectedIds: newSelectedIds }));
  };

  const handleNext = async () => {
    if (selectedTaskIds.size === 0) {
      alert("Please select at least one task.");
      return;
    }

    // Always add the category and wait for it to complete
    await onAddCategory(CATEGORIES[activeStep], selectedTaskIds);

    if (activeStep < CATEGORIES.length - 1) {
      setActiveStep((prev) => prev + 1);
      setCompletedCategories((prev) => prev + 1);
      setSelectedTaskIds(new Set());
      // The table data will be updated in the useEffect hook
    } else {
      // This is the last category
      setCompletedCategories((prev) => prev + 1);
      onDone();
    }
  };

  return (
    <Box sx={{ p: 1 }}>
      <Stepper activeStep={activeStep}>
        {CATEGORIES.map((label, index) => (
          <Step key={label} completed={index < completedCategories}>
            <StepLabel>{label}</StepLabel>
          </Step>
        ))}
      </Stepper>

      <Typography gutterBottom sx={{ mt: 2 }}>
        Select tasks that we should recognize as {CATEGORIES[activeStep]}. We
        will use these to set up automatic detection for similar activities.
      </Typography>

      <CustomTable
        tableData={{ ...tableData, selectedIds: selectedTaskIds }}
        onSelectionChange={handleTableSelectionChange}
        onColumnsChange={setSelectedColumns}
        paginate={true}
      />

      <Box sx={{ mt: 2, display: "flex", justifyContent: "flex-start" }}>
        <Button onClick={handleNext} variant="contained" color="primary">
          {activeStep < CATEGORIES.length - 1 ? "Next" : "Done"}
        </Button>
      </Box>
    </Box>
  );
};

export default ProspectingCategoryForm;
