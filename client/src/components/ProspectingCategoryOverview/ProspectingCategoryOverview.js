import React, { useEffect, useState } from "react";
import {
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Box,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  ThemeProvider,
  createTheme,
  CssBaseline,
  Divider,
  Grid,
  IconButton,
  Tooltip,
} from "@mui/material";
import { styled } from "@mui/system";
import DeleteIcon from "@mui/icons-material/Delete";
import AddIcon from "@mui/icons-material/Add";

const FILTER_OPERATOR_MAPPING = {
  string: {
    contains: "LIKE",
    equals: "=",
    "not equals": "!=",
  },
  int: {
    equals: "=",
    "not equals": "!=",
    "less than": "<",
    "less than or equal": "<=",
    "greater than": ">",
    "greater than or equal": ">=",
  },
};

const theme = createTheme({
  palette: {
    background: {
      default: "#f5f5f5",
    },
  },
  typography: {
    h4: {
      fontWeight: 600,
      marginBottom: "1rem",
    },
    h6: {
      fontWeight: 500,
      marginBottom: "0.5rem",
    },
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: "0 4px 6px rgba(0, 0, 0, 0.1)",
          borderRadius: "8px",
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: "20px",
          textTransform: "none",
          fontWeight: 600,
        },
      },
    },
  },
});

const StyledCard = styled(Card)(({ theme }) => ({
  marginBottom: theme.spacing(3),
  backgroundColor: "#ffffff",
  transition: "box-shadow 0.3s ease-in-out",
  "&:hover": {
    boxShadow: "0 6px 12px rgba(0, 0, 0, 0.15)",
  },
}));

const FilterContainer = styled(Box)(({ theme }) => ({
  marginBottom: theme.spacing(2),
  padding: theme.spacing(2),
  backgroundColor: "#f9f9f9",
  borderRadius: "4px",
}));

const ProspectingCategoryOverview = ({
  proposedFilterContainers,
  onSave,
  taskFilterFields,
}) => {
  const [filterContainers, setFilterContainers] = useState(undefined);
  const [logicErrors, setLogicErrors] = useState({}); // Track logic errors by filterContainer index

  useEffect(() => {
    if (proposedFilterContainers) {
      setFilterContainers(proposedFilterContainers);
    }
  }, [proposedFilterContainers]);

  const handleFieldChange = (filterContainerIndex, value, filterFieldIndex) => {
    // Update field value for specific filterContainer in a similar manner to handleValueChange
    setFilterContainers((currentFilters) => {
      const newFilterContainers = [...currentFilters];
      const targetFilter =
        newFilterContainers[filterContainerIndex].filters[filterFieldIndex];
      // Update the target filter with new field value and reset value and operator
      newFilterContainers[filterContainerIndex].filters[filterFieldIndex] = {
        ...targetFilter,
        field: value,
        value: "", // Reset value when field changes
        operator: "", // Reset operator when field changes
        dataType: taskFilterFields.find((field) => field.name === value).type,
      };
      return newFilterContainers;
    });
  };

  const handleOperatorChange = (
    filterContainerIndex,
    value,
    filterFieldIndex
  ) => {
    // Update operator for specific filterContainer
    setFilterContainers((currentFilters) => {
      const newFilterContainers = [...currentFilters];
      newFilterContainers[filterContainerIndex].filters[
        filterFieldIndex
      ].operator = value;
      return newFilterContainers;
    });
  };

  const handleValueChange = (filterContainerIndex, value, filterFieldIndex) => {
    // Update value for specific filterContainer
    setFilterContainers((currentFilters) => {
      const newFilterContainers = [...currentFilters];
      newFilterContainers[filterContainerIndex].filters[
        filterFieldIndex
      ].value = value;
      return newFilterContainers;
    });
  };

  const handleLogicChange = (filterContainerIndex, value) => {
    const error = validateFilterLogic(filterContainerIndex, value);
    setFilterContainers((currentFilters) => {
      const newFilterContainers = [...currentFilters];
      newFilterContainers[filterContainerIndex].filterLogic = value;
      return newFilterContainers;
    });
    // Update logic error state
    setLogicErrors((currentErrors) => ({
      ...currentErrors,
      [filterContainerIndex]: error,
    }));
  };

  const validateFilterLogic = (filterContainerIndex, logicInput) => {
    const filterContainer = filterContainers[filterContainerIndex];
    const numberOfFilters = filterContainer.filters.length;
    const logicInputNumbers = logicInput.match(/\d+/g) || [];

    for (let number of logicInputNumbers) {
      if (parseInt(number, 10) > numberOfFilters) {
        return `Error: Logic input contains a number (${number}) greater than the number of filters (${numberOfFilters}).`;
      }
    }

    // If no errors, return null or an empty string
    return null;
  };

  const handleDeleteFilter = (filterContainerIndex, filterIndex) => {
    setFilterContainers((currentFilters) => {
      const newFilterContainers = [...currentFilters];
      const targetContainer = newFilterContainers[filterContainerIndex];

      // Remove the filter at the specified index
      targetContainer.filters.splice(filterIndex, 1);
      return newFilterContainers;
    });

    // Set a default error message
    setLogicErrors((currentErrors) => ({
      ...currentErrors,
      [filterContainerIndex]:
        "Filter deleted. Please review and update the logic.",
    }));
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ p: 3 }}>
        <Typography variant="h4" gutterBottom>
          Prospecting Categories
        </Typography>
        {filterContainers &&
          filterContainers.map((filterContainer, filterIndex) => (
            <StyledCard key={filterIndex}>
              <CardContent>
                <Typography variant="h6">{filterContainer.name}</Typography>
                <Divider sx={{ my: 2 }} />
                {filterContainer.filters.map((filter, idx) => {
                  const fieldDefinition = taskFilterFields.find(
                    (field) => field.name === filter.field
                  );
                  return (
                    <FilterContainer key={idx}>
                      <Grid container spacing={2} alignItems="center">
                        <Grid item xs={12} sm={3}>
                          <FormControl fullWidth size="small">
                            <InputLabel>Field</InputLabel>
                            <Select
                              value={filter.field}
                              label="Field"
                              onChange={(event) =>
                                handleFieldChange(
                                  filterIndex,
                                  event.target.value,
                                  idx
                                )
                              }
                            >
                              {taskFilterFields.map((field) => (
                                <MenuItem key={field.name} value={field.name}>
                                  {field.name}
                                </MenuItem>
                              ))}
                            </Select>
                          </FormControl>
                        </Grid>
                        <Grid item xs={12} sm={3}>
                          <FormControl fullWidth size="small">
                            <InputLabel>Operator</InputLabel>
                            <Select
                              value={filter.operator}
                              label="Operator"
                              onChange={(event) =>
                                handleOperatorChange(
                                  filterIndex,
                                  event.target.value,
                                  idx
                                )
                              }
                            >
                              {Object.entries(
                                FILTER_OPERATOR_MAPPING[filter.dataType] || {}
                              ).map(([key, value]) => (
                                <MenuItem key={key} value={key}>
                                  {key}
                                </MenuItem>
                              ))}
                            </Select>
                          </FormControl>
                        </Grid>
                        <Grid item xs={12} sm={5}>
                          {fieldDefinition &&
                          fieldDefinition.type === "picklist" ? (
                            <FormControl fullWidth size="small">
                              <InputLabel>Value</InputLabel>
                              <Select
                                value={filter.value}
                                label="Value"
                                onChange={(event) =>
                                  handleValueChange(
                                    filterIndex,
                                    event.target.value,
                                    idx
                                  )
                                }
                              >
                                {fieldDefinition.options.map((option) => (
                                  <MenuItem
                                    key={option.value}
                                    value={option.value}
                                  >
                                    {option.label}
                                  </MenuItem>
                                ))}
                              </Select>
                            </FormControl>
                          ) : (
                            <TextField
                              fullWidth
                              label="Value"
                              value={filter.value}
                              variant="outlined"
                              size="small"
                              onChange={(event) =>
                                handleValueChange(
                                  filterIndex,
                                  event.target.value,
                                  idx
                                )
                              }
                            />
                          )}
                        </Grid>
                        <Grid item xs={12} sm={1}>
                          <Tooltip title="Remove filter">
                            <IconButton
                              aria-label="delete"
                              onClick={() =>
                                handleDeleteFilter(filterIndex, idx)
                              }
                            >
                              <DeleteIcon />
                            </IconButton>
                          </Tooltip>
                        </Grid>
                      </Grid>
                    </FilterContainer>
                  );
                })}
                <Box sx={{ mt: 2 }}>
                  <Button
                    startIcon={<AddIcon />}
                    onClick={() => {
                      /* Implement add filter logic */
                    }}
                  >
                    Add Filter
                  </Button>
                </Box>
                <TextField
                  label="Logic"
                  value={filterContainer.filterLogic}
                  variant="outlined"
                  fullWidth
                  margin="normal"
                  error={!!logicErrors[filterIndex]}
                  helperText={logicErrors[filterIndex]}
                  onChange={(event) =>
                    handleLogicChange(filterIndex, event.target.value)
                  }
                />
              </CardContent>
            </StyledCard>
          ))}
        <Box sx={{ display: "flex", justifyContent: "flex-end", mt: 3 }}>
          <Button
            variant="contained"
            color="primary"
            size="large"
            onClick={onSave}
          >
            Save Changes
          </Button>
        </Box>
      </Box>
    </ThemeProvider>
  );
};

export default ProspectingCategoryOverview;
