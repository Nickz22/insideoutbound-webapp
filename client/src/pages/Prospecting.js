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
  Paper,
} from "@mui/material";
import RefreshIcon from "@mui/icons-material/Refresh";
import DataFilter from "./../components/DataFilter/DataFilter";
import {
  fetchSalesforceUsers,
  fetchProspectingActivities,
  fetchAndUpdateProspectingActivity,
  getInstanceUrl,
  generateActivationSummary,
} from "src/components/Api/Api";
import MetricCard from "../components/MetricCard/MetricCard";
import CustomTable from "../components/CustomTable/CustomTable";

const Prospecting = () => {
  const [period, setPeriod] = useState("All");
  const [view, setView] = useState("Summary");
  const [loading, setLoading] = useState(true);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [error, setError] = useState(null);
  const [summaryData, setSummaryData] = useState(null);
  const [rawData, setRawData] = useState([]);
  const [activatedByUsers, setActivatedByUsers] = useState([]);
  const [selectedActivatedBy, setSelectedActivatedBy] = useState("");
  const [instanceUrl, setInstanceUrl] = useState("");
  const inFlightRef = useRef(false);
  const navigate = useNavigate();

  const [dataFilter, setDataFilter] = useState(null);

  const accountFields = useMemo(() => {
    if (rawData.length === 0) return [];
    const firstAccount = rawData[0].account;
    return Object.keys(firstAccount).filter(
      (key) => typeof firstAccount[key] !== "object"
    );
  }, [rawData]);

  const handleDataFilter = useCallback((filter) => {
    setDataFilter(filter);
  }, []);

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

  const filterDataByPeriod = useCallback((data, selectedPeriod) => {
    if (selectedPeriod === "All") return data;

    const now = new Date();
    const periodInHours = {
      "24h": 24,
      "48h": 48,
      "7d": 24 * 7,
      "30d": 24 * 30,
      "90d": 24 * 90,
    }[selectedPeriod];

    return data.filter((item) => {
      const lastProspectingActivity = new Date(item.last_prospecting_activity);
      const hoursDifference =
        (now - lastProspectingActivity) / (1000 * 60 * 60);
      return hoursDifference < periodInHours; // Changed <= to
    });
  }, []);

  const filteredData = useMemo(() => {
    let filtered = rawData;
    if (selectedActivatedBy) {
      filtered = filtered.filter(
        (item) => item.activated_by_id === selectedActivatedBy
      );
    }
    if (dataFilter) {
      filtered = filtered.filter((item) => {
        const accountValue = item.account[dataFilter.field];
        if (dataFilter.operator === "equals") {
          return accountValue === dataFilter.value;
        } else if (dataFilter.operator === "notEquals") {
          return accountValue !== dataFilter.value;
        }
        return true;
      });
    }
    return filterDataByPeriod(filtered, period);
  }, [rawData, selectedActivatedBy, dataFilter, filterDataByPeriod, period]);

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

  useEffect(() => {
    const fetchFilteredSummary = async () => {
      setSummaryLoading(true);
      try {
        const filteredIds = filteredData.map((item) => item.id);
        const response = await generateActivationSummary(filteredIds);
        if (response.success) {
          setSummaryData(response.data[0].summary);
        } else {
          setError(
            `Failed to generate activation summary. ${response.message}`
          );
        }
      } catch (err) {
        setError(`An error occurred while generating the summary. ${err}`);
      } finally {
        setSummaryLoading(false);
      }
    };

    if (filteredData.length > 0) {
      fetchFilteredSummary();
    } else {
      setSummaryData({
        total_activations: 0,
        activations_today: 0,
        avg_tasks_per_contact: 0,
        avg_contacts_per_account: 0,
        total_tasks: 0,
        total_events: 0,
        total_contacts: 0,
        total_accounts: 0,
        total_deals: 0,
        total_pipeline_value: 0,
      });
    }
  }, [filteredData]);

  const renderSummaryView = () => (
    <Grid container spacing={2}>
      {summaryLoading ? (
        <Box
          sx={{
            display: "flex",
            justifyContent: "center",
            width: "100%",
            mt: 4,
          }}
        >
          <CircularProgress />
        </Box>
      ) : (
        <>
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
        </>
      )}
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
    <Box sx={{ padding: "24px" }}>
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "16px",
        }}
      >
        <DataFilter fields={accountFields} onFilter={handleDataFilter} />
        <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
          <FormControl variant="outlined" size="small" sx={{ minWidth: 120 }}>
            <InputLabel id="period-label">Period</InputLabel>
            <Select
              labelId="period-label"
              id="period-select"
              value={period}
              onChange={handlePeriodChange}
              label="Period"
            >
              <MenuItem value="All">All</MenuItem>
              <MenuItem value="24h">24h</MenuItem>
              <MenuItem value="48h">48h</MenuItem>
              <MenuItem value="7d">7d</MenuItem>
              <MenuItem value="30d">30d</MenuItem>
              <MenuItem value="90d">90d</MenuItem>
            </Select>
          </FormControl>
          <FormControl variant="outlined" size="small" sx={{ minWidth: 120 }}>
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
            <FormControl variant="outlined" size="small" sx={{ minWidth: 120 }}>
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
            <IconButton onClick={handleRefresh} color="primary" size="small">
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {loading ? (
        <Box
          sx={{
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            height: "50vh",
          }}
        >
          <CircularProgress />
        </Box>
      ) : error ? (
        <Alert severity="error">{error}</Alert>
      ) : (
        <>
          {view === "Summary" ? (
            <Grid container spacing={2}>
              {summaryLoading ? (
                <Box
                  sx={{
                    display: "flex",
                    justifyContent: "center",
                    width: "100%",
                    mt: 4,
                  }}
                >
                  <CircularProgress />
                </Box>
              ) : (
                <>
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
                </>
              )}
            </Grid>
          ) : (
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
          )}
        </>
      )}
    </Box>
  );
};

export default Prospecting;
