import React, { useState, useEffect } from "react";
import { Box, Button, Typography, CircularProgress } from "@mui/material";
import FilterContainer from "./../FilterContainer/FilterContainer";
import { fetchTaskFilterFields, getTaskQueryCount } from "../Api/Api";
import { FILTER_OPERATOR_MAPPING } from "./../../utils/c";

const TaskQueryCounter = () => {
  const [taskFilterFields, setTaskFilterFields] = useState([]);
  const [criteria, setCriteria] = useState({
    name: "Task Query",
    filters: [],
    filterLogic: "",
  });
  const [queryCount, setQueryCount] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchFields = async () => {
      try {
        const response = await fetchTaskFilterFields();
        if (response.success) {
          setTaskFilterFields(response.data);
        } else {
          setError("Failed to fetch task filter fields");
        }
      } catch (error) {
        setError("Error fetching task filter fields");
      }
    };

    fetchFields();
  }, []);

  const handleCriteriaChange = (newCriteria) => {
    setCriteria(newCriteria);
  };

  const handleGetQueryCount = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await getTaskQueryCount(criteria, []);
      if (response.success) {
        setQueryCount(response.data[0].count);
      } else {
        setError("Failed to get query count");
      }
    } catch (error) {
      setError("Error getting query count");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Box sx={{ overflow: "scroll", width: "100%", height: "100%", padding: "32px 32px 16px" }}>
      <Typography variant="h6" gutterBottom>
        Task Query Counter
      </Typography>
      <FilterContainer
        initialFilterContainer={criteria}
        onLogicChange={handleCriteriaChange}
        onValueChange={handleCriteriaChange}
        filterFields={taskFilterFields}
        filterOperatorMapping={FILTER_OPERATOR_MAPPING}
        hasNameField={false}
        hasDirectionField={false}
      />
      <Box mt={2}>
        <Button
          variant="contained"
          color="primary"
          onClick={handleGetQueryCount}
          disabled={isLoading}
        >
          {isLoading ? <CircularProgress size={24} /> : "Get Query Count"}
        </Button>
      </Box>
      {queryCount !== null && (
        <Typography mt={2}>Number of Tasks: {queryCount}</Typography>
      )}
      {error && (
        <Typography color="error" mt={2}>
          {error}
        </Typography>
      )}
    </Box >
  );
};

export default TaskQueryCounter;
