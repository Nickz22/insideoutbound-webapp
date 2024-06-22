import React, { useState, useEffect } from "react";
import {
  Box,
  Typography,
  TextField,
  Button,
  Switch,
  FormControlLabel,
} from "@mui/material";

const InfoGatheringStep = ({ stepData, onComplete, stepIndex }) => {
  const [inputValue, setInputValue] = useState(() => {
    switch (stepData.inputType) {
      case "boolean":
        return false;
      case "number":
        return ""; // Changed to empty string
      default:
        return "";
    }
  });

  useEffect(() => {
    // Reset input value when stepIndex changes
    setInputValue(() => {
      switch (stepData.inputType) {
        case "boolean":
          return false;
        case "number":
          return ""; // Changed to empty string
        default:
          return "";
      }
    });
  }, [stepIndex, stepData.inputType]);

  const handleComplete = () => {
    // For number inputs, convert empty string to null or undefined
    const valueToSubmit =
      stepData.inputType === "number" && inputValue === "" ? null : inputValue;
    onComplete(valueToSubmit);
    // Reset is handled by useEffect when stepIndex changes
  };

  const renderInput = () => {
    switch (stepData.inputType) {
      case "text":
        return (
          <TextField
            fullWidth
            variant="outlined"
            label={stepData.inputLabel}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            margin="normal"
          />
        );
      case "boolean":
        return (
          <FormControlLabel
            control={
              <Switch
                checked={inputValue}
                onChange={(e) => setInputValue(e.target.checked)}
                color="primary"
              />
            }
            label={stepData.inputLabel}
          />
        );
      case "number":
        return (
          <TextField
            fullWidth
            variant="outlined"
            label={stepData.inputLabel}
            type="number"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)} // Changed to directly use string value
            margin="normal"
          />
        );
      default:
        return null;
    }
  };

  return (
    <Box display="flex" flexDirection="column" alignItems="center" p={3}>
      <Typography variant="h6" gutterBottom>
        {stepData.title}
      </Typography>
      <Typography variant="body1" paragraph>
        {stepData.description}
      </Typography>
      {renderInput()}
      <Button
        variant="contained"
        color="primary"
        onClick={handleComplete}
        sx={{ mt: 2 }}
      >
        Next
      </Button>
    </Box>
  );
};

export default InfoGatheringStep;
