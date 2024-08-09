import React, { useState, useEffect, useCallback } from "react";
import { debounce } from "lodash";
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
 * @param {{title?: string, initialFilterContainers: FilterContainer[], filterFields: CriteriaField[], tableData: TableData, onFilterChange: function, onTaskSelection: function, onSave?: function}} props
 */
const ProspectingCriteriaSelector = ({
  title,
  initialFilterContainers,
  filterFields,
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
  const [showTable, setShowTable] = useState(false);
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [activeStep, setActiveStep] = useState(0);

  useEffect(() => {
    if (initialFilterContainers.length !== filterContainers.length) {
      setFilterContainers(initialFilterContainers);
    }
    setCurrentFilter(initialFilterContainers[activeStep]);
  }, [initialFilterContainers, activeStep]);

  const debouncedOnFilterChange = useCallback(
    debounce((updatedFilter, onFilterChange) => {
      onFilterChange(updatedFilter);
    }, 1000),
    []
  );

  const debouncedSetCurrentFilter = useCallback(
    debounce((updatedFilter) => {
      setCurrentFilter(updatedFilter);
    }, 1000),
    []
  );

  const handleFilterChange = (updatedFilter) => {
    debouncedSetCurrentFilter(updatedFilter);
    const newFilters = filterContainers.map((filter) =>
      filter.name === updatedFilter.name ? updatedFilter : filter
    );
    setFilterContainers(newFilters);

    // Use the debounced function
    debouncedOnFilterChange(updatedFilter, onFilterChange);
  };

  const handleTaskSelectionChange = (newSelectedIds) => {
    setSelectedIds(newSelectedIds);
  };

  const handleGenerateCriteria = async () => {
    setIsGeneratingCriteria(true);
    try {
      const generatedCriteria = await onTaskSelection(Array.from(selectedIds));
      if (generatedCriteria) {
        setShowTable(false);
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
    setSelectedIds(new Set()); // Clear selected tasks
    setShowTable(false); // Hide the task table
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
      {title && (
        <Typography variant="h4" fontWeight="lighter" gutterBottom>
          {title}
        </Typography>
      )}

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
              checked={showTable}
              onChange={(e) => setShowTable(e.target.checked)}
            />
          }
          label="Show Table to Generate Criteria"
        />

        {showTable && (
          <Box sx={{ my: 2 }}>
            <CustomTable
              tableData={{ ...tableData, selectedIds: selectedIds }}
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
            filterFields={filterFields}
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
