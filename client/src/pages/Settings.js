import React, { useState, useEffect } from "react";
import axios from "axios";
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
} from "@mui/material";
import CheckCircleOutlineIcon from "@mui/icons-material/CheckCircleOutline";
import CloseIcon from "@mui/icons-material/Close";
import { useNavigate } from "react-router-dom";
import {
  fetchEventFilterFields,
  fetchTaskFilterFields,
} from "../components/Api/Api";
import { FILTER_OPERATOR_MAPPING } from "../utils/c";
import FilterContainer from "../components/FilterContainer/FilterContainer";

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
  });

  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [taskFilterFields, setTaskFilterFields] = useState();
  const [eventFilterFields, setEventFilterFields] = useState();
  const [isLoading, setIsLoading] = useState(true);

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
          axios.get("http://localhost:8000/get_settings"),
        ]);

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
        setSettings(settingsResponse.data);
      } catch (error) {
        console.error("Error fetching initial data:", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchInitialData();
  }, [navigate]);

  const handleChange = (field, value) => {
    setSettings((prev) => ({ ...prev, [field]: value }));
    saveSettings({ ...settings, [field]: value });
  };

  const saveSettings = async (updatedSettings) => {
    setSaving(true);
    setSaveSuccess(false);
    try {
      await axios.post("http://localhost:8000/save_settings", updatedSettings);
      setSaveSuccess(true);
    } catch (error) {
      console.error("Error saving settings:", error);
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteFilter = async (index) => {
    const newCriteria = settings.criteria.filter((_, i) => i !== index);
    const updatedSettings = { ...settings, criteria: newCriteria };
    setSettings(updatedSettings);
    await saveSettings(updatedSettings);
  };

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
    <Box sx={{ width: "100%", mt: 2 }}>
      <Card sx={{ mb: 2 }}>
        <CardContent sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom marginBottom={2}>
            General Settings
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={4}>
              <TextField
                fullWidth
                label="Inactivity Threshold (days)"
                type="number"
                value={settings.inactivityThreshold}
                onChange={(e) =>
                  handleChange("inactivityThreshold", parseInt(e.target.value))
                }
              />
            </Grid>
            <Grid item xs={12} sm={6} md={4}>
              <TextField
                fullWidth
                label="Activities per Contact"
                type="number"
                value={settings.activitiesPerContact}
                onChange={(e) =>
                  handleChange("activitiesPerContact", parseInt(e.target.value))
                }
              />
            </Grid>
            <Grid item xs={12} sm={6} md={4}>
              <TextField
                fullWidth
                label="Contacts per Account"
                type="number"
                value={settings.contactsPerAccount}
                onChange={(e) =>
                  handleChange("contactsPerAccount", parseInt(e.target.value))
                }
              />
            </Grid>
            <Grid item xs={12} sm={6} md={4}>
              <TextField
                fullWidth
                label="Tracking Period (days)"
                type="number"
                value={settings.trackingPeriod}
                onChange={(e) =>
                  handleChange("trackingPeriod", parseInt(e.target.value))
                }
              />
            </Grid>
          </Grid>
          <Grid container spacing={2} marginTop={2}>
            <Grid item xs={12} sm={6} md={4}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.activateByOpportunity}
                    onChange={(e) =>
                      handleChange("activateByOpportunity", e.target.checked)
                    }
                  />
                }
                label="Activate by Opportunity"
              />
            </Grid>
            <Grid item xs={12} sm={6} md={4}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.activateByMeeting}
                    onChange={(e) =>
                      handleChange("activateByMeeting", e.target.checked)
                    }
                  />
                }
                label="Activate by Meeting"
              />
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      <Card sx={{ mb: 2 }}>
        <CardContent sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>
            Prospecting Activity Criteria
          </Typography>
          <Grid container spacing={2}>
            {settings.criteria.map((criteriaContainer, index) => (
              <Grid item xs={12} md={6} key={index}>
                <Box sx={{ position: "relative" }}>
                  <FilterContainer
                    initialFilterContainer={criteriaContainer}
                    onLogicChange={(newContainer) => {
                      const newCriteria = [...settings.criteria];
                      newCriteria[index] = newContainer;
                      handleChange("criteria", newCriteria);
                    }}
                    onValueChange={(newContainer) => {
                      const newCriteria = [...settings.criteria];
                      newCriteria[index] = newContainer;
                      handleChange("criteria", newCriteria);
                    }}
                    filterFields={taskFilterFields}
                    filterOperatorMapping={FILTER_OPERATOR_MAPPING}
                    hasNameField={true}
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
          <Button
            variant="outlined"
            onClick={() =>
              handleChange("criteria", [
                ...settings.criteria,
                { filters: [], filterLogic: "", name: "" },
              ])
            }
            sx={{ mt: 2 }}
          >
            Add Criteria
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardContent sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>
            Meeting Criteria
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <Select
                fullWidth
                value={settings.meetingObject}
                onChange={(e) => handleChange("meetingObject", e.target.value)}
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
              onLogicChange={(newContainer) =>
                handleChange("meetingsCriteria", newContainer)
              }
              filterFields={eventFilterFields}
              filterOperatorMapping={FILTER_OPERATOR_MAPPING}
            />
          </Box>
        </CardContent>
      </Card>

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
