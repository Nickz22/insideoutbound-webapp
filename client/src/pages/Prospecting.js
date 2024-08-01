import React, {
  useState,
  useEffect,
  useRef,
  useCallback,
  useMemo,
} from "react";
import { useNavigate } from "react-router-dom";
import {
  Box,
  Alert,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  CircularProgress,
  IconButton,
  Tooltip,
  Link,
} from "@mui/material";
import RefreshIcon from "@mui/icons-material/Refresh";
import {
  fetchSalesforceUsers,
  fetchProspectingActivities,
  fetchAndUpdateProspectingActivity,
  generateActivationSummary,
  getInstanceUrl,
} from "src/components/Api/Api";
import MetricCard from "../components/MetricCard/MetricCard";
import CustomTable from "../components/CustomTable/CustomTable";

const Prospecting = () => {
  const [period, setPeriod] = useState("");
  const [view, setView] = useState("Summary");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [summaryData, setSummaryData] = useState(null);
  const [rawData, setRawData] = useState([]);
  const [activatedByUsers, setActivatedByUsers] = useState([]);
  const [filteredSummaryData, setFilteredSummaryData] = useState(null);
  const [selectedActivatedBy, setSelectedActivatedBy] = useState("");
  const [instanceUrl, setInstanceUrl] = useState("");
  const inFlightRef = useRef(false);
  const navigate = useNavigate();

  const fetchData = useCallback(
    async (isRefresh = false) => {
      if (inFlightRef.current) return;
      inFlightRef.current = true;
      setLoading(true);
      try {
        const response = isRefresh
          ? await fetchAndUpdateProspectingActivity()
          : await fetchProspectingActivities();

        switch (response.statusCode) {
          case 200:
            setSummaryData(response.data[0].summary);
            setFilteredSummaryData(response.data[0].summary);
            setRawData(response.data[0].raw_data || []);
            break;
          case 400:
          case 401:
            if (response.message.toLowerCase().includes("session expired")) {
              navigate("/");
            } else {
              setError(response.message);
            }
            break;
          default:
            setError(response.message);
            break;
        }
      } catch (err) {
        setError("An error occurred while fetching data.");
      } finally {
        setLoading(false);
        inFlightRef.current = false;
      }
    },
    [navigate]
  );

  useEffect(() => {
    const fetchInitialData = async () => {
      await fetchData();
      try {
        const response = await getInstanceUrl();
        if (response.success) {
          setInstanceUrl(response.data[0]);
        } else {
          console.error("Failed to fetch instance URL:", response.message);
        }
      } catch (error) {
        console.error("Error fetching instance URL:", error);
      }
    };

    fetchInitialData();
  }, [fetchData]);

  useEffect(() => {
    const fetchAndSetActivatedByUsers = async () => {
      if (summaryData && rawData.length > 0) {
        const activatedByIds = new Set(
          rawData.map((item) => item.activated_by_id)
        );
        const response = await fetchSalesforceUsers();
        if (response.success) {
          const filteredUsers = response.data.filter((user) =>
            activatedByIds.has(user.id)
          );
          setActivatedByUsers(filteredUsers);
        } else {
          setError("Failed to fetch Salesforce users.");
        }
      }
    };

    fetchAndSetActivatedByUsers();
  }, [summaryData, rawData]);

  const handleRefresh = () => {
    fetchData(true);
  };

  const handlePeriodChange = (event) => {
    setPeriod(event.target.value);
  };

  const handleViewChange = (event) => {
    setView(event.target.value);
  };

  const handleActivatedByChange = (event) => {
    setSelectedActivatedBy(event.target.value);
  };

  const filteredData = useMemo(() => {
    if (!selectedActivatedBy) return rawData;
    return rawData.filter(
      (item) => item.activated_by_id === selectedActivatedBy
    );
  }, [selectedActivatedBy, rawData]);

  useEffect(() => {
    const fetchFilteredSummaryData = async () => {
      if (selectedActivatedBy) {
        setLoading(true);
        const newSummary = (
          await generateActivationSummary(filteredData.map((item) => item.id))
        ).data[0].summary;
        setLoading(false);
        setFilteredSummaryData(newSummary);
      } else {
        setFilteredSummaryData(summaryData);
      }
    };

    if (summaryData && rawData.length > 0) {
      fetchFilteredSummaryData();
    }
  }, [selectedActivatedBy, filteredData, summaryData]);

  const tableColumns = [
    { id: "id", label: "ID", dataType: "text" },
    { id: "account.name", label: "Account Name", dataType: "component" },
    {
      id: "opportunity.name",
      label: "Opportunity Name",
      dataType: "component",
    },
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

  const renderSummaryView = () => (
    <Grid container spacing={2}>
      <Grid item xs={12} sm={6} md={4} lg={4}>
        <MetricCard
          title="Total Activations"
          value={filteredSummaryData.total_activations.toString()}
          subText=""
        />
      </Grid>
      <Grid item xs={12} sm={6} md={4} lg={4}>
        <MetricCard
          title="Activations Today"
          value={filteredSummaryData.activations_today.toString()}
          subText=""
        />
      </Grid>
      <Grid item xs={12} sm={6} md={4} lg={4}>
        <MetricCard
          title="Total Tasks"
          value={filteredSummaryData.total_tasks.toString()}
          subText=""
        />
      </Grid>
      <Grid item xs={12} sm={6} md={4} lg={4}>
        <MetricCard
          title="Total Events"
          value={filteredSummaryData.total_events.toString()}
          subText=""
        />
      </Grid>
      <Grid item xs={12} sm={6} md={4} lg={4}>
        <MetricCard
          title="Avg Tasks Per Contact"
          value={filteredSummaryData.avg_tasks_per_contact.toFixed(2)}
          subText=""
        />
      </Grid>
      <Grid item xs={12} sm={6} md={4} lg={4}>
        <MetricCard
          title="Avg Contacts Per Account"
          value={filteredSummaryData.avg_contacts_per_account.toFixed(2)}
          subText=""
        />
      </Grid>
      <Grid item xs={12} sm={6} md={4} lg={4}>
        <MetricCard
          title="Total Deals"
          value={filteredSummaryData.total_deals.toString()}
          subText=""
        />
      </Grid>
      <Grid item xs={12} sm={6} md={4} lg={4}>
        <MetricCard
          title="Total Pipeline Value"
          value={`$${filteredSummaryData.total_pipeline_value.toLocaleString()}`}
          subText=""
        />
      </Grid>
    </Grid>
  );

  const renderDetailedView = () => (
    <CustomTable
      tableData={{
        columns: tableColumns,
        data: filteredData.map((item) => ({
          ...item,
          "account.name": (
            <Link
              href={`${instanceUrl}/${item.account?.id}`}
              target="_blank"
              rel="noopener noreferrer"
            >
              {item.account?.name || "N/A"}
            </Link>
          ),
          "opportunity.name": item.opportunity ? (
            <Link
              href={`${instanceUrl}/${item.opportunity.id}`}
              target="_blank"
              rel="noopener noreferrer"
            >
              {item.opportunity.name || "N/A"}
            </Link>
          ) : (
            "N/A"
          ),
        })),
        selectedIds: new Set(),
        availableColumns: tableColumns,
      }}
      paginate={true}
    />
  );

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

  return (
    summaryData &&
    rawData && (
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
          <FormControl
            variant="outlined"
            sx={{ minWidth: 120, marginRight: "16px" }}
          >
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
          {activatedByUsers.length > 0 && (
            <FormControl
              variant="outlined"
              sx={{ minWidth: 120, marginRight: "16px" }}
            >
              <InputLabel id="activated-by-label">User</InputLabel>
              <Select
                labelId="activated-by-label"
                id="activated-by-select"
                value={selectedActivatedBy}
                onChange={handleActivatedByChange}
                label="Activated By"
              >
                <MenuItem value="">
                  <em>All</em>
                </MenuItem>
                {activatedByUsers.map((user) => (
                  <MenuItem key={user.id} value={user.id}>
                    {`${user.firstName} ${user.lastName}`}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          )}
          <Tooltip title="Refresh data from org">
            <IconButton onClick={handleRefresh} color="primary">
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Box>
        {view === "Summary" ? renderSummaryView() : renderDetailedView()}
      </Box>
    )
  );
};

export default Prospecting;
