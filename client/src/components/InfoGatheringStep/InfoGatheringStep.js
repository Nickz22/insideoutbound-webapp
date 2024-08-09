import React, { useState, useEffect, useRef } from "react";
import {
  Box,
  CircularProgress,
  Typography,
  TextField,
  Select,
  MenuItem,
  Button,
  FormControl,
  InputLabel,
  Paper,
  Grid,
  Tooltip,
} from "@mui/material";
import { generateCriteria } from "../Api/Api";
import parse from "html-react-parser";
import ProspectingCriteriaSelector from "../ProspectingCriteriaSelector/ProspectingCriteriaSelector";

/**
 * @typedef {import('types').OnboardWizardStepInput} OnboardWizardStepInput
 */

const InfoGatheringStep = ({
  stepData,
  onComplete,
  onTableDisplay,
  settings,
}) => {
  const [inputValues, setInputValues] = useState({});
  const [tableData, setTableData] = useState(null);
  const [filterFields, setFilterFields] = useState(null);
  const [loadingStates, setLoadingStates] = useState({});
  const settingsRef = useRef(settings);
  const [renderedDescription, setRenderedDescription] = useState("");
  const [prospectingFilters, setProspectingFilters] = useState({});

  useEffect(() => {
    settingsRef.current = settings;
  }, [settings]);

  useEffect(() => {
    if (stepData.descriptionRenderer) {
      const newDescription = stepData.descriptionRenderer(
        stepData.description,
        inputValues
      );
      setRenderedDescription(newDescription);
    } else {
      setRenderedDescription(stepData.description);
    }
  }, [stepData, inputValues]);

  const setLoadingState = (inputSetting, isLoading) => {
    setLoadingStates((prev) => ({ ...prev, [inputSetting]: isLoading }));
  };

  useEffect(() => {
    const fetchData = async () => {
      const criteriaInput = stepData.inputs.find(
        /** @param {OnboardWizardStepInput} input */
        (input) => input.inputType === "prospectingCriteria"
      );
      if (criteriaInput && criteriaInput.renderEval(inputValues)) {
        setLoadingState(criteriaInput.setting, true);
        try {
          const data = await criteriaInput.dataFetcher({
            ...settingsRef.current,
            ...inputValues,
          });
          setTableData({ ...data.data });
          onTableDisplay(true);

          const fields = await criteriaInput.fetchFilterFields({
            ...settingsRef.current,
            ...inputValues,
          });
          setFilterFields(fields);
        } catch (error) {
          console.error("Error fetching data:", error);
        } finally {
          setLoadingState(criteriaInput.setting, false);
        }
      }
    };

    fetchData();
  }, [stepData, inputValues, settingsRef]);

  const handleInputChange = (event, setting) => {
    setInputValues((prev) => ({
      ...prev,
      [setting]: event.target.value,
    }));
  };

  const handleSubmit = () => {
    const completedInputs = Object.entries(inputValues).map(
      ([setting, value]) => ({
        label: setting,
        value,
      })
    );
    completedInputs.push(
      ...Object.entries(prospectingFilters).map(([setting, value]) => ({
        label: setting,
        value,
      }))
    );
    onComplete(completedInputs);
  };

  const handleProspectingFilterChange = (updatedFilter, setting) => {
    setProspectingFilters((prev) => ({
      ...prev,
      [setting]: updatedFilter,
    }));
  };

  const handleTaskSelection = async (selectedTaskIds) => {
    if (tableData) {
      const selectedTasks = tableData.data.filter((task) =>
        selectedTaskIds.includes(task.id)
      );
      const response = await generateCriteria(selectedTasks, tableData.columns);
      return response.data[0];
    }
    return null;
  };

  const renderInput = (input) => {
    const isLoading = loadingStates[input.setting];

    switch (input.inputType) {
      case "text":
      case "number":
      case "picklist":
        const inputComponent = (
          <>
            {isLoading && <CircularProgress size={20} />}
            {input.inputType === "picklist" ? (
              <FormControl fullWidth variant="outlined" margin="normal">
                <InputLabel>{input.inputLabel}</InputLabel>
                <Select
                  value={
                    inputValues[input.setting] || settings[input.setting] || ""
                  }
                  onChange={(e) => handleInputChange(e, input.setting)}
                  label={input.inputLabel}
                >
                  <MenuItem value="">
                    <em>Select an option</em>
                  </MenuItem>
                  {input.options?.map((option, index) => (
                    <MenuItem key={index} value={option}>
                      {option}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            ) : (
              <TextField
                fullWidth
                type={input.inputType}
                value={
                  inputValues[input.setting] || settings[input.setting] || ""
                }
                onChange={(e) => handleInputChange(e, input.setting)}
                label={input.inputLabel}
                variant="outlined"
                margin="normal"
              />
            )}
          </>
        );

        return input.tooltip ? (
          <Tooltip title={input.tooltip} arrow>
            <div>{inputComponent}</div>
          </Tooltip>
        ) : (
          inputComponent
        );
      case "prospectingCriteria":
        return (
          <Box sx={{ mt: 2, mb: 2 }}>
            {isLoading ? (
              <CircularProgress />
            ) : (
              tableData &&
              filterFields && (
                <>
                  <Typography variant="body1">{input.inputLabel}</Typography>
                  <ProspectingCriteriaSelector
                    initialFilterContainers={[
                      prospectingFilters[input.setting] || {
                        name: input.setting,
                        filters: [],
                        filterLogic: "",
                      },
                    ]}
                    filterFields={filterFields}
                    tableData={tableData}
                    onFilterChange={(updatedFilter) =>
                      handleProspectingFilterChange(
                        updatedFilter,
                        input.setting
                      )
                    }
                    onTaskSelection={handleTaskSelection}
                  />
                </>
              )
            )}
          </Box>
        );
      default:
        return null;
    }
  };

  const shouldRenderInput = (input, index) => {
    if (!input.renderEval) return true;
    if (index === 0) return true;
    return input.renderEval(inputValues);
  };

  return (
    stepData && (
      <Paper elevation={3} sx={{ mx: "auto", p: 4 }}>
        <Typography variant="h4" component="h2" gutterBottom>
          {stepData.title}
        </Typography>
        <Typography variant="body1" paragraph>
          {parse(renderedDescription)}
        </Typography>
        <Grid container spacing={2}>
          {stepData.inputs.map(
            (input, index) =>
              shouldRenderInput(input, index) && (
                <Grid item xs={12} key={index}>
                  {renderInput(input)}
                </Grid>
              )
          )}
        </Grid>
        <Box mt={2}>
          <Button
            variant="contained"
            color="primary"
            onClick={handleSubmit}
            size="large"
            fullWidth
          >
            Next
          </Button>
        </Box>
      </Paper>
    )
  );
};

export default InfoGatheringStep;
