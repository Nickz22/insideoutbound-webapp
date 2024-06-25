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

/**
 * @typedef {import('types').OnboardWizardStep} OnboardWizardStep
 * @typedef {import('types').CriteriaField} CriteriaField
 */

const nextValidityWhitelist = ["activateByMeeting", "activateByOpportunity"];

/**
 *
 * @param {{stepData: OnboardWizardStep | OnboardWizardStep[], onComplete: function, onInputChange: function, stepIndex: number, filterFields: CriteriaField[], filterOperatorMapping: { [key: string]: {[key:string]: string} }}} props
 * @returns
 */
const InfoGatheringStep = ({
  stepData,
  onComplete,
  onInputChange,
  stepIndex,
  filterFields,
  filterOperatorMapping,
}) => {
  const isArrayStep = Array.isArray(stepData);
  /**
   * @type {[{label:string, value: any}[] | null, function]}
   **/
  const [responses, setResponses] = useState(
    isArrayStep ? new Array(stepData.length).fill(null) : [null]
  );

  useEffect(() => {
    setResponses(
      isArrayStep
        ? stepData.map((step) => ({ label: step.setting, value: "" }))
        : [{ label: stepData.setting, value: "" }]
    );
  }, [stepIndex, isArrayStep]);

  /**
   *
   * @param {number} index
   * @param {string | boolean | number} value
   * @param {string} title
   */
  const handleInputChange = (index, value, title) => {
    if (isArrayStep) {
      setResponses(
        /** @param {{ label: string, value: any }[]} prev */
        (prev) => {
          const newResponses = [...prev];
          newResponses[index] = { label: title, value: value };
          return newResponses;
        }
      );
    } else {
      setResponses([{ label: title, value: value }]);
    }
    onInputChange({ label: title, value: value });
  };

  const handleComplete = () => {
    onComplete(responses);
  };

  /**
   *
   * @param {OnboardWizardStep} inputData
   * @param {number} index
   * @returns
   */
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
            value={(responses && responses[index]?.value) || ""}
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
                checked={(responses && responses[index]?.value) || false}
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
            value={(responses && responses[index]?.value) || ""}
            onChange={(e) =>
              handleInputChange(index, e.target.value, inputData.setting)
            }
            label={inputData.inputLabel}
          >
            {inputData.options?.map((option) => (
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
              (responses && responses[index]?.value?.filterContainer) || {
                filters: [],
                filterLogic: "",
                name: "",
              }
            }
            filterFields={filterFields}
            filterOperatorMapping={filterOperatorMapping}
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
    const step = Array.isArray(stepData) ? stepData : [stepData];
    return step.map((subStep, index) => (
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
    const step = Array.isArray(stepData) ? stepData[0] : stepData;
    return (
      <>
        <Typography variant="h6" gutterBottom>
          {step.title}
        </Typography>
        <Typography variant="body1" paragraph>
          {step.description}
        </Typography>
        {renderInput(step, 0)}
      </>
    );
  };

  return (
    responses && (
      <Box display="flex" flexDirection="column" alignItems="stretch" p={3}>
        {isArrayStep ? renderArrayStep() : renderSingleStep()}
        <Button
          variant="contained"
          color="primary"
          onClick={handleComplete}
          sx={{ mt: 2, alignSelf: "center" }}
          disabled={responses?.some(
            (r) => !r?.value && !nextValidityWhitelist.includes(r?.label)
          )}
        >
          Next
        </Button>
      </Box>
    )
  );
};

export default InfoGatheringStep;
