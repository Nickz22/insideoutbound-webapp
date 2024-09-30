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
} from "src/components/Api/Api";
import CustomTable from "../../components/CustomTable/CustomTable";
import ProspectingMetadataOverview from "../../components/ProspectingMetadataOverview/ProspectingMetadataOverview";
import ProspectingEffortTimeline from "../../components/ProspectingEffortTimeline/ProspectingEffortTimeline";

import Lottie from "lottie-react";
import ProspectingLoadingAnimation from "../../assets/lottie/prospecting-loading-animation.json";
import HintsShowOnLoading from "src/components/HintsShowOnLoading/HintsShowOnLoading";
import CustomSelect from "src/components/CustomSelect/CustomSelect";
/**
 * @typedef {import('types').Activation} Activation
 */

import FreeTrialExpired from "../../components/FreeTrialExpired/FreeTrialExpired";
import ProspectingSummary from "./ProspectingSummary";

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
  const [period, setPeriod] = useState("This Week");
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
  const [columnShows, setColumnShows] = useState(tableColumns);

  const [loggedInUser, setLoggedInUser] = useState(null);
  const [userLoading, setUserLoading] = useState(true);
  const [userError, setUserError] = useState(null);

  const [instanceUrl, setInstanceUrl] = useState("");
  const [urlLoading, setUrlLoading] = useState(true);
  const [urlError, setUrlError] = useState(null);

  const [userTimezone, setUserTimezone] = useState("");

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
      } catch (err) {
        setUserError("An error occurred while fetching user data");
        setUrlError("An error occurred while fetching instance URL");
        console.error("An error occurred while fetching user timezone");
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
          response = await fetchProspectingActivities(
            selectedPeriod,
            filteredIds
          );
        } else {
          response = await fetchProspectingActivities(
            selectedPeriod,
            filteredIds
          );
        }

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
        setError("An error occurred while fetching data.");
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
  };

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
        <Box
          sx={{
            position: "relative",
            width: "100%",
            maxWidth: 852,
            textAlign: "center",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
          }}
        >
          <Typography
            variant="h6"
            gutterBottom
            sx={{
              fontWeight: "700",
              fontSize: "54px",
              letterSpacing: "-1.62px",
              lineHeight: "1",
            }}
          >
            {message}
          </Typography>
          <Box
            sx={{
              width: "271px",
              height: "271px",
              position: "relative",
              top: "-75px",
            }}
          >
            <Lottie animationData={ProspectingLoadingAnimation} loop={true} />
          </Box>

          <Typography
            variant="caption"
            gutterBottom
            sx={{
              marginTop: "-130px",
              marginBottom: "20px",
              width: "586px",
              fontSize: "18px",
              lineHeight: "1.78",
            }}
          >
            While the magic runs behind the scenes, here are some helpful hints
            to get the best use case from the app:
          </Typography>

          <HintsShowOnLoading />
        </Box>
      </Box>
    );
  };

  useEffect(() => {
    const fetchFilteredSummary = async () => {
      setSummaryLoading(true);
      try {
        const filteredIds = filteredData.map((item) => item.id);
        await fetchData(false, period, filteredIds);
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
  }, [dataFilter, period]);

  if (loading || summaryLoading || userLoading || urlLoading) {
    return getLoadingComponent("We are fetching your activity...");
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
          <Box sx={{ display: "flex", alignItems: "center", gap: "24px" }}>
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
                data: filteredData.map((item) => ({
                  ...item,
                  "account.owner.status": item.account?.owner?.status,
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
              onColumnsChange={handleColumnsChange}
            />

            {selectedActivation && (
              <Box sx={{ mt: 4 }}>
                <Box sx={{ mb: 4, overflowX: "auto", width: "100%" }}>
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
        <Box
          onClick={() => {
            navigate("/app/account");
          }}
          sx={{
            position: "absolute",
            bottom: "60px",
            right: "-75px",
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
            cursor: "pointer",
          }}
        >
          {freeTrialDaysLeft} days left in trial
        </Box>
      )}
    </Box>
  );
};

export default Prospecting;
