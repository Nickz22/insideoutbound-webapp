import React, { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import {
  Box,
  Alert,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  CircularProgress,
} from "@mui/material";

import MetricCard from "../components/MetricCard/MetricCard";
import CustomTable from "../components/CustomTable/CustomTable";

const Prospecting = () => {
  const [period, setPeriod] = useState("");
  const [view, setView] = useState("Summary");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [summaryData, setSummaryData] = useState(null);
  const [rawData, setRawData] = useState([]);
  const inFlightRef = useRef(false);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchData = async () => {
      if (inFlightRef.current) return;
      inFlightRef.current = true;
      setLoading(true);
      try {
        const response = await axios.get(
          "http://localhost:8000/load_prospecting_activity",
          {
            validateStatus: function () {
              return true;
            },
          }
        );
        switch (response.status) {
          case 200:
            setSummaryData(response.data.data.summary);
            setRawData(response.data.data.raw_data || []);
            break;
          case 400:
            if (
              response.data?.message.toLowerCase().includes("session expired")
            ) {
              navigate("/");
            } else {
              setError(response.data.message);
            }
            break;
          default:
            setError(response.data.message);
            break;
        }
      } catch (err) {
        setError("An error occurred while fetching data.");
      } finally {
        setLoading(false);
        inFlightRef.current = false;
      }
    };

    fetchData();
  }, [navigate]);

  const handlePeriodChange = (event) => {
    setPeriod(event.target.value);
  };

  const handleViewChange = (event) => {
    setView(event.target.value);
  };

  if (loading) {
    return (
      <Box
        sx={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          height: "100vh",
        }}
      >
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  const tableColumns = [
    { id: "id", label: "ID", dataType: "text" },
    { id: "account.name", label: "Account Name", dataType: "text" },
    { id: "activated_date", label: "Activated Date", dataType: "date" },
    { id: "status", label: "Status", dataType: "text" },
    { id: "days_activated", label: "Days Activated", dataType: "number" },
    { id: "days_engaged", label: "Days Engaged", dataType: "number" },
    { id: "engaged_date", label: "Engaged Date", dataType: "date" },
    {
      id: "first_prospecting_activity",
      label: "First Prospecting Activity",
      dataType: "date",
    },
    {
      id: "last_prospecting_activity",
      label: "Last Prospecting Activity",
      dataType: "date",
    },
    {
      id: "last_outbound_engagement",
      label: "Last Outbound Engagement",
      dataType: "date",
    },
  ];

  const tableData = {
    columns: tableColumns,
    data: rawData.map((item) => ({
      ...item,
      "account.name": item.account?.name || "N/A",
    })),
    selectedIds: new Set(),
    availableColumns: tableColumns,
  };

  const renderSummaryView = () => (
    <Grid container spacing={2}>
      <Grid item xs={12} sm={6} md={4} lg={4}>
        <MetricCard
          title="Total Activations"
          value={summaryData.total_activations.toString()}
          subText=""
        />
      </Grid>
      <Grid item xs={12} sm={6} md={4} lg={4}>
        <MetricCard
          title="Activations Today"
          value={summaryData.activations_today.toString()}
          subText=""
        />
      </Grid>
      <Grid item xs={12} sm={6} md={4} lg={4}>
        <MetricCard
          title="Total Tasks"
          value={summaryData.total_tasks.toString()}
          subText=""
        />
      </Grid>
      <Grid item xs={12} sm={6} md={4} lg={4}>
        <MetricCard
          title="Total Events"
          value={summaryData.total_events.toString()}
          subText=""
        />
      </Grid>
      <Grid item xs={12} sm={6} md={4} lg={4}>
        <MetricCard
          title="Avg Tasks Per Contact"
          value={summaryData.avg_tasks_per_contact.toFixed(2)}
          subText=""
        />
      </Grid>
      <Grid item xs={12} sm={6} md={4} lg={4}>
        <MetricCard
          title="Avg Contacts Per Account"
          value={summaryData.avg_contacts_per_account.toFixed(2)}
          subText=""
        />
      </Grid>
      <Grid item xs={12} sm={6} md={4} lg={4}>
        <MetricCard
          title="Total Deals"
          value={summaryData.total_deals.toString()}
          subText=""
        />
      </Grid>
      <Grid item xs={12} sm={6} md={4} lg={4}>
        <MetricCard
          title="Total Pipeline Value"
          value={`$${summaryData.total_pipeline_value.toLocaleString()}`}
          subText=""
        />
      </Grid>
    </Grid>
  );

  const renderDetailedView = () => (
    <CustomTable
      tableData={tableData}
      paginate={true}
    />
  );

  return (
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
            <MenuItem value="Summary">Summary</MenuItem>
            <MenuItem value="Detailed">Detailed</MenuItem>
          </Select>
        </FormControl>
      </Box>
      {view === "Summary" ? renderSummaryView() : renderDetailedView()}
    </Box>
  );
};

export default Prospecting;
