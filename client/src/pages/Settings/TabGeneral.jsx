import {
  Card,
  CardContent,
  FormControlLabel,
  Grid,
  Switch,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import { useSettings } from "./SettingProvider";

const TabGeneral = () => {
  const { settings, handleChange, formatDateForInput } = useSettings();
  return (
    <Card id="general" sx={{ mb: 2 }}>
      <CardContent sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom marginBottom={2}>
          General Settings
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={4}>
            <Tooltip title="Number of days without a new Task, Event or Opportunity before an approach is considered inactive.">
              <TextField
                fullWidth
                label="Inactivity Threshold (days)"
                type="number"
                value={settings.inactivityThreshold}
                onChange={(e) => {
                  handleChange("inactivityThreshold", parseInt(e.target.value));
                }}
              />
            </Tooltip>
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            <Tooltip title="Number of prospecting activities per Contact required for an Account to be activated.">
              <TextField
                fullWidth
                label="Activities per Contact"
                type="number"
                value={settings.activitiesPerContact}
                onChange={(e) => {
                  handleChange(
                    "activitiesPerContact",
                    parseInt(e.target.value)
                  );
                }}
              />
            </Tooltip>
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            <Tooltip title="Number of activated Contacts required before considering an Account as being actively prospected.">
              <TextField
                fullWidth
                label="Contacts per Account"
                type="number"
                value={settings.contactsPerAccount}
                onChange={(e) => {
                  handleChange("contactsPerAccount", parseInt(e.target.value));
                }}
              />
            </Tooltip>
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            <Tooltip title="Number of days within which prospecting activities should be created to be attributed to an approach. If the first prospecting activity was created on 1/1/2024 and the tracking period is 5 days, then any other prospecting activity, event or opportunity included under the same approach needs to be created by 1/6/2024.">
              <TextField
                fullWidth
                label="Tracking Period (days)"
                type="number"
                value={settings.trackingPeriod}
                onChange={(e) => {
                  handleChange("trackingPeriod", parseInt(e.target.value));
                }}
              />
            </Tooltip>
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            <Tooltip title="We'll query activities created on or after this time to calculate your prospecting activity.">
              <TextField
                fullWidth
                label="Query activities created after"
                type="datetime-local"
                value={
                  formatDateForInput
                    ? formatDateForInput(settings.latestDateQueried)
                    : ""
                }
                onChange={(e) => {
                  handleChange("latestDateQueried", e.target.value);
                }}
                InputLabelProps={{
                  shrink: true,
                }}
              />
            </Tooltip>
          </Grid>
        </Grid>
        <Grid container spacing={2} marginTop={2}>
          <Grid item xs={12} sm={6} md={4}>
            <Tooltip title="Consider an Account as 'approached' when an Opportunity is created after a prospecting activity was already created under the same Account.">
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.activateByOpportunity}
                    onChange={(e) => {
                      handleChange("activateByOpportunity", e.target.checked);
                    }}
                  />
                }
                label="Activate by Opportunity"
              />
            </Tooltip>
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            <Tooltip title="Consider an Account as 'approached' when a Meeting is created after a prospecting activity was already created under the same Account.">
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.activateByMeeting}
                    onChange={(e) => {
                      handleChange("activateByMeeting", e.target.checked);
                    }}
                  />
                }
                label="Activate by Meeting"
              />
            </Tooltip>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
};

export default TabGeneral;
