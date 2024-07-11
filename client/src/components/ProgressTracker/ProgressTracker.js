import React from "react";
import { Box, Stepper, Step, StepButton, Typography } from "@mui/material";

const ProgressTracker = ({
  steps,
  currentStep,
  onStepClick,
  canNavigateToStep,
  orientation = "horizontal",
}) => {
  return (
    <Box sx={{ width: "100%" }}>
      <Stepper activeStep={currentStep - 1} orientation={orientation}>
        {steps.map((step, index) => (
          <Step key={index}>
            <StepButton
              onClick={() => onStepClick(index + 1)}
              disabled={!canNavigateToStep[index + 1]}
            >
              <Typography variant="body2">{step.title}</Typography>
            </StepButton>
          </Step>
        ))}
      </Stepper>
      <Typography variant="caption" display="block" textAlign="center" mt={2}>
        Step {currentStep} of {steps.length}
      </Typography>
    </Box>
  );
};

export default ProgressTracker;
