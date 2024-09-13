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
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  LinearProgress,
  IconButton,
  Tooltip,
  Link,
  Typography,
} from "@mui/material";
import RefreshIcon from "@mui/icons-material/Refresh";
import DataFilter from "../../components/DataFilter/DataFilter";
import { tableColumns } from "./tableColumns";
import {
  fetchProspectingActivities,
  fetchAndUpdateProspectingActivity,
  getInstanceUrl,
  generateActivationSummary,
} from "src/components/Api/Api";
import CustomTable from "../../components/CustomTable/CustomTable";
import ProspectingMetadataOverview from "../../components/ProspectingMetadataOverview/ProspectingMetadataOverview";
import ProspectingEffortTimeline from "../../components/ProspectingEffortTimeline/ProspectingEffortTimeline";
import ProspectingMetrics from "../../components/ProspectingMetrics/ProspectingMetrics";

/**
 * @typedef {import('types').Activation} Activation
 */

const Prospecting = () => {
  const [period, setPeriod] = useState("7d");
  const [view, setView] = useState("Summary");
  const [loading, setLoading] = useState(true);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [error, setError] = useState(null);
  const [summaryData, setSummaryData] = useState(null);
  const [rawData, setRawData] = useState([]);
  const [instanceUrl, setInstanceUrl] = useState("");
  const inFlightRef = useRef(false);
  const navigate = useNavigate();

  const [dataFilter, setDataFilter] = useState(null);
  const [originalRawData, setOriginalRawData] = useState([]);

  const handleDataFilter = useCallback((filters) => {
    setDataFilter(filters);
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

  const handleRefresh = () => {
    fetchData(true);
  };

  const handlePeriodChange = (event) => {
    setPeriod(event.target.value);
  };

  const handleViewChange = (event) => {
    setView(event.target.value);
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

  const filteredData = useMemo(() => {
    let filtered = originalRawData;
    if (dataFilter) {
      filtered = filtered.filter((item) => {
        if (
          dataFilter.industry.length > 0 &&
          !dataFilter.industry.includes(item.account.industry)
        )
          return false;
        if (
          item.account.annual_revenue < dataFilter.annualRevenue[0] ||
          item.account.annual_revenue > dataFilter.annualRevenue[1]
        )
          return false;
        if (
          dataFilter.activatedBy &&
          item.activated_by_id !== dataFilter.activatedBy
        )
          return false;
        if (
          item.account.number_of_employees < dataFilter.employeeCount[0] ||
          item.account.number_of_employees > dataFilter.employeeCount[1]
        )
          return false;
        const createdDate = new Date(item.account.created_date);
        if (
          dataFilter.createdDate.start &&
          createdDate < new Date(dataFilter.createdDate.start)
        )
          return false;
        if (
          dataFilter.createdDate.end &&
          createdDate > new Date(dataFilter.createdDate.end)
        )
          return false;
        return true;
      });
    }
    return filterDataByPeriod(filtered, period);
  }, [originalRawData, dataFilter, filterDataByPeriod, period]);

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
    <Box sx={{ padding: "24px" }}>
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "16px",
        }}
      >
        <DataFilter onFilter={handleDataFilter} rawData={rawData} />
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
              <MenuItem value="24h">Last 24 hours</MenuItem>
              <MenuItem value="48h">Last 48 hours</MenuItem>
              <MenuItem value="7d">Last 7 days</MenuItem>
              <MenuItem value="30d">Last 30 days</MenuItem>
              <MenuItem value="90d">Last 90 days</MenuItem>
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
          <Tooltip title="Refresh data from org">
            <IconButton onClick={handleRefresh} color="primary" size="small">
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {error ? (
        <Alert severity="error">{error}</Alert>
      ) : view === "Summary" ? (
        <ProspectingMetrics
          summaryData={summaryData}
          summaryLoading={summaryLoading}
          getLoadingComponent={getLoadingComponent}
        />
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
  );
};

export default Prospecting;
