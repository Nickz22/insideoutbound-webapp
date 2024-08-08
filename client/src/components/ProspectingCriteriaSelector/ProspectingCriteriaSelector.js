import React, { useState, useEffect } from "react";
import {
  Typography,
  Button,
  Box,
  CircularProgress,
  Switch,
  FormControlLabel,
  Stepper,
  Step,
  StepLabel,
  Paper,
} from "@mui/material";
import FilterContainer from "../FilterContainer/FilterContainer";
import CustomTable from "../CustomTable/CustomTable";
import { FILTER_OPERATOR_MAPPING } from "src/utils/c";

/**
 * @typedef {import('types').FilterContainer} FilterContainer
 * @typedef {import('types').CriteriaField} CriteriaField
 * @typedef {import('types').TableData} TableData
 */

/**
 * @param {{initialFilterContainers: FilterContainer[], taskFilterFields: CriteriaField[], tableData: TableData, onFilterChange: function, onTaskSelection: function, onSave: function}} props
 */
const ProspectingCriteriaSelector = ({
  initialFilterContainers,
  taskFilterFields,
  tableData,
  onFilterChange,
  onTaskSelection,
  onSave,
}) => {
  const [filterContainers, setFilterContainers] = useState(
    initialFilterContainers
  );
  const [isGeneratingCriteria, setIsGeneratingCriteria] = useState(false);
  const [currentFilter, setCurrentFilter] = useState(null);
  const [showTaskTable, setShowTaskTable] = useState(false);
  const [selectedTaskIds, setSelectedTaskIds] = useState(new Set());
  const [activeStep, setActiveStep] = useState(0);

  useEffect(() => {
    if (initialFilterContainers.length !== filterContainers.length) {
      setFilterContainers(initialFilterContainers);
    }
    setCurrentFilter(initialFilterContainers[activeStep]);
  }, [initialFilterContainers, activeStep]);

  const handleFilterChange = (updatedFilter) => {
    setCurrentFilter(updatedFilter);
    const newFilters = filterContainers.map((filter) =>
      filter.name === updatedFilter.name ? updatedFilter : filter
    );
    setFilterContainers(newFilters);
    onFilterChange(updatedFilter);
  };

  const handleTaskSelectionChange = (newSelectedIds) => {
    setSelectedTaskIds(newSelectedIds);
  };

  const handleGenerateCriteria = async () => {
    setIsGeneratingCriteria(true);
    try {
      const generatedCriteria = await onTaskSelection(
        Array.from(selectedTaskIds)
      );
      if (generatedCriteria) {
        setShowTaskTable(false);
        generatedCriteria.name = currentFilter.name;
        handleFilterChange(generatedCriteria);
      }
    } finally {
      setIsGeneratingCriteria(false);
    }
  };

  const handleNext = () => {
    setActiveStep((prevActiveStep) => prevActiveStep + 1);
    setCurrentFilter(null); // Clear the current filter
    setSelectedTaskIds(new Set()); // Clear selected tasks
    setShowTaskTable(false); // Hide the task table
  };

  const handleBack = () => {
    setActiveStep((prevActiveStep) => prevActiveStep - 1);
  };

  const isStepComplete = (step) => {
    const filter = filterContainers[step];
    return filter && filter.filters.length > 0 && filter.filterLogic;
  };

  const allStepsCompleted = filterContainers.every((_, index) =>
    isStepComplete(index)
  );

  const showProgressBar = filterContainers.length > 1;

  return (
    <Box sx={{ p: 4, pb: 10 }}>
      <Typography variant="h4" fontWeight="lighter" gutterBottom>
        Prospecting Activity Criteria
      </Typography>

      {showProgressBar && (
        <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
          {filterContainers.map((filter, index) => (
            <Step key={filter.name} completed={isStepComplete(index)}>
              <StepLabel>{filter.name}</StepLabel>
            </Step>
          ))}
        </Stepper>
      )}

      <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
        <Typography variant="h6" gutterBottom>
          {filterContainers[activeStep]?.name} Criteria
        </Typography>

        <FormControlLabel
          control={
            <Switch
              checked={showTaskTable}
              onChange={(e) => setShowTaskTable(e.target.checked)}
            />
          }
          label="Show Task Table to Generate Criteria"
        />

        {showTaskTable && (
          <Box sx={{ my: 2 }}>
            <CustomTable
              tableData={{ ...tableData, selectedIds: selectedTaskIds }}
              onSelectionChange={handleTaskSelectionChange}
              paginate={true}
            />
            <Button
              variant="contained"
              color="primary"
              onClick={handleGenerateCriteria}
              disabled={isGeneratingCriteria}
              sx={{ mt: 2 }}
            >
              {isGeneratingCriteria ? (
                <CircularProgress size={24} color="inherit" />
              ) : (
                "Generate Criteria from Tasks"
              )}
            </Button>
          </Box>
        )}

        {currentFilter && (
          <FilterContainer
            initialFilterContainer={currentFilter}
            filterFields={taskFilterFields}
            filterOperatorMapping={FILTER_OPERATOR_MAPPING}
            hasNameField={true}
            isNameReadOnly={true}
            hasDirectionField={false}
            onLogicChange={handleFilterChange}
            onValueChange={handleFilterChange}
          />
        )}
      </Paper>

      {showProgressBar && (
        <Box sx={{ display: "flex", justifyContent: "space-between", mt: 2 }}>
          <Button onClick={handleBack} disabled={activeStep === 0}>
            Back
          </Button>
          {activeStep === filterContainers.length - 1 ? (
            <Button
              variant="contained"
              color="success"
              onClick={() => onSave(filterContainers)}
              disabled={!allStepsCompleted}
            >
              Finish
            </Button>
          ) : (
            <Button
              variant="contained"
              color="primary"
              onClick={handleNext}
              disabled={!isStepComplete(activeStep)}
            >
              Next
            </Button>
          )}
        </Box>
      )}
    </Box>
  );
};

export default ProspectingCriteriaSelector;
