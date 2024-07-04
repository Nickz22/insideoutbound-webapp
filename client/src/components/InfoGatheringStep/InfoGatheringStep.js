import React, { useState, useEffect } from "react";
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

/**
 * @typedef {import('@mui/material/Select').SelectChangeEvent<string>} SelectChangeEvent
 * @typedef {import('types').OnboardWizardStep} OnboardWizardStep
 * @typedef {import('types').OnboardWizardStepInput} OnboardWizardStepInput
 * @typedef {import('types').TableColumn} TableColumn
 */

/**
 * @param {{ stepData: OnboardWizardStep | OnboardWizardStep[], onComplete: Function, onTableDisplay: Function}} props
 */
const InfoGatheringStep = ({ stepData, onComplete, onTableDisplay }) => {
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  /** @type {[{ [key: string]: string }, Function]} */
  const [inputValues, setInputValues] = useState({});
  /** @type {[{ columns: TableColumn[], data: any[], selectedIds: Set<string> }, Function]} */
  const [tableData, setTableData] = useState({
    columns: [],
    data: [],
    selectedIds: new Set(),
  });

  useEffect(() => {
    if (steps[currentStepIndex].type === "table") {
      fetchTableData();
      onTableDisplay(true);
    } else {
      onTableDisplay(false);
    }
  }, [currentStepIndex, onTableDisplay]);

  const steps = Array.isArray(stepData) ? stepData : [stepData];

  useEffect(() => {
    // Evaluate next step when input values change
    if (Array.isArray(stepData) && currentStepIndex < steps.length - 1) {
      const nextStep = steps[currentStepIndex + 1];
      if (shouldRenderStep(nextStep, currentStepIndex + 1)) {
        setCurrentStepIndex(currentStepIndex + 1);
      }
    }
  }, [inputValues]);

  const fetchTableData = async () => {
    const currentStep = steps[currentStepIndex];
    if (currentStep.type === "table" && currentStep.dataFetcher) {
      const data = await currentStep.dataFetcher();
      setTableData({
        columns: currentStep.columns,
        data: data.data,
        selectedIds: new Set(),
      });
    }
  };

  /**
   * Handles changes to the input components.
   * @param {SelectChangeEvent | React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>} event
   * @param {string} setting
   */
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
    if (tableData.selectedIds.size > 0) {
      completedInputs.push({
        label: "selectedTeammates",
        value: Array.from(tableData.selectedIds),
      });
    }
    onComplete(completedInputs);
  };

  /**
   * @param {OnboardWizardStepInput} input
   * @returns {JSX.Element | null}
   */
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
      default:
        return null;
    }
  };

  /**
   * Toggles the selected state of a table row.
   * @param {any} item table row data
   */
  const handleToggle = (item) => {
    setTableData((prev) => {
      const newSelectedIds = new Set(prev.selectedIds);
      if (newSelectedIds.has(item.Id)) {
        newSelectedIds.delete(item.Id);
      } else {
        newSelectedIds.add(item.Id);
      }
      return { ...prev, selectedIds: newSelectedIds };
    });
  };

  /**
   * Determines if the current step should be rendered based on the previous step's input.
   * @param {OnboardWizardStep} step
   * @param {number} index
   * @returns {boolean}
   **/
  const shouldRenderStep = (step, index) => {
    if (!step.renderEval) return true;
    const prevStep = steps[index - 1];
    return (
      prevStep?.inputs?.some(
        (input) =>
          step?.renderEval &&
          step.renderEval(input.inputLabel, inputValues[input.setting])
      ) || false
    );
  };

  /**
   * Renders a single step based on its type.
   * @param {OnboardWizardStep} step
   * @param {number} index
   * @returns {JSX.Element | null}
   */
  const renderStep = (step, index) => {
    if (!shouldRenderStep(step, index)) return null;

    switch (step.type) {
      case "input":
        return (
          <Grid container spacing={2}>
            {step?.inputs?.map((input, inputIndex) => (
              <Grid item xs={12} sm={6} key={inputIndex}>
                {renderInput(input)}
              </Grid>
            ))}
          </Grid>
        );
      case "table":
        return (
          <CustomTable
            columns={tableData.columns}
            data={tableData.data}
            onToggle={handleToggle}
          />
        );
      default:
        return null;
    }
  };

  return (
    <Paper elevation={3} sx={{ mx: "auto", p: 4 }}>
      {steps.slice(0, currentStepIndex + 1).map((step, index) => (
        <Box key={index} mb={4}>
          <Typography variant="h4" component="h2" gutterBottom>
            {step.title}
          </Typography>
          <Typography variant="body1" paragraph>
            {parse(step.description)}
          </Typography>
          {renderStep(step, index)}
        </Box>
      ))}
      {currentStepIndex === steps.length - 1 && (
        <Box mt={2}>
          <Button
            variant="contained"
            color="primary"
            onClick={handleSubmit}
            size="large"
            fullWidth
          >
            Complete
          </Button>
        </Box>
      )}
    </Paper>
  );
};

export default InfoGatheringStep;
