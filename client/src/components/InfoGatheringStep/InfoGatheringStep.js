import React, { useState, useEffect, useRef } from "react";
import {
  Box,
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
  /** @type {[TableData | null, Function]} */
  const [tableData, setTableData] = useState(
    /** @type {TableData | null} */ (null)
  );

  const settingsRef = useRef(settings);

  useEffect(() => {
    settingsRef.current = settings;
  }, [settings]);

  useEffect(() => {
    const fetchTableData = async () => {
      const tableInput = stepData.inputs.find(
        (input) =>
          input.inputType === "table" &&
          shouldRenderInput(input, stepData.inputs.indexOf(input))
      );

      if (tableInput && tableInput.dataFetcher) {
        const data = await tableInput.dataFetcher({
          ...settingsRef.current,
          ...inputValues,
        });
        if (data.success && data.data.length > 0) {
          setTableData({
            availableColumns: tableInput.availableColumns,
            columns: tableInput.columns,
            data: data.data,
            selectedIds: new Set(),
          });
          onTableDisplay(true);
        } else if (data.message.toLowerCase().includes("session expired")) {
          navigate("/");
        }
      } else {
        setTableData(null);
        onTableDisplay(false);
      }
    };

    fetchTableData();
  }, [stepData, inputValues]);

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
        value: Array.from(tableData.selectedIds),
      });
    }

    onComplete(completedInputs);
  };

  const renderInput = (input) => {
    switch (input.inputType) {
      case "text":
      case "number":
        return (
          <TextField
            fullWidth
            type={input.inputType}
            value={inputValues[input.setting] || ""}
            onChange={(e) => handleInputChange(e, input.setting)}
            label={input.inputLabel}
            variant="outlined"
            margin="normal"
          />
        );
      case "picklist":
        return (
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
        );
      case "table":
        return tableData ? (
          <CustomTable
            tableData={tableData}
            onSelectionChange={handleTableSelectionChange}
            onColumnsChange={handleColumnsChange}
            paginate={true}
          />
        ) : null;
      default:
        return null;
    }
  };

  const shouldRenderInput = (input, index) => {
    if (!input.renderEval) return true;
    if (index === 0) return true; // Always render the first input

    return input.renderEval(inputValues);
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
