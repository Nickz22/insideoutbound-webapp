import React, { useState, useEffect } from "react";
import axios from "axios";
import {
  Box,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from "@mui/material";
import MetricCard from "../components/MetricCard/MetricCard";
import DiagramCard from "../components/DiagramCard/DiagramCard";
import ConversionRatesChart from "../components/ConversionRatesChart/ConversionRatesChart";
import FunnelChart from "../components/FunnelChart/FunnelChart";

const Prospecting = () => {
  const [period, setPeriod] = useState("");
  const [view, setView] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [inFlight, setInFlight] = useState(false); // State to track if a request is in flight

  useEffect(() => {
    const fetchData = async () => {
      if (inFlight) return; // Prevent new request if one is already in flight
      setInFlight(true); // Set request as in-flight
      setLoading(true);
      try {
        await axios.get("http://localhost:8000/load_prospecting_activities");
      } catch (err) {
        setError(err);
      } finally {
        setLoading(false);
        setInFlight(false); // Reset in-flight state after request completes
      }
    };

    fetchData();
  }, []);

  const handlePeriodChange = (event) => {
    setPeriod(event.target.value);
  };

  const handleViewChange = (event) => {
    setView(event.target.value);
  };

  return loading ? (
    <p>Loading...</p>
  ) : (
    <Box sx={{ padding: "24px" }}>
      <Box
        sx={{
          display: "flex",
          justifyContent: "flex-end",
          marginBottom: "16px",
        }}
      >
        <FormControl
          variant="outlined"
          sx={{ minWidth: 120, marginRight: "16px" }}
        >
          <InputLabel id="period-label">Period</InputLabel>
          <Select
            labelId="period-label"
            id="period-select"
            value={period}
            onChange={handlePeriodChange}
            label="Period"
          >
            <MenuItem value="">
              <em>None</em>
            </MenuItem>
            <MenuItem value="Q1">Q1</MenuItem>
            <MenuItem value="Q2">Q2</MenuItem>
            <MenuItem value="Q3">Q3</MenuItem>
            <MenuItem value="Q4">Q4</MenuItem>
          </Select>
        </FormControl>
        <FormControl variant="outlined" sx={{ minWidth: 120 }}>
          <InputLabel id="view-label">View</InputLabel>
          <Select
            labelId="view-label"
            id="view-select"
            value={view}
            onChange={handleViewChange}
            label="View"
          >
            <MenuItem value="">
              <em>None</em>
            </MenuItem>
            <MenuItem value="Summary">Summary</MenuItem>
            <MenuItem value="Detailed">Detailed</MenuItem>
          </Select>
        </FormControl>
      </Box>
      <Grid container spacing={2}>
        <Grid item xs={12} sm={6} md={4} lg={4}>
          <MetricCard title="Accounts Approached" value="86" subText="" />
        </Grid>
        <Grid item xs={12} sm={6} md={4} lg={4}>
          <MetricCard title="Opportunities Created" value="7" subText="" />
        </Grid>
        <Grid item xs={12} sm={6} md={4} lg={4}>
          <MetricCard title="Pipeline Generated" value="$210,000" subText="" />
        </Grid>
        <Grid item xs={12} sm={6} md={4} lg={4}>
          <MetricCard title="Avg Contacts Per Account" value="4.8" subText="" />
        </Grid>
        <Grid item xs={12} sm={6} md={4} lg={4}>
          <MetricCard
            title="Avg Activities Per Contact"
            value="7.3"
            subText=""
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4} lg={4}>
          <MetricCard
            title="Prospecting Cycle Time"
            value="11.6 Days"
            subText=""
          />
        </Grid>
        <Grid item xs={12} sm={6} md={6} lg={6}>
          <DiagramCard title="Conversion Rates">
            <ConversionRatesChart />
          </DiagramCard>
        </Grid>
        <Grid item xs={12} sm={6} md={6} lg={6}>
          <DiagramCard title="Prospecting Funnel">
            <FunnelChart />
          </DiagramCard>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Prospecting;
