import React, { useState, useEffect, useRef } from "react";
import {
  Box,
  CircularProgress,
  Typography,
  TextField,

  Button,
  FormControl,

  Grid,
  Tooltip,
  styled,
} from "@mui/material";
import { generateCriteria } from "../Api/Api";
import parse, { domToReact } from "html-react-parser";
import ProspectingCriteriaSelector from "../ProspectingCriteriaSelector/ProspectingCriteriaSelector";
import CustomTable from "../CustomTable/CustomTable";
import CustomSelect from "../CustomSelect/CustomSelect";
import RoleStep from "../RoleStep/RoleStep";

/**
 * @typedef {import('types').OnboardWizardStepInput} OnboardWizardStepInput
 */

const StyledTextField = styled(TextField)({
  '& .MuiInputLabel-root': {
    color: '#533AF3', // Adjust the color to match the blue color in the image
    fontSize: '22px', // Larger font size
    fontWeight: 'normal', // Normal font weight
  },
  '& .MuiInputLabel-root.Mui-focused': {
    color: '#533AF3', // Adjust the color to match the blue color in the image
    fontSize: '22px', // Larger font size
    fontWeight: 'normal', // Normal font weight
    fontFamiliy: '"Albert Sans", sans-serif'
  },
  '& .MuiInput-underline:before': {
    borderBottomColor: '#533AF3', // Blue underline
  },
  '& .MuiInput-underline:hover:not(.Mui-disabled):before': {
    borderBottomColor: '#533AF3', // Blue underline on hover
  },
  '& .MuiInput-underline:after': {
    borderBottomColor: '#533AF3', // Blue underline after focus
  },
  '& .MuiInputBase-input': {
    fontSize: '16px',
    marginTop: "16px"
  },
});

const InfoGatheringStep = ({
  stepData,
  onComplete,
  onTableDisplay,
  settings,
  step
}) => {
  const [inputValues, setInputValues] = useState({ userRole: "placeholder" });
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
      const criteriaOrTableInput = stepData.inputs.find(
        /** @param {OnboardWizardStepInput} input */
        (input) =>
          input.inputType === "prospectingCriteria" ||
          input.inputType === "table"
      );
      if (
        criteriaOrTableInput &&
        criteriaOrTableInput.renderEval(inputValues)
      ) {
        setLoadingState(criteriaOrTableInput.setting, true);
        try {
          const data = await criteriaOrTableInput.dataFetcher({
            ...settingsRef.current,
            ...inputValues,
          });

          const isProspectingCriteria =
            criteriaOrTableInput.inputType === "prospectingCriteria";

          const tableData = isProspectingCriteria
            ? data.data
            : {
              availableColumns: criteriaOrTableInput.availableColumns,
              columns: criteriaOrTableInput.columns,
              data: data.data,
              selectedIds: new Set(),
            };

          setTableData(tableData);
          onTableDisplay(true);

          if (isProspectingCriteria) {
            const fields = await criteriaOrTableInput.fetchFilterFields({
              ...settingsRef.current,
              ...inputValues,
            });
            setFilterFields(fields);
          }
        } catch (error) {
          console.error("Error fetching data:", error);
        } finally {
          setLoadingState(criteriaOrTableInput.setting, false);
        }
      } else {
        setTableData(null);
        onTableDisplay(false);
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

  const handleTableSelectionChange = (newSelectedIds) => {
    setTableData((prev) =>
      prev ? { ...prev, selectedIds: newSelectedIds } : null
    );
  };

  const handleColumnsChange = (newColumns) => {
    setTableData((prev) => (prev ? { ...prev, columns: newColumns } : null));
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
                <CustomSelect
                  value={
                    inputValues[input.setting] || settings[input.setting] || ""
                  }
                  onChange={(e) => handleInputChange(e, input.setting)}
                  label={input.inputLabel}
                  placeholder={input.inputLabel}
                  options={input.options}
                />
              </FormControl>
            ) : (
              <StyledTextField
                fullWidth
                type={input.inputType}
                value={
                  inputValues[input.setting] || settings[input.setting] || ""
                }
                onChange={(e) => handleInputChange(e, input.setting)}
                label={input.inputLabel}
                variant="standard"
                InputLabelProps={{
                  shrink: true,
                }}

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

  if (step === 1) {
    return (
      <RoleStep
        inputValues={inputValues}
        handleInputChange={handleInputChange}
        handleNext={handleSubmit}
      />
    )
  }

  /** @type {import("html-react-parser").HTMLReactParserOptions} */
  const options = {
    replace: (domNode) => {
      // Check if the node is an element node
      if (domNode.type === 'tag') {
        if (domNode.name === 'h1') {
          return <Typography variant="h1">{domToReact(domNode.children)}</Typography>;
        }
        if (domNode.name === 'h2') {
          return <Typography variant="h2">{domToReact(domNode.children)}</Typography>;
        }
        if (domNode.name === 'h3') {
          return <Typography variant="h3">{domToReact(domNode.children)}</Typography>;
        }
        if (domNode.name === 'p') {
          return <Typography variant="body1" paragraph>{domToReact(domNode.children)}</Typography>;
        }

        // Default case for all other elements
        return domNode;
      }
    },
  };

  return (
    stepData && (
      <Box sx={{ p: 4 }}>
        <Typography
          variant="h2"
          component="h2"
          gutterBottom
          sx={{
            letterSpacing: "-1.2px",
          }}
        >
          {stepData.title}
        </Typography>
        {parse(renderedDescription, options)}
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
        <Box mt={2} sx={{ width: "100%", display: "flex", justifyContent: "center" }}>
          <Button
            onClick={handleSubmit}
            variant="contained"
            color="primary"
            sx={{
              background: "linear-gradient(131.16deg, #FF7D2F 24.98%, #491EFF 97.93%)",
              width: "271px",
              height: "52px",
              borderRadius: "40px",
              fontWeight: "700",
              fontSize: "32px",
              letterSpacing: "-0.96px",
              textTransform: "none"
            }}

          >
            Next
          </Button>
        </Box>
      </Box>
    )
  );
};

export default InfoGatheringStep;
