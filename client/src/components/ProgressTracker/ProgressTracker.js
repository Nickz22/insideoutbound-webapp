import React from "react";
import { Box, Stepper, Step, StepLabel } from "@mui/material";

/** @typedef {import("types/OnboardWizardStep").OnboardWizardStep} OnboardWizardStep */
/** @typedef {{steps: (OnboardWizardStep | {title: string;})[]; currentStep: number; onStepClick: (stepIndex: number) => void; orientation: import("@mui/material").Orientation }} Props */

function CheckIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M0 9.05013C0.0295273 8.30397 0.345279 7.75997 0.990118 7.46258C1.64305 7.16129 2.2617 7.27702 2.79462 7.76437C3.61043 8.51053 4.41386 9.27134 5.22253 10.0263C5.37635 10.1699 5.52923 10.3144 5.68353 10.457C5.91642 10.6714 6.12311 10.6611 6.33123 10.4199C8.08382 8.38943 9.83546 6.35848 11.588 4.32802C12.7734 2.95436 13.9593 1.58167 15.1437 0.207524C15.2899 0.0380751 15.4604 -0.0468936 15.6814 0.0278202C15.8686 0.0908143 16.0076 0.263682 15.9995 0.465849C15.9952 0.574257 15.9524 0.691455 15.8957 0.784725C14.5527 3.01149 13.2054 5.23533 11.8586 7.45965C10.3084 10.0204 8.75771 12.5802 7.20848 15.1415C6.93797 15.5883 6.56935 15.8916 6.05405 15.9761C5.47065 16.0718 4.98345 15.8789 4.61198 15.4145C3.28182 13.7517 1.95833 12.0836 0.631028 10.4179C0.382903 10.1064 0.118109 9.80557 0.046196 9.38952C0.0252411 9.26988 0.0133349 9.14877 0 9.05013Z" fill="white" />
    </svg>
  )
}

/** @param {import("@mui/material").StepIconProps} props */
function ColorlibStepIcon(props) {
  const { active, completed } = props;

  return (
    <div style={{
      width: "32px",
      height: "32px",
      background: active ? "linear-gradient(137.17deg, #FF7D2F 21%, #491EFF 82.81%)" : "rgba(14, 20, 32, 1)",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      color: active ? "rgba(255, 255, 255, 1)" : "rgba(135, 159, 202, 1)",
      borderRadius: "100%",
      fontSize: "18px",
      fontWeight: active ? "700" : "300",
    }}>
      {completed ? <CheckIcon /> : props.icon}
    </div>
  )
}

/** @param {Props} props */
const ProgressTracker = ({
  steps,
  currentStep,
  onStepClick,
  orientation = "horizontal",
}) => {
  return (
    <Box sx={{ width: "100%" }}>
      <Stepper activeStep={currentStep - 1} orientation={orientation} connector={undefined}>
        {steps.map((step, index) => (
          <Step
            key={index}
            onClick={() => onStepClick(index + 1)}
            disabled={index + 1 > currentStep}
            sx={{
              cursor: "pointer"
            }}
          >
            <StepLabel
              sx={{
                "& .MuiStepLabel-label": {
                  fontSize: "18px",
                  color: "rgba(135, 159, 202, 1)",
                  fontWeight: "300"
                },
                "& .MuiStepLabel-label.Mui-active": {
                  fontSize: "18px",
                  color: "rgba(255, 255, 255, 1)",
                  fontWeight: "500"
                },
                "& .MuiStepLabel-label.Mui-completed": {
                  fontSize: "18px",
                  color: "rgba(255, 255, 255, 1)",
                  fontWeight: "300"
                }
              }}
              StepIconComponent={ColorlibStepIcon}
            >
              {step.title}
            </StepLabel>
          </Step>
        ))}
      </Stepper>
    </Box>
  );
};

export default ProgressTracker;
