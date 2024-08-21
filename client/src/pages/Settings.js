import React, { useState, useEffect, useCallback, useMemo } from "react";
import { 
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Switch,
  FormControlLabel,
  Button,
  Grid,
  CircularProgress,
  Snackbar,
  Select,
  MenuItem,
  IconButton,
  Tooltip,
  Tabs,
  Tab,
  AppBar,
} from "@mui/material";
import CheckCircleOutlineIcon from "@mui/icons-material/CheckCircleOutline";
import CloseIcon from "@mui/icons-material/Close";
import { useNavigate } from "react-router-dom";
import {
  deleteAllActivations,
  fetchEventFilterFields,
  fetchTaskFilterFields,
  fetchSalesforceUsers,
  fetchSettings,
  saveSettings,
} from "../components/Api/Api";
import { FILTER_OPERATOR_MAPPING } from "../utils/c";
import FilterContainer from "../components/FilterContainer/FilterContainer";
import CustomTable from "../components/CustomTable/CustomTable";
import { debounce } from "lodash";

const Settings = () => {

  const navigate = useNavigate();
  const [settings, setSettings] = useState({
    inactivityThreshold: 0,
    criteria: [],
    meetingObject: "",
    meetingsCriteria: { filters: [], filterLogic: "", name: "" },
    activitiesPerContact: 0,
    contactsPerAccount: 0,
    trackingPeriod: 0,
    activateByMeeting: false,
    activateByOpportunity: false,
    userRole: "",
    teamMemberIds: [],
    latestDateQueried: null,
  });

  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [taskFilterFields, setTaskFilterFields] = useState();
  const [eventFilterFields, setEventFilterFields] = useState();
  const [isLoading, setIsLoading] = useState(true);
  const [criteria, setCriteria] = useState([]);
  const [tableData, setTableData] = useState(null);
  const [isTableLoading, setIsTableLoading] = useState(false);
  const [currentTab, setCurrentTab] = useState(0);

  /* Constants - can be moved to a separate file*/
  const LABELS = {
    GENERAL_SETTINGS: 'General Settings',
    PROSPECTING_ACTIVITY: 'Prospecting Activity',
    MEETING_CRITERIA: 'Meeting Criteria',
    USER_ROLE: 'User Role',
    INACTIVITY_THRESHOLD: 'Inactivity Threshold (days)',
    ACTIVITIES_PER_CONTACT: 'Activities per Contact',
    CONTACTS_PER_ACCOUNT: 'Contacts per Account',
    TRACKING_PERIOD: "Tracking Period (days)",
    QUERY_ACTIVITIES_CREATED_AFTER: 'Query activities created after',
    ACTIVATE_BY_OPPORTUNITY: 'Activate by Opportunity',
    ACTIVATE_BY_MEETING: 'Activate by Meeting',
    SAVE_SUCCESS: 'Saved successfully',
    SAVE_PROGRESS: "Saving..."
  };
  
  const TITLES = {
    INACTIVITY_THRESHOLD: 'Number of days without a new Task, Event or Opportunity before an approach is considered inactive.',
    ACTIVITIES_PER_CONTACT: 'Number of prospecting activities per Contact required for an Account to be activated.',
    CONTACTS_PER_ACCOUNT: 'Number of activated Contacts required before considering an Account as being actively prospected.',
    TRACKING_PERIOD: 'Number of days within which prospecting activities should be created to be attributed to an approach. If the first prospecting activity was created on 1/1/2024 and the tracking period is 5 days, then any other prospecting activity, event or opportunity included under the same approach needs to be created by 1/6/2024.',
    QUERY_ACTIVITIES_CREATED_AFTER: "We'll query activities created on or after this time to calculate your prospecting activity.",
    ACTIVATE_BY_OPPORTUNITY: "Consider an Account as 'approached' when an Opportunity is created after a prospecting activity was already created under the same Account.",
    ACTIVATE_BY_MEETING: "Consider an Account as 'approached' when a Meeting is created after a prospecting activity was already created under the same Account.",
  };
  
  const columns = [
    { id: "select", label: "Select", dataType: "select" },
    { id: "photoUrl", label: "", dataType: "image" },
    { id: "firstName", label: "First Name", dataType: "string" },
    { id: "lastName", label: "Last Name", dataType: "string" },
    { id: "email", label: "Email", dataType: "string" },
    { id: "role", label: "Role", dataType: "string" },
    { id: "username", label: "Username", dataType: "string" },
  ];

  const TEAM_MANAGER = "I manage a team"
  const INDIVIDUAL_CONTRIBUTER = "I am an individual contributor"
  const TABS = ["general", "prospecting", "meeting", "user-role"] 


  useEffect(() => {

    const fetchTaskFilterFieldsData = async () => {
      try {
        setIsLoading(true); 
        const response = await fetchTaskFilterFields();
        handleTaskFilterResponse(response);
      } catch (error) {
      console.error("Error fetching task filter fields:" , error);
      } finally {
        setIsLoading(false);
      }
    };
  
    fetchTaskFilterFieldsData();
  }, []);

  useEffect(() => {
    const fetchEventFilterFieldsData = async () => {
      try {
        setIsLoading(true);
        const response = await fetchEventFilterFields();
        setEventFilterFields( response.data);
      } 
      catch (error) {
        console.error("error fetching event filter fields: ", error);
      } finally {
        setIsLoading(false);
      }
    };
  
    fetchEventFilterFieldsData();
  }, []);

  useEffect(() => {
    const fetchSettingsData = async () => {
      try {

        setIsLoading(true);
        const response = await fetchSettings();
        await handleSettingsResponse(response.data[0]);
      } catch (error) {

        console.error("Error fetching settings data: " , error);
      } finally {
        setIsLoading(false);
      }
    };
    fetchSettingsData();
  }, [navigate]);
  
  const handleTaskFilterResponse = (response) => {
    if (response.statusCode === 200) {
      setTaskFilterFields(response.data);
    } else if (
      response.statusCode === 400 &&
      response.data?.message.toLowerCase().includes("session expired")
    ) {
      navigate("/");
    } else {
      console.error(response.data.message);
    }
  };
  
  const handleSettingsResponse = async (settings) => {
    const teamMemberIds = settings.teamMemberIds || [];
    const defaultUserRole =
      teamMemberIds.length > 0 ? TEAM_MANAGER : INDIVIDUAL_CONTRIBUTER;
  
    setSettings({
      ...settings,
      userRole: settings.userRole || defaultUserRole,
    });
  
    setCriteria(settings.criteria || []);
  
    if (teamMemberIds.length > 0) {
      await fetchTeamMembersData(teamMemberIds);
    }
  };  

  const handleTabChange = (/** @type {any} */ event, /** @type {string | React.SetStateAction<number>} */ newValue) => {
    setCurrentTab(newValue);
    // Scroll to the corresponding section
    const sectionId = TABS[newValue];
    const element = document.getElementById(sectionId);
    if (element) {
      element.scrollIntoView({ behavior: "smooth" });
    }
  };

  const fetchTeamMembersData = async (selectedIds = []) => {
    setIsTableLoading(true);
    try {
      const response = await fetchSalesforceUsers();
      if (response.success) {
        setTableData({
          columns,
          data: response.data,
          selectedIds: new Set(selectedIds),
          availableColumns: columns,
        });
      } else {
        console.error("Error fetching Salesforce users:", response.message);
      }
    } catch (error) {
      console.error("Error fetching Salesforce users:", error);
    } finally {
      setIsTableLoading(false);
    }
  };

  const debouncedSaveSettings = useMemo(
    () =>
      debounce(async (/** @type {{ [x: string]: any; userRole: any; }} */ settings) => {
        const { userRole, ...settingsToSave } = settings;
        setSaving(true);
        try {
          saveSettings(settingsToSave);
          setSaveSuccess(true);
        } catch (error) {
          console.error("Error saving settings:", error);
        } finally {
          setSaving(false);
        }
      }, 500),
    []
  );

  /* Divided the handleChange function to enforce single responsibility for each function */
  const handleChange = useCallback(
    (/** @type {any} */ field, /** @type {string} */ value) => {
      setSettings((/** @type {any} */ prev) => {
        const updatedSettings = { ...prev, [field]: value };
        debouncedSaveSettings(updatedSettings);
        return updatedSettings;
      });
    },
    [debouncedSaveSettings]
  );

  const handleUserRoleChange = useCallback(
    (/** @type {string} */ value) => {
      setSettings((/** @type {{ teamMemberIds: any[] | undefined; }} */ prev) => {
        const updatedSettings = { ...prev, userRole: value };
  
        if (value === TEAM_MANAGER) {
          fetchTeamMembersData(prev.teamMemberIds);
        } else {
          setTableData(null);
          updatedSettings.teamMemberIds = [];
        }
  
        debouncedSaveSettings(updatedSettings);
        return updatedSettings;
      });
    },
    [debouncedSaveSettings]
  );
  
  const handleMeetingObjectChange = useCallback(
    (value) => {
      setSettings((/** @type {{ meetingObject: string; }} */ prev) => {
        const updatedSettings = { ...prev, meetingObject: value };
  
        if (value !== prev.meetingObject) {
          updatedSettings.meetingsCriteria = {
            filters: [],
            filterLogic: "",
            name: "",
          };
        }
  
        debouncedSaveSettings(updatedSettings);
        return updatedSettings;
      });
    },
    [debouncedSaveSettings]
  );
  
  const handleLatestDateQueriedChange = useCallback(
    (/** @type {string} */ value) => {
      setSettings((/** @type {any} */ prev) => {
        const updatedSettings = { ...prev, latestDateQueried: value };
        deleteAllActivations();
        debouncedSaveSettings(updatedSettings);
        return updatedSettings;
      });
    },
    [debouncedSaveSettings]
  );
  
  const handleDeleteFilter = useCallback(
    (/** @type {number} */ index) => {
      setCriteria((/** @type {any[]} */ prevCriteria) => {
        const newCriteria = prevCriteria.filter((/** @type {any} */ _, /** @type {number} */ i) => i !== index);
        setSettings((/** @type {any} */ prev) => {
          const updatedSettings = { ...prev, criteria: newCriteria };
          debouncedSaveSettings(updatedSettings);
          return updatedSettings;
        });
        return newCriteria;
      });
    },
    [debouncedSaveSettings]
  );

  const handleAddCriteria = useCallback(() => {
    setCriteria((/** @type {any} */ prevCriteria) => {
      const newCriteria = [
        ...prevCriteria,
        { filters: [], filterLogic: "", name: "" },
      ];
      setSettings((/** @type {any} */ prev) => {
        const updatedSettings = { ...prev, criteria: newCriteria };
        debouncedSaveSettings(updatedSettings);
        return updatedSettings;
      });
      return newCriteria;
    });
  }, [debouncedSaveSettings]);

  const handleCriteriaChange = useCallback(
    (/** @type {string | number} */ index, /** @type {any} */ newContainer) => {
      setSettings((/** @type {{ criteria: any; }} */ prev) => {
        const newCriteria = [...prev.criteria];
        newCriteria[index] = newContainer;
        const updatedSettings = { ...prev, criteria: newCriteria };
        debouncedSaveSettings(updatedSettings);
        return updatedSettings;
      });
    },
    [debouncedSaveSettings]
  );

  const handleTableSelectionChange = useCallback( (/** @type {Iterable<any> | ArrayLike<any>} */ selectedIds) => {
      const teamMemberIds = Array.from(selectedIds);
      setSettings((/** @type {any} */ prev) => {
        const newSettings = {
          ...prev,
          teamMemberIds,
          userRole: teamMemberIds.length > 0 ? TEAM_MANAGER : INDIVIDUAL_CONTRIBUTER,
        };
        debouncedSaveSettings(newSettings);
        return newSettings;
      });
  
      setTableData((/** @type {any} */ prev) => ({
        ...prev,
        selectedIds,
      }));
    },
    [debouncedSaveSettings]
  );

  const handleColumnsChange = useCallback((/** @type {any} */ newColumns) => {
    setTableData((/** @type {any} */ prev) => ({
      ...prev,
      columns: newColumns,
    }));
  }, []);

  
  /* Util functions */
  const formatDateForInput = (/** @type {string | number | Date} */ date) => {
    if (!date) return "";
    const d = new Date(date);
    if (isNaN(d.getTime())) return "";

    return d.toISOString().slice(0, 16); /* Date obj's ISO string returns the same format of string*/
  };
  

  /* 
  Render functions - Can be made into different components
  This will help in reusability and readability of the code overall   
  */ 
  const renderTeamMembers = () => (
    <Box sx={{ mt: 2 }}>
      <Typography variant="subtitle1" gutterBottom>
        Select Team Members
      </Typography>
      {isTableLoading ? (
        <CircularProgress />
      ) : (
        tableData && (
          <CustomTable
            tableData={tableData}
            onSelectionChange={handleTableSelectionChange}
            onColumnsChange={handleColumnsChange}
            paginate={true}
          />
        )
      )}
    </Box>
  );

  const renderUserRoleAndTeamMembers = () => (
    <Card id="user-role" sx={{ mb: 2 }}>
      <CardContent sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom marginBottom={2}>
          User Role and Team Members
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <Select
              fullWidth
              value={settings.userRole}
              onChange={e => handleUserRoleChange("userRole", e.target.value)}
              label="User Role"
            >
              <MenuItem value={TEAM_MANAGER}>I manage a team</MenuItem>
              <MenuItem value={INDIVIDUAL_CONTRIBUTER}>I am an individual contributor</MenuItem>
            </Select>
          </Grid>
        </Grid>
        {settings.userRole === TEAM_MANAGER && renderTeamMembers()}
      </CardContent>
    </Card>
  );

  const renderMeetingCriteria = () => (
    <Card id="meeting">
      <CardContent sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>
          Meeting Criteria
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <Select
              fullWidth
              value={settings.meetingObject}
              onChange={e => handleMeetingObjectChange("meetingObject", e.target.value)}
              label="Meeting Object"
            >
              <MenuItem value="Task">Task</MenuItem>
              <MenuItem value="Event">Event</MenuItem>
            </Select>
          </Grid>
        </Grid>
        <Box sx={{ mt: 2 }}>
          <FilterContainer 
            initialFilterContainer={settings.meetingsCriteria}
            onLogicChange={newContainer => handleMeetingObjectChange("meetingsCriteria", newContainer)}
            onValueChange={newContainer => handleMeetingObjectChange("meetingsCriteria", newContainer)}
            filterFields={settings.meetingObject === "Event" ? eventFilterFields : taskFilterFields}
            filterOperatorMapping={FILTER_OPERATOR_MAPPING}
            hasDirectionField={false}
          />
        </Box>
      </CardContent>
    </Card>
  );

  const renderProspectingActivityCriteria = () => (
    <Card id="prospecting" sx={{ mb: 2 }}>
      <CardContent sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>
          Prospecting Activity Criteria
        </Typography>
        <Grid container spacing={2}>
          {criteria.map((criteriaContainer, index) => (
            <Grid item xs={12} md={6} key={index}>
              <Box sx={{ position: "relative" }}>
                <FilterContainer 
                  initialFilterContainer={criteriaContainer}
                  onLogicChange={newContainer => handleCriteriaChange(index, newContainer)}
                  onValueChange={newContainer => handleCriteriaChange(index, newContainer)}
                  filterFields={taskFilterFields}
                  filterOperatorMapping={FILTER_OPERATOR_MAPPING}
                  hasNameField={true}
                  hasDirectionField={true}
                />
                <IconButton
                  aria-label="delete"
                  onClick={() => handleDeleteFilter(index)}
                  sx={{ position: "absolute", top: 0, right: 0 }}
                >
                  <CloseIcon />
                </IconButton>
              </Box>
            </Grid>
          ))}
        </Grid>
        <Button variant="outlined" onClick={handleAddCriteria} sx={{ mt: 2 }}>
          Add Criteria
        </Button>
      </CardContent>
    </Card>
  );

  const renderSwitch = (label, checked, key) => (
    <Grid item xs={12} sm={6} md={4} key={key}>
      <Tooltip title={TITLES[key.toUpperCase()]}>
        <FormControlLabel
          control={
            <Switch
              checked={checked}
              onChange={e => handleChange(key, e.target.checked)}
            />
          }
          label={label}
        />
      </Tooltip>
    </Grid>
  );

  const renderTextField = (label, value, key) => (
    <Grid item xs={12} sm={6} md={4} key={key}>
      <Tooltip title={TITLES[key.toUpperCase()]}>
        <TextField
          fullWidth
          label={label}
          type="number"
          value={value || ''}
          onChange={e => handleChange(key, e.target.value ? parseInt(e.target.value, 10) : null)}
        />
      </Tooltip>
    </Grid>
  );

  const renderGeneralSettings = () => (
    <Card id="general" sx={{ mb: 2 }}>
      <CardContent sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom marginBottom={2}>
          General Settings
        </Typography>
        <Grid container spacing={2}>
          {renderTextField(LABELS.INACTIVITY_THRESHOLD, settings.inactivityThreshold, 'inactivityThreshold')}
          {renderTextField(LABELS.ACTIVITIES_PER_CONTACT, settings.activitiesPerContact, 'activitiesPerContact')}
          {renderTextField(LABELS.CONTACTS_PER_ACCOUNT, settings.contactsPerAccount, 'contactsPerAccount')}
          {renderTextField(LABELS.TRACKING_PERIOD, settings.trackingPeriod, 'trackingPeriod')}
          <Grid item xs={12} sm={6} md={4}>
            <Tooltip title={TITLES.QUERY_ACTIVITIES_CREATED_AFTER}>
              <TextField
                fullWidth
                label={LABELS.QUERY_ACTIVITIES_CREATED_AFTER}
                type="datetime-local"
                value={formatDateForInput(settings.latestDateQueried)}
                onChange={e => handleLatestDateQueriedChange("latestDateQueried", e.target.value)}
                InputLabelProps={{ shrink: true }}
              />
            </Tooltip>
          </Grid>
        </Grid>
        <Grid container spacing={2} marginTop={2}>
          {renderSwitch(LABELS.ACTIVATE_BY_OPPORTUNITY, settings.activateByOpportunity, 'activateByOpportunity')}
          {renderSwitch(LABELS.ACTIVATE_BY_MEETING, settings.activateByMeeting, 'activateByMeeting')}
        </Grid>
      </CardContent>
    </Card>
  );


  /*Render return part*/ 
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
  }else{

    return (
      <Box sx={{ width: "100%", mt: 2 }}>
        <AppBar position="sticky" color="default" elevation={0}>
          <Tabs value={currentTab} onChange={handleTabChange} variant="fullWidth">
            <Tab label={LABELS.GENERAL_SETTINGS} />
            <Tab label={LABELS.PROSPECTING_ACTIVITY} />
            <Tab label={LABELS.MEETING_CRITERIA} />
            <Tab label={LABELS.USER_ROLE} />
          </Tabs>
        </AppBar>
  
        {renderGeneralSettings()}
        {renderProspectingActivityCriteria()}
        {renderMeetingCriteria()}
        {renderUserRoleAndTeamMembers()}
  
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
            <Typography>{saving ? LABELS.SAVE_PROGRESS : LABELS.SAVE_SUCCESS}</Typography>
          </Box>
        </Snackbar>
      </Box>
    );
  }
};

export default Settings;