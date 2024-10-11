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
  IconButton,
  Tooltip,
  Link,
  Typography,
  Switch,
  styled,
  Stack,
} from "@mui/material";
import RefreshIcon from "@mui/icons-material/Refresh";
import DataFilter from "../../components/DataFilter/DataFilter";
import { tableColumns } from "./tableColumns";
import {
  fetchProspectingActivities,
  getInstanceUrl,
  processNewProspectingActivity,
  getLoggedInUser,
  getUserTimezone,
  getPaginatedProspectingActivities,
} from "src/components/Api/Api";
import CustomTable from "../../components/CustomTable/CustomTable";
// import ProspectingMetadataOverview from "../../components/ProspectingMetadataOverview/ProspectingMetadataOverview";
// import ProspectingEffortTimeline from "../../components/ProspectingEffortTimeline/ProspectingEffortTimeline";
import CustomSelect from "src/components/CustomSelect/CustomSelect";
import CardActiveAccount from "../../components/ProspectingActiveAccount/CardActiveAccount";
/**
 * @typedef {import('types').Activation} Activation
 */
import SummaryBarChartCard from "src/components/SummaryCard/SummaryBarChartCard";
import FreeTrialExpired from "../../components/FreeTrialExpired/FreeTrialExpired";
import ProspectingSummary from "./ProspectingSummary";
import LoadingComponent from "../../components/LoadingComponent/LoadingComponent";
import FreeTrialRibbon from "../../components/FreeTrialRibbon/FreeTrialRibbon";
import { debounce } from "lodash"; // Make sure to import lodash or use a custom debounce function
import TimeLine from "src/components/ProspectingActiveAccount/TimeLine";

const AntSwitch = styled(Switch)(({ theme }) => ({
  width: 28,
  height: 16,
  padding: 0,
  display: "flex",
  "&:active": {
    "& .MuiSwitch-thumb": {
      width: 15,
    },
    "& .MuiSwitch-switchBase.Mui-checked": {
      transform: "translateX(9px)",
    },
  },
  "& .MuiSwitch-switchBase": {
    padding: 2,
    "&.Mui-checked": {
      transform: "translateX(12px)",
      color: "#fff",
      "& + .MuiSwitch-track": {
        opacity: 1,
        backgroundColor: "#1890ff",
        ...theme.applyStyles("dark", {
          backgroundColor: "#177ddc",
        }),
      },
    },
  },
  "& .MuiSwitch-thumb": {
    boxShadow: "0 2px 4px 0 rgb(0 35 11 / 20%)",
    width: 12,
    height: 12,
    borderRadius: 6,
    transition: theme.transitions.create(["width"], {
      duration: 200,
    }),
  },
  "& .MuiSwitch-track": {
    borderRadius: 16 / 2,
    opacity: 1,
    backgroundColor: "rgba(0,0,0,.25)",
    boxSizing: "border-box",
    ...theme.applyStyles("dark", {
      backgroundColor: "rgba(255,255,255,.35)",
    }),
  },
}));

const Prospecting = () => {
  /** @type {[('This Week' | 'All' | 'Last Week' | 'This Month' | 'Last Month' | 'This Quarter' | 'Last Quarter'), Function]} */
  const [period, setPeriod] = useState("All");
  const [isSummary, setIsSummary] = useState(true);
  const [loading, setLoading] = useState(true);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [error, setError] = useState(null);
  const [summaryData, setSummaryData] = useState(null);
  const [rawData, setRawData] = useState([]);
  const inFlightRef = useRef(false);
  const navigate = useNavigate();

  const [dataFilter, setDataFilter] = useState(null);
  const [originalRawData, setOriginalRawData] = useState([]);
  const [columnShows, setColumnShows] = useState(
    localStorage.getItem("activationColumnShow")
      ? JSON.parse(localStorage.getItem("activationColumnShow"))
      : tableColumns
  );

  const [loggedInUser, setLoggedInUser] = useState(null);
  const [userLoading, setUserLoading] = useState(true);
  const [userError, setUserError] = useState(null);

  const [instanceUrl, setInstanceUrl] = useState("");
  const [urlLoading, setUrlLoading] = useState(true);
  const [urlError, setUrlError] = useState(null);

  const [userTimezone, setUserTimezone] = useState("");

  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [totalItems, setTotalItems] = useState(0);
  const [detailedActivationData, setDetailedActivationData] = useState([]);
  const [tableLoading, setTableLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [sortColumn, setSortColumn] = useState("");
  /** @type {["asc" | "desc" | undefined, Function]} */
  const [sortOrder, setSortOrder] = useState("asc");

  useEffect(() => {
    async function fetchUserAndInstanceUrl() {
      try {
        if (loggedInUser && instanceUrl && userTimezone) {
          return;
        }
        const [userResponse, instanceUrlResponse, timezoneResponse] =
          await Promise.all([
            getLoggedInUser(),
            getInstanceUrl(),
            getUserTimezone(),
          ]);

        if (userResponse.success) {
          setLoggedInUser(userResponse.data[0]);
        } else {
          setUserError("Failed to fetch user data");
        }

        if (instanceUrlResponse.success) {
          setInstanceUrl(instanceUrlResponse.data[0]);
        } else {
          setUrlError("Failed to fetch instance URL");
        }

        if (timezoneResponse.success) {
          setUserTimezone(timezoneResponse.data);
        } else {
          console.error("Failed to fetch user timezone");
        }
      } catch (error) {
        setUserError("An error occurred while fetching user data");
        setUrlError("An error occurred while fetching instance URL");
        console.error("An error occurred while fetching user timezone");
        throw error; // Add this line to ensure the error is propagated
      } finally {
        setUserLoading(false);
        setUrlLoading(false);
      }
    }

    fetchUserAndInstanceUrl();
  }, []);

  const freeTrialDaysLeft = useMemo(() => {
    if (!loggedInUser) {
      return 0;
    }
    if (loggedInUser?.created_at?.length === 0) {
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
  }, [loggedInUser]);

  const handleDataFilter = useCallback((filters) => {
    setDataFilter(filters);
  }, []);

  const handleRefresh = () => {
    fetchData(true);
  };

  const fetchData = useCallback(
    /**
     *
     * @param {boolean} isRefresh
     * @param {'Today' | 'Yesterday' | 'This Week' | 'Last Week' | 'This Month' | 'Last Month' | 'This Quarter' | 'Last Quarter'} selectedPeriod
     * @param {string[]} filteredIds
     * @returns
     */
    async (isRefresh = false, selectedPeriod = period, filteredIds = []) => {
      if (inFlightRef.current) return;
      inFlightRef.current = true;
      setLoading(true);
      setSummaryLoading(true);
      try {
        let response;
        if (isRefresh) {
          await processNewProspectingActivity(userTimezone);
        }

        response = await fetchProspectingActivities(
          selectedPeriod,
          filteredIds
        );

        if (response.statusCode === 200 && response.success) {
          setSummaryData(response.data[0].summary);
          setRawData(response.data[0].raw_data || []);
          setOriginalRawData(response.data[0].raw_data || []);
        } else if (response.statusCode === 401) {
          navigate("/");
        } else {
          setError(response.message);
        }
      } catch (err) {
        setError(`An error occurred while fetching data: ${err.message}`);
        console.error("Error details:", err);
        throw err;
      } finally {
        setLoading(false);
        setSummaryLoading(false);
        inFlightRef.current = false;
      }
    },
    [navigate, period, userTimezone]
  );

  useEffect(() => {
    fetchData(false, period);
  }, [fetchData, period]);

  const filteredData = useMemo(() => {
    if (!dataFilter) return originalRawData;

    return originalRawData.filter((item) => {
      if (
        dataFilter.activatedBy.length > 0 &&
        !dataFilter.activatedBy.includes(item.activated_by_id)
      )
        return false;
      if (
        dataFilter.accountOwner.length > 0 &&
        !dataFilter.accountOwner.includes(item.account.owner.id)
      )
        return false;
      if (
        dataFilter.activatedByTeam.length > 0 &&
        !dataFilter.activatedByTeam.includes(item.activated_by.role)
      )
        return false;
      return true;
    });
  }, [originalRawData, dataFilter]);

  const fetchPaginatedData = useCallback(
    async (
      newPage,
      newRowsPerPage,
      newSearchTerm,
      newSortColumn,
      newSortOrder
    ) => {
      setTableLoading(true);
      try {
        const filteredIds = filteredData.map((item) => item.id);
        const response = await getPaginatedProspectingActivities(
          filteredIds,
          newPage,
          newRowsPerPage,
          newSearchTerm,
          newSortColumn,
          newSortOrder
        );
        if (response.statusCode === 200 && response.success) {
          setDetailedActivationData(response.data[0].raw_data || []);
          setTotalItems(response.data[0].total_items);
        } else if (response.statusCode === 401) {
          navigate("/");
        } else {
          setError(response.message);
        }
      } catch (err) {
        setError(`An error occurred while fetching data: ${err.message}`);
        console.error("Error details:", err);
        throw err;
      } finally {
        setTableLoading(false);
      }
    },
    [filteredData, navigate]
  );

  const debouncedFetchPaginatedData = useMemo(
    () => debounce(fetchPaginatedData, 250),
    [fetchPaginatedData]
  );

  useEffect(() => {
    return () => {
      debouncedFetchPaginatedData.cancel();
    };
  }, [debouncedFetchPaginatedData]);

  useEffect(() => {
    if (filteredData.length > 0) {
      debouncedFetchPaginatedData(
        page,
        rowsPerPage,
        searchTerm,
        sortColumn,
        sortOrder
      );
    }
  }, [
    debouncedFetchPaginatedData,
    page,
    rowsPerPage,
    filteredData,
    searchTerm,
    sortColumn,
    sortOrder,
  ]);

  const handlePageChange = (newPage, newRowsPerPage) => {
    setPage(newPage);
    setRowsPerPage(newRowsPerPage);
    // The debounced function will be called in the useEffect
  };

  const handleRowsPerPageChange = (newRowsPerPage) => {
    setRowsPerPage(newRowsPerPage);
    setPage(0);
    // The debounced function will be called in the useEffect
  };

  useEffect(() => {
    const filteredIds = filteredData.map((item) => item.id);
    fetchData(false, period, filteredIds);
  }, [dataFilter, period]);

  const handlePeriodChange = (event) => {
    const newPeriod = event.target.value;
    setPeriod(newPeriod);
  };

  const [selectedActivation, setSelectedActivation] = useState(null);

  const handleRowClick = (activation) => {
    setSelectedActivation(activation);
  };

  const handleColumnsChange = (newColumns) => {
    setColumnShows(newColumns);
    localStorage.setItem("activationColumnShow", JSON.stringify(newColumns));
  };

  useEffect(() => {
    const fetchFilteredSummary = async () => {
      setSummaryLoading(true);
      try {
        const filteredIds = filteredData.map((item) => item.id);
        await fetchData(false, period, filteredIds);
      } catch (err) {
        setError(`An error occurred while generating the summary. ${err}`);
        throw err;
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
  }, [dataFilter, period]);

  const handleSearch = (newSearchTerm) => {
    setSearchTerm(newSearchTerm);
    setPage(0); // Reset to first page when searching
    fetchPaginatedData(0, rowsPerPage, newSearchTerm, sortColumn, sortOrder);
  };

  const handleSort = (columnId, order) => {
    setSortColumn(columnId);
    setSortOrder(order);
    setPage(0); // Reset to first page when sorting
    fetchPaginatedData(0, rowsPerPage, searchTerm, columnId, order);
  };

  if (loading || summaryLoading || userLoading || urlLoading) {
    return <LoadingComponent message="We are fetching your activity..." />;
  }

  if (error || userError || urlError) {
    return <Alert severity="error">{error || userError || urlError}</Alert>;
  }

  if (loggedInUser?.status !== "paid" && freeTrialDaysLeft === 0) {
    return <FreeTrialExpired />;
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
          backgroundColor: "#FFFFFF",
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
          <DataFilter onFilter={handleDataFilter} rawData={rawData} />
          <Box
            sx={{
              display: "flex",
              alignItems: "center",
              gap: "24px",
            }}
          >
            <FormControl
              variant="outlined"
              size="small"
              sx={{ minWidth: "64px", marginTop: "-12px" }}
            >
              <CustomSelect
                value={period}
                label="Period"
                onChange={handlePeriodChange}
                placeholder="Select Field"
                selectSx={{
                  width: "100%",
                  fontSize: "16px",
                  lineHeight: "1.78",
                  letterSpacing: "-0.48px",
                  paddingBottom: "0px",
                }}
                labelSx={{
                  fontSize: "12px",
                  top: "13px",
                  left: "-14px",
                  "&.Mui-focused": {
                    top: "0px",
                  },
                }}
                options={[
                  "All",
                  "Today",
                  "Yesterday",
                  "This Week",
                  "Last Week",
                  "This Month",
                  "Last Month",
                  "This Quarter",
                  "Last Quarter",
                ]}
              />
            </FormControl>
            <FormControl
              variant="outlined"
              size="small"
              sx={{ minWidth: "93px", marginTop: "-12px" }}
            >
              <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
                <Typography>Detailed</Typography>
                <AntSwitch
                  checked={isSummary}
                  onChange={() => {
                    setIsSummary((prev) => !prev);
                  }}
                  inputProps={{ "aria-label": "ant design" }}
                />
                <Typography>Summary</Typography>
              </Stack>
            </FormControl>
            <Tooltip
              title={
                loggedInUser?.status === "not paid" && freeTrialDaysLeft === 0
                  ? "please upgrade to continue fetching your prospecting data"
                  : "Refresh data from org"
              }
            >
              <IconButton
                onClick={() => {
                  if (
                    loggedInUser?.status === "not paid" &&
                    freeTrialDaysLeft === 0
                  ) {
                    return;
                  }
                  handleRefresh();
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
        ) : isSummary && !summaryLoading ? (
          <ProspectingSummary period={period} summaryData={summaryData} />
        ) : (
          <>
            <CustomTable
              tableData={{
                columns: columnShows,
                data: detailedActivationData.map((item) => ({
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
              paginationConfig={{
                type: "server-side",
                totalItems: totalItems,
                page: page,
                rowsPerPage: rowsPerPage,
                onPageChange: handlePageChange,
                onRowsPerPageChange: handleRowsPerPageChange,
              }}
              sortConfig={{
                columnId: sortColumn,
                order: sortOrder,
                onSort: handleSort,
              }}
              onRowClick={handleRowClick}
              onColumnsChange={handleColumnsChange}
              isLoading={tableLoading}
              onSearch={handleSearch}
            />

            {selectedActivation && (
              <Box sx={{ mt: 4 }}>
                <Box
                  sx={{
                    mb: 4,
                    overflowX: "auto",
                    width: "100%",
                  }}
                >
                  <Box sx={{ minWidth: "600px" }}>
                    <ProspectingEffortTimeline
                      efforts={selectedActivation.prospecting_effort}
                    />
                  </Box>
                </Box>
                <ProspectingMetadataOverview
                  activation={selectedActivation}
                  instanceUrl={instanceUrl}
                />
              </Box>
            )}
          </>
        )}
      </Box>

      {loggedInUser?.status === "not paid" && freeTrialDaysLeft > 0 && (
        <FreeTrialRibbon daysLeft={freeTrialDaysLeft} />
      )}
    </Box>
  );
};

export default Prospecting;
