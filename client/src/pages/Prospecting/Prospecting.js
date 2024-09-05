import React, {
  useState,
  useEffect,
  useRef,
  useCallback,
  useMemo,
} from "react";
import "./Prospecting.css";
import { useNavigate } from "react-router-dom";
import {
  Box,
  Alert,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Card,
  CardContent,
  LinearProgress,
  IconButton,
  Tooltip,
  Link,
  List,
  ListItem,
  ListItemText,
  Typography,
} from "@mui/material";
import {
  Timeline,
  TimelineItem,
  TimelineSeparator,
  TimelineConnector,
  TimelineContent,
  TimelineDot,
} from "@mui/lab";
import RefreshIcon from "@mui/icons-material/Refresh";
import DataFilter from "../../components/DataFilter/DataFilter";
import {
  fetchSalesforceUsers,
  fetchProspectingActivities,
  fetchAndUpdateProspectingActivity,
  getInstanceUrl,
  generateActivationSummary,
  getLoggedInUser,
} from "src/components/Api/Api";
import MetricCard from "../../components/MetricCard/MetricCard";
import CustomTable from "../../components/CustomTable/CustomTable";

/**
 * @typedef {import('types').Activation} Activation
 */

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
  const [originalRawData, setOriginalRawData] = useState([]);
  const [loggedInUser, setLoggedInUser] = useState({
    id: 0,
    created_at: "",
    firstName: "",
    lastName: "",
    email: "",
    username: "",
    photoUrl: "",
    status: ""
  });

  const freeTrialDaysLeft = useMemo(() => {
    if (loggedInUser.created_at.length === 0) {
      return 0; // No creation date, no trial left
    }

    const createdAtDate = new Date(loggedInUser.created_at); // Convert to Date object
    const currentDate = new Date(); // Current date

    // Set both dates to midnight (00:00:00) to ignore time
    createdAtDate.setHours(0, 0, 0, 0);
    currentDate.setHours(0, 0, 0, 0);

    // Calculate difference in milliseconds
    const timeDifference = currentDate.getTime() - createdAtDate.getTime();

    // Convert milliseconds to days
    const daysPassed = Math.floor(timeDifference / (1000 * 60 * 60 * 24));

    // Free trial is 3 days, so calculate days left
    const trialDaysLeft = 3 - daysPassed;

    // If days left is less than 0, return 0
    return trialDaysLeft > 0 && trialDaysLeft < 4 ? trialDaysLeft : 0;
  }, [loggedInUser])


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

  const handleClearFilter = useCallback(() => {
    setDataFilter(null);
    setRawData(originalRawData); // Reset to original data
  }, [originalRawData]);

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
            setOriginalRawData(response.data[0].raw_data || []);
            break;
          case 400:
          case 401:
            if (response.message.toLowerCase().includes("session")) {
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
        const [userResponse, instanceUrlResponse] = await Promise.all([
          getLoggedInUser(),
          getInstanceUrl(),
        ]);

        if (userResponse.success) {
          setLoggedInUser(userResponse.data[0]);
        }

        if (instanceUrlResponse.success) {
          setInstanceUrl(instanceUrlResponse.data[0]);
        } else {
          console.error("Failed to fetch instance URL:", instanceUrlResponse.message);
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

  const [selectedActivation, setSelectedActivation] = useState(null);

  const handleRowClick = (activation) => {
    setSelectedActivation(activation);
  };

  const ProspectingMetadataOverview = ({ metadata }) => (
    <Grid container spacing={2}>
      {metadata.map((item, index) => (
        <Grid item xs={12} key={index}>
          <Card variant="outlined">
            <CardContent>
              <Typography variant="h6" component="div" gutterBottom>
                {item.name}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total: {item.total}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                First: {new Date(item.first_occurrence).toLocaleDateString()}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Last: {new Date(item.last_occurrence).toLocaleDateString()}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      ))}
    </Grid>
  );

  const ProspectingEffortTimeline = ({ efforts }) => (
    <Timeline sx={{ padding: 0, margin: 0 }}>
      {efforts.map((effort, index) => (
        <TimelineItem key={index}>
          <TimelineSeparator>
            <TimelineDot color={getStatusColor(effort.status)} />
            {index < efforts.length - 1 && <TimelineConnector />}
          </TimelineSeparator>
          <TimelineContent>
            <Typography variant="h6" component="span">
              {effort.status}
            </Typography>
            <Typography>
              {new Date(effort.date_entered).toLocaleDateString()}
            </Typography>
            <Typography>Tasks: {effort.task_ids.length}</Typography>
            {effort.prospecting_metadata.length > 0 && (
              <List dense>
                {effort.prospecting_metadata.map((item, metaIndex) => (
                  <ListItem key={metaIndex}>
                    <ListItemText
                      primary={`${item.name}: ${item.total}`}
                      secondary={`${new Date(
                        item.first_occurrence
                      ).toLocaleDateString()} - ${new Date(
                        item.last_occurrence
                      ).toLocaleDateString()}`}
                    />
                  </ListItem>
                ))}
              </List>
            )}
          </TimelineContent>
        </TimelineItem>
      ))}
    </Timeline>
  );

  const getStatusColor = (status) => {
    switch (status) {
      case "Activated":
        return "primary";
      case "Meeting Set":
        return "secondary";
      case "Opportunity Created":
        return "success";
      default:
        return "grey";
    }
  };

  const filteredData = useMemo(() => {
    /** @type {Activation[]} */
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
    } else {
      filtered = rawData;
    }
    return filterDataByPeriod(filtered, period);
  }, [rawData, selectedActivatedBy, dataFilter, filterDataByPeriod, period]);

  const getLoadingComponent = (message) => {
    return (
      <Box
        sx={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          height: "100vh",
          width: "100%",
        }}
      >
        <Box sx={{ width: "100%", maxWidth: 400, textAlign: "center" }}>
          <Typography variant="h6" gutterBottom>
            {message}
          </Typography>
          <LinearProgress />
        </Box>
      </Box>
    );
  };

  const tableColumns = [
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
        engaged_activations: 0,
      });
    }
  }, [filteredData]);

  if (loading) {
    return getLoadingComponent("Looking for prospecting activities...");
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  return (
    <Box
      sx={{
        position: "relative",
        width: "100%",
        height: "100dvh",
        maxHeight: "100dvh",
        overflow: "hidden",
        backgroundColor: "#FFFFFF",
        maxWidth: "100%",
        boxSizing: "border-box",
        padding: 0,
        margin: 0,
      }}
    >
      <Box
        sx={{
          padding: "24px",
          overflowX: "auto",
          maxHeight: "100%",
          height: "100%",
          maxWidth: "100%",
          boxSizing: "border-box",
          backgroundColor: "#FFFFFF"
        }}
      >
        <Box
          sx={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: "16px",
          }}
        >
          <DataFilter
            fields={accountFields}
            onFilter={handleDataFilter}
            onClear={handleClearFilter}
          />
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
                <InputLabel id="activated-by-label">Activated By</InputLabel>
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
            <Tooltip
              title={loggedInUser.status === "not paid" && freeTrialDaysLeft === 0 ? "please upgrade to continue fetching your prospecting data" : "Refresh data from org"}>
              <IconButton
                onClick={() => {
                  if (loggedInUser.status === "not paid" && freeTrialDaysLeft === 0) {
                    return;
                  }
                  handleRefresh()
                }}
                color="primary"
                size="small"
              >
                <RefreshIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        {error ? (
          <Alert severity="error">{error}</Alert>
        ) : view === "Summary" ? (
          <Grid container spacing={2}>
            {summaryLoading ? (
              getLoadingComponent("Generating summary...")
            ) : (
              <>
                <Grid item xs={12} sm={6} md={4} lg={4}>
                  <MetricCard
                    title="Total Activations"
                    value={summaryData.total_activations.toString()}
                    subText=""
                    tooltipTitle="The number of approached accounts in the selected period"
                  />
                </Grid>
                <Grid item xs={12} sm={6} md={4} lg={4}>
                  <MetricCard
                    title="Activations Today"
                    value={summaryData.activations_today.toString()}
                    subText=""
                    tooltipTitle="The number of accounts which were approached today"
                  />
                </Grid>
                <Grid item xs={12} sm={6} md={4} lg={4}>
                  <MetricCard
                    title="Total Tasks"
                    value={summaryData.total_tasks.toString()}
                    subText=""
                    tooltipTitle="The total number of prospecting Tasks created in the selected period"
                  />
                </Grid>
                <Grid item xs={12} sm={6} md={4} lg={4}>
                  <MetricCard
                    title="Total Events"
                    value={summaryData.total_events.toString()}
                    subText=""
                    tooltipTitle="The total number of meetings created in the selected period"
                  />
                </Grid>
                <Grid item xs={12} sm={6} md={4} lg={4}>
                  <MetricCard
                    title="Avg Tasks Per Contact"
                    value={summaryData.avg_tasks_per_contact.toFixed(2)}
                    subText=""
                    tooltipTitle="The average number of tasks per contact under each activated account"
                  />
                </Grid>
                <Grid item xs={12} sm={6} md={4} lg={4}>
                  <MetricCard
                    title="Avg Contacts Per Account"
                    value={summaryData.avg_contacts_per_account.toFixed(2)}
                    subText=""
                    tooltipTitle="The average number of tasks per activated account"
                  />
                </Grid>
                <Grid item xs={12} sm={6} md={4} lg={4}>
                  <MetricCard
                    title="Total Deals"
                    value={summaryData.total_deals.toString()}
                    subText=""
                    tooltipTitle="The total number of open opportunities related to any activated account in the selected period"
                  />
                </Grid>
                <Grid item xs={12} sm={6} md={4} lg={4}>
                  <MetricCard
                    title="Total Pipeline Value"
                    value={`$${summaryData.total_pipeline_value.toLocaleString()}`}
                    subText=""
                    tooltipTitle="The total amount of open opportunities related to any activated account in the selected period"
                  />
                </Grid>
                <Grid item xs={12} sm={6} md={4} lg={4}>
                  <MetricCard
                    title="Engaged Activations"
                    value={summaryData.engaged_activations.toString()}
                    subText=""
                    tooltipTitle="The number of activated Accounts which have had inbound engagement"
                  />
                </Grid>
              </>
            )}
          </Grid>
        ) : (
          <>
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
              onRowClick={handleRowClick}
            />

            {selectedActivation && (
              <Box
                sx={{
                  marginTop: 4,
                  display: "flex",
                  height: "calc(100vh - 600px)",
                  minHeight: "400px",
                }}
              >
                <Box sx={{ width: "40%", overflowY: "auto", pr: 2 }}>
                  <Typography variant="h6" gutterBottom>
                    Prospecting Metadata for {selectedActivation.account.name}
                  </Typography>
                  <ProspectingMetadataOverview
                    metadata={selectedActivation.prospecting_metadata}
                  />
                </Box>
                <Box
                  sx={{
                    width: "60%",
                    overflowY: "auto",
                    pl: 2,
                    borderLeft: "1px solid #e0e0e0",
                  }}
                >
                  <ProspectingEffortTimeline
                    efforts={selectedActivation.prospecting_effort}
                  />
                </Box>
              </Box>
            )}
          </>
        )}


      </Box>

      {loggedInUser.status === "not paid" && freeTrialDaysLeft > 0 && (
        <Box
          onClick={() => {
            navigate("/app/account")
          }}
          sx={{
            position: "absolute",
            bottom: "60px",
            right: "-65px",
            transform: "rotate(-45deg)",
            backgroundColor: "#1E242F",
            color: "white",
            fontWeight: "bold",
            height: "56px",
            width: "320px",
            boxShadow: "0px 4px 6px rgba(0,0,0,0.1)",
            zIndex: 1,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            overflow: "hidden",
            cursor: "pointer"
          }}
        >
          {freeTrialDaysLeft} days left in trial
        </Box>
      )}
    </Box>
  );
};

export default Prospecting;
