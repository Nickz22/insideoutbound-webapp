import { useEffect } from "react";
import {
  Box,
  CircularProgress,
  Snackbar,
  Tabs,
  Tab,
  AppBar,
  Typography,
} from "@mui/material";
import CheckCircleOutlineIcon from "@mui/icons-material/CheckCircleOutline";
import { useNavigate } from "react-router-dom";
import {
  fetchEventFilterFields,
  fetchTaskFilterFields,
  fetchSettings,
} from "../../components/Api/Api";
import TabGeneral from "./TabGeneral";
import TabProspecting from "./TabProspecting";
import TabMeeting from "./TabMeeting";
import TabUserRole from "./TabUserRole";
import { useSettings } from "./SettingProvider";
const Settings = () => {
  const navigate = useNavigate();
  const {
    status: { isLoading, saving, saveSuccess, setSaveSuccess, setIsLoading },
    handleTabChange,
    currentTab,
    filter: { setEventFilterFields, setTaskFilterFields },
    setSettings,
    setCriteria,
    fetchTeamMembersData,
  } = useSettings();

  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        setIsLoading(true);
        const [
          taskFilterFieldsResponse,
          eventFilterFieldsResponse,
          settingsResponse,
        ] = await Promise.all([
          fetchTaskFilterFields(),
          fetchEventFilterFields(),
          fetchSettings(),
        ]);

        /** @type {import('types').Settings} */
        const settings = settingsResponse.data[0];
        if (taskFilterFieldsResponse.statusCode === 200) {
          setTaskFilterFields(taskFilterFieldsResponse.data);
        } else if (
          taskFilterFieldsResponse.statusCode === 400 &&
          taskFilterFieldsResponse.data?.message
            .toLowerCase()
            .includes("session expired")
        ) {
          navigate("/");
          return;
        } else {
          console.error(taskFilterFieldsResponse.data.message);
        }

        setEventFilterFields(eventFilterFieldsResponse.data);

        // Set the default userRole based on teamMemberIds
        const teamMemberIds =
          settings.teamMemberIds?.length > 0 ? settings.teamMemberIds : [];
        const defaultUserRole =
          teamMemberIds.length > 0
            ? "I manage a team"
            : "I am an individual contributor";

        setSettings({
          ...settings,
          userRole: settings.userRole || defaultUserRole,
        });

        setCriteria(settings.criteria || []);

        if (teamMemberIds.length > 0) {
          if (fetchTeamMembersData) {
            await fetchTeamMembersData(teamMemberIds);
          }
        }
      } catch (error) {
        console.error("Error fetching initial data:", error);
        throw error; // Add this line to ensure the error is propagated
      } finally {
        setIsLoading(false);
      }
    };

    fetchInitialData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [navigate]);

  if (isLoading) {
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

  return (
    <Box sx={{ width: "100%", height: "100%" }}>
      <AppBar position="sticky" color="default" elevation={0}>
        <Tabs value={currentTab} onChange={handleTabChange} variant="fullWidth">
          <Tab label="General Settings" />
          <Tab label="Prospecting Activity" />
          <Tab label="Meeting Criteria" />
          <Tab label="User Role" />
        </Tabs>
      </AppBar>
      <Box
        sx={{
          overflow: "scroll",
          width: "100%",
          height: "100%",
          paddingBottom: "16px",
        }}
      >
        <TabGeneral />
        <TabProspecting />
        <TabMeeting />
        <TabUserRole />
      </Box>

      <Snackbar
        anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
        open={saving || saveSuccess}
        autoHideDuration={2000}
        onClose={() => setSaveSuccess(false)}
      >
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            bgcolor: "background.paper",
            borderRadius: 1,
            p: 1,
          }}
        >
          {saving ? (
            <CircularProgress size={24} sx={{ mr: 1 }} />
          ) : (
            <CheckCircleOutlineIcon color="success" sx={{ mr: 1 }} />
          )}
          <Typography>{saving ? "Saving..." : "Saved successfully"}</Typography>
        </Box>
      </Snackbar>
    </Box>
  );
};

export default Settings;
