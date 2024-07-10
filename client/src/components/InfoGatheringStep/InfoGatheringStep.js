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
} from "@mui/material";
import parse from "html-react-parser";
import CustomTable from "./../CustomTable/CustomTable";
import FilterContainer from "../FilterContainer/FilterContainer";
import { useNavigate } from "react-router-dom";

/**
 * @typedef {import('@mui/material/Select').SelectChangeEvent<string>} SelectChangeEvent
 * @typedef {import('types').OnboardWizardStep} OnboardWizardStep
 * @typedef {import('types').OnboardWizardStepInput} OnboardWizardStepInput
 * @typedef {import('types').TableColumn} TableColumn
 * @typedef {import('types').TableData} TableData
 * @typedef {import('types').Settings} Settings
 */

/**
 * @param {{ stepData: OnboardWizardStep, onComplete: Function, onTableDisplay: Function, settings: Settings}} props
 */
const InfoGatheringStep = ({
  stepData,
  onComplete,
  onTableDisplay,
  settings,
}) => {
  const navigate = useNavigate();
  const [inputValues, setInputValues] = useState({});
  const [tableData, setTableData] = useState(null);
  const [criteriaData, setCriteriaData] = useState(null);
  const [loadingStates, setLoadingStates] = useState({});
  const settingsRef = useRef(settings);

  useEffect(() => {
    settingsRef.current = settings;
  }, [settings]);

  /**
   * @param {string} inputSetting
   * @param {boolean} isLoading
   */
  const setLoadingState = (inputSetting, isLoading) => {
    setLoadingStates((prev) => ({ ...prev, [inputSetting]: isLoading }));
  };

  useEffect(() => {
    const criteriaInput = stepData.inputs.find(
      (input) => input.inputType === "criteria"
    );
    const shouldRender =
      !criteriaInput?.renderEval || criteriaInput.renderEval(tableData);
    if (criteriaInput && shouldRender && tableData) {
      fetchCriteriaData(criteriaInput);
    }
  }, [stepData, tableData]);

  /**
   * @param {OnboardWizardStepInput} input
   */
  const fetchCriteriaData = async (input) => {
    if (input.dataFetcher && tableData) {
      setLoadingState(input.setting, true);
      try {
        const data = await input.dataFetcher(tableData);
        if (data.success) {
          setCriteriaData(data.data[0]);
          handleCriteriaChange(data.data[0].filterContainer);
        } else if (data.message?.toLowerCase().includes("session expired")) {
          navigate("/");
        }
      } finally {
        setLoadingState(input.setting, false);
      }
    }
  };

  /**
   * @param {FilterContainer} newFilterContainer
   */
  const handleCriteriaChange = (newFilterContainer) => {
    setInputValues((prev) => ({
      ...prev,
      [stepData.inputs.find((input) => input.inputType === "criteria").setting]:
        newFilterContainer,
    }));
  };

  const prevMeetingObject = useRef();

  useEffect(() => {
    const fetchTableData = async () => {
      const tableInput = stepData.inputs.find(
        (input) =>
          input.inputType === "table" &&
          shouldRenderInput(input, stepData.inputs.indexOf(input))
      );

      if (tableInput && tableInput.dataFetcher) {
        setLoadingState(tableInput.setting, true);
        try {
          const data = await tableInput.dataFetcher({
            ...settingsRef.current,
            ...inputValues,
          });
          if (
            !data.success &&
            data.message?.toLowerCase().includes("session expired")
          ) {
            navigate("/");
          }
          if (data.success && data.data.length > 0) {
            setTableData({
              availableColumns: tableInput.availableColumns,
              columns: tableInput.columns,
              data: data.data,
              selectedIds: new Set(),
            });
            onTableDisplay(true);
          } else if (data.message?.toLowerCase().includes("session expired")) {
            navigate("/");
          }
        } finally {
          setLoadingState(tableInput.setting, false);
        }
      } else {
        setTableData(null);
        onTableDisplay(false);
      }
    };

    if (
      inputValues["meetingObject"] !== prevMeetingObject.current ||
      prevMeetingObject.current === undefined
    ) {
      fetchTableData();
      prevMeetingObject.current = inputValues["meetingObject"];
    }
  }, [stepData, inputValues, settingsRef]);

  const handleInputChange = (event, setting) => {
    setInputValues((prev) => ({
      ...prev,
      [setting]: event.target.value,
    }));
  };

  const handleTableSelectionChange = (newSelectedIds) => {
    setTableData((prev) =>
      prev ? { ...prev, selectedIds: newSelectedIds } : null
    );
  };

  const handleColumnsChange = (newColumns) => {
    setTableData((prev) => (prev ? { ...prev, columns: newColumns } : null));
  };

  const handleSubmit = () => {
    const completedInputs = Object.entries(inputValues).map(
      ([setting, value]) => ({
        label: setting,
        value,
      })
    );

    const tableInput = stepData.inputs.find(
      (input) => input.inputType === "table"
    );
    if (tableInput && tableData && tableData.selectedIds.size > 0) {
      completedInputs.push({
        label: tableInput.setting,
        value: tableData.data.filter((row) =>
          tableData.selectedIds.has(row.id)
        ),
      });
    }

    onComplete(completedInputs);
  };

  /**
   *
   * @param {OnboardWizardStepInput} input
   * @returns
   */
  const renderInput = (input) => {
    const isLoading = loadingStates[input.setting];

    switch (input.inputType) {
      case "text":
      case "number":
      case "picklist":
        return (
          <>
            {isLoading && <CircularProgress size={20} />}
            {input.inputType === "picklist" ? (
              <FormControl fullWidth variant="outlined" margin="normal">
                <InputLabel>{input.inputLabel}</InputLabel>
                <Select
                  value={inputValues[input.setting] || ""}
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
                value={inputValues[input.setting] || ""}
                onChange={(e) => handleInputChange(e, input.setting)}
                label={input.inputLabel}
                variant="outlined"
                margin="normal"
              />
            )}
          </>
        );
      case "table":
        return (
          <Box sx={{ mt: 2, mb: 2 }}>
            {isLoading ? (
              <CircularProgress />
            ) : (
              tableData && (
                <>
                  <Typography variant="caption" gutterBottom>
                    {input.inputLabel}
                  </Typography>
                  <CustomTable
                    tableData={tableData}
                    onSelectionChange={handleTableSelectionChange}
                    onColumnsChange={handleColumnsChange}
                    paginate={true}
                  />
                </>
              )
            )}
          </Box>
        );
      case "criteria":
        return (
          <Box sx={{ mt: 2, mb: 2 }}>
            {isLoading ? (
              <CircularProgress />
            ) : (
              criteriaData && (
                <FilterContainer
                  initialFilterContainer={criteriaData.filterContainer}
                  filterFields={criteriaData.filterFields}
                  filterOperatorMapping={criteriaData.filterOperatorMapping}
                  hasNameField={criteriaData.hasNameField}
                  onLogicChange={handleCriteriaChange}
                  onValueChange={handleCriteriaChange}
                />
              )
            )}
          </Box>
        );
      default:
        return null;
    }
  };

  /**
   * @param {OnboardWizardStepInput} input
   * @param {number} index
   */
  const shouldRenderInput = (input, index) => {
    if (!input.renderEval) return true;
    if (index === 0) return true; // Always render the first input
    const shouldRender = input.renderEval(
      input.inputType === "criteria" ? tableData : inputValues
    );
    return shouldRender;
  };

  return (
    stepData && (
      <Paper elevation={3} sx={{ mx: "auto", p: 4 }}>
        <Typography variant="h4" component="h2" gutterBottom>
          {stepData.title}
        </Typography>
        <Typography variant="body1" paragraph>
          {parse(stepData.description)}
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
