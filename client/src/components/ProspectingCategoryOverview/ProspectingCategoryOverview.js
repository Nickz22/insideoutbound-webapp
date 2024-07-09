import React, { useEffect, useState } from "react";
import {
  Typography,
  Button,
  Box,
  ThemeProvider,
  createTheme,
  CssBaseline,
  Grid,
  AppBar,
  Toolbar,
} from "@mui/material";
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
  }
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
      fontFamily: `"Roboto", "Helvetica", "Arial", sans-serif`,
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

const ProspectingCategoryOverview = ({
  proposedFilterContainers,
  onSave,
  taskFilterFields,
}) => {
  const [filterContainers, setFilterContainers] = useState([]);

  useEffect(() => {
    if (proposedFilterContainers) {
      setFilterContainers(proposedFilterContainers);
    }
  }, [proposedFilterContainers]);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ p: 4, pb: 10 }}>
        <Typography variant="h4" fontWeight="lighter" gutterBottom>
          Prospecting Activity Filters
        </Typography>
        <Grid container spacing={3}>
          {filterContainers.map((filterContainer, filterIndex) => (
            <Grid item xs={12} lg={6} key={filterIndex}>
              <FilterContainer
                filterContainer={filterContainer}
                filterFields={taskFilterFields}
                filterOperatorMapping={FILTER_OPERATOR_MAPPING}
                hasNameField={true}
              />
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
