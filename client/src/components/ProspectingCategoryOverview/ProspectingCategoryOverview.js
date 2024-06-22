import React, { useEffect, useState } from "react";
import {
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Box,
  ThemeProvider,
  createTheme,
  CssBaseline,
  Grid,
  AppBar,
  Toolbar,
} from "@mui/material";
import { styled } from "@mui/system";
import FilterContainer from "../FilterContainer/FilterContainer";

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
  marginBottom: theme.spacing(4),
  backgroundColor: "#ffffff",
  transition: "box-shadow 0.3s ease-in-out",
  "&:hover": {
    boxShadow: "0 6px 12px rgba(0, 0, 0, 0.15)",
  },
  height: "500px", // Fixed height for the card
  display: "flex",
  flexDirection: "column",
}));

const ScrollableFilters = styled(Box)({
  flexGrow: 1,
  overflowY: "auto",
  display: "flex",
  flexDirection: "column",
});

const ProspectingCategoryOverview = ({
  proposedFilterContainers,
  onSave,
  taskFilterFields,
}) => {
  const [filterContainers, setFilterContainers] = useState([]);
  const [logicErrors, setLogicErrors] = useState({});

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

  const handleAddFilter = (filterIndex) => {
    setFilterContainers((currentFilters) => {
      const newFilterContainers = [...currentFilters];
      newFilterContainers[filterIndex].filters.push({
        field: "",
        operator: "",
        value: "",
        dataType: "string", // default data type
      });
      return newFilterContainers;
    });
  };

  const handleSave = () => {
    onSave(filterContainers);
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

  const handleTitleChange = (filterContainerIndex, newTitle) => {
    setFilterContainers((currentFilters) => {
      const newFilterContainers = [...currentFilters];
      newFilterContainers[filterContainerIndex].name = newTitle;
      return newFilterContainers;
    });
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ p: 4, pb: 10 }}>
        <Typography
          variant="h4"
          fontFamily="Roboto"
          fontWeight="lighter"
          gutterBottom
        >
          Prospecting Activity Filters
        </Typography>
        <Grid container spacing={3}>
          {filterContainers.map((filterContainer, filterIndex) => (
            <Grid item xs={12} lg={6} key={filterIndex}>
              <StyledCard>
                <CardContent
                  sx={{
                    height: "100%",
                    display: "flex",
                    flexDirection: "column",
                  }}
                >
                  <Box mb={2}>
                    <TextField
                      fullWidth
                      value={filterContainer.name}
                      onChange={(e) =>
                        handleTitleChange(filterIndex, e.target.value)
                      }
                      variant="outlined"
                    />
                  </Box>
                  <ScrollableFilters>
                    <FilterContainer
                      filters={filterContainer.filters}
                      taskFilterFields={taskFilterFields}
                      FILTER_OPERATOR_MAPPING={FILTER_OPERATOR_MAPPING}
                      onFieldChange={(value, idx) =>
                        handleFieldChange(filterIndex, value, idx)
                      }
                      onOperatorChange={(value, idx) =>
                        handleOperatorChange(filterIndex, value, idx)
                      }
                      onValueChange={(value, idx) =>
                        handleValueChange(filterIndex, value, idx)
                      }
                      onDeleteFilter={(idx) =>
                        handleDeleteFilter(filterIndex, idx)
                      }
                      onAddFilter={() => handleAddFilter(filterIndex)}
                      onLogicChange={(value) =>
                        handleLogicChange(filterIndex, value)
                      }
                      filterLogic={filterContainer.filterLogic}
                      logicError={logicErrors[filterIndex]}
                    />
                  </ScrollableFilters>
                </CardContent>
              </StyledCard>
            </Grid>
          ))}
        </Grid>
      </Box>
      <AppBar
        position="fixed"
        color="transparent"
        sx={{
          top: "auto",
          bottom: 0,
          backgroundColor: "rgba(255, 255, 255, 0.7)",
        }}
      >
        <Toolbar>
          <Box sx={{ flexGrow: 1 }} />
          <Button
            variant="contained"
            color="info"
            size="large"
            onClick={() => onSave(filterContainers)}
          >
            Save Changes
          </Button>
        </Toolbar>
      </AppBar>
    </ThemeProvider>
  );
};

export default ProspectingCategoryOverview;
