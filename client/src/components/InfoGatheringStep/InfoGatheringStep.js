import React, { useState, useEffect } from "react";
import {
  Box,
  Typography,
  TextField,
  Button,
  Switch,
  FormControlLabel,
  Select,
  MenuItem,
} from "@mui/material";
import FilterContainer from "../FilterContainer/FilterContainer";

const InfoGatheringStep = ({
  stepData,
  onComplete,
  onInputChange,
  stepIndex,
  filterFields,
  FILTER_OPERATOR_MAPPING,
}) => {
  const isArrayStep = Array.isArray(stepData);
  const [responses, setResponses] = useState(
    isArrayStep ? new Array(stepData.length).fill(null) : null
  );

  useEffect(() => {
    setResponses(isArrayStep ? new Array(stepData.length).fill(null) : null);
  }, [stepIndex, isArrayStep]);

  const handleInputChange = (index, value, title) => {
    if (isArrayStep) {
      setResponses((prev) => {
        const newResponses = [...prev];
        newResponses[index] = { label: title, value: value };
        return newResponses;
      });
    } else {
      setResponses({ label: title, value: value });
    }
    onInputChange({ label: title, value: value });
  };

  const handleComplete = () => {
    onComplete(responses);
  };

  const renderInput = (inputData, index) => {
    switch (inputData.inputType) {
      case "text":
      case "number":
        return (
          <TextField
            fullWidth
            variant="outlined"
            label={inputData.inputLabel}
            type={inputData.inputType}
            value={
              isArrayStep
                ? responses[index].value || ""
                : responses?.value || ""
            }
            onChange={(e) =>
              handleInputChange(index, e.target.value, inputData.setting)
            }
            margin="normal"
          />
        );
      case "boolean":
        return (
          <FormControlLabel
            control={
              <Switch
                checked={
                  isArrayStep
                    ? responses[index]?.value || false
                    : responses?.value || false
                }
                onChange={(e) =>
                  handleInputChange(index, e.target.checked, inputData.setting)
                }
                color="primary"
              />
            }
            label={inputData.inputLabel}
          />
        );
      case "picklist":
        return (
          <Select
            fullWidth
            value={
              isArrayStep
                ? responses[index]?.value || ""
                : responses?.value || ""
            }
            onChange={(e) =>
              handleInputChange(index, e.target.value, inputData.setting)
            }
            label={inputData.inputLabel}
          >
            {inputData.options.map((option) => (
              <MenuItem key={option} value={option}>
                {option}
              </MenuItem>
            ))}
          </Select>
        );
      case "filterContainer":
        return (
          <FilterContainer
            filterContainer={
              isArrayStep
                ? responses[index]?.value?.filterContainer || {
                    filters: [],
                    filterLogic: "",
                    name: "",
                  }
                : responses?.filterContainer?.value || {
                    filters: [],
                    filterLogic: "",
                    name: "",
                  }
            }
            filterFields={filterFields}
            filterOperatorMapping={FILTER_OPERATOR_MAPPING}
            onLogicChange={(newData) =>
              handleInputChange(index, newData, inputData.setting)
            }
            hasNameField={false}
          />
        );
      default:
        return null;
    }
  };

  const renderArrayStep = () => {
    return stepData.map((subStep, index) => (
      <Box
        key={index}
        mt={2}
        style={{
          display:
            index === 0 || responses[index - 1]?.value !== null
              ? "block"
              : "none",
        }}
      >
        <Typography variant="subtitle1" gutterBottom>
          {subStep.title}
        </Typography>
        <Typography variant="body2" paragraph>
          {subStep.description}
        </Typography>
        {renderInput(subStep, index)}
      </Box>
    ));
  };

  const renderSingleStep = () => {
    return (
      <>
        <Typography variant="h6" gutterBottom>
          {stepData.title}
        </Typography>
        <Typography variant="body1" paragraph>
          {stepData.description}
        </Typography>
        {renderInput(stepData, 0)}
      </>
    );
  };

  return (
    <Box display="flex" flexDirection="column" alignItems="stretch" p={3}>
      {isArrayStep ? renderArrayStep() : renderSingleStep()}
      <Button
        variant="contained"
        color="primary"
        onClick={handleComplete}
        sx={{ mt: 2, alignSelf: "center" }}
        disabled={
          isArrayStep ? responses?.value?.some((r) => !r) : !responses?.value
        }
      >
        Next
      </Button>
    </Box>
  );
};

export default InfoGatheringStep;
