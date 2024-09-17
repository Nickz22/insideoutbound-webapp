import React from "react";
import { Grid } from "@mui/material";
import MetricCard from "../MetricCard/MetricCard";

const ProspectingMetrics = ({
  summaryData,
  summaryLoading,
  getLoadingComponent,
}) => {
  if (summaryLoading) {
    return getLoadingComponent("Generating summary...");
  }

  return (
    <Grid container spacing={2}>
      <Grid item xs={12} sm={6} md={4} lg={4}>
        <MetricCard
          title="Total Activations"
          value={summaryData.total_activations?.toString() ||  "0"}
          subText=""
          tooltipTitle="The number of approached accounts in the selected period"
        />
      </Grid>
      <Grid item xs={12} sm={6} md={4} lg={4}>
        <MetricCard
          title="Activations Today"
          value={summaryData.activations_today?.toString() || "0"}
          subText=""
          tooltipTitle="The number of accounts which were approached today"
        />
      </Grid>
      <Grid item xs={12} sm={6} md={4} lg={4}>
        <MetricCard
          title="Total Tasks"
          value={summaryData.total_tasks?.toString() || "0"}
          subText=""
          tooltipTitle="The total number of prospecting Tasks created in the selected period"
        />
      </Grid>
      <Grid item xs={12} sm={6} md={4} lg={4}>
        <MetricCard
          title="Total Meetings"
          value={summaryData.total_events?.toString() || "0"}
          subText=""
          tooltipTitle="The total number of meetings created in the selected period"
        />
      </Grid>
      <Grid item xs={12} sm={6} md={4} lg={4}>
        <MetricCard
          title="Contacts Approached"
          value={summaryData.total_active_contacts?.toString() || "0"}
          subText=""
          tooltipTitle="The total number of contacts with sufficient outbound prospecting activities to be considered activated"
        />
      </Grid>
      <Grid item xs={12} sm={6} md={4} lg={4}>
        <MetricCard
          title="Avg Tasks Per Contact"
          value={summaryData.avg_tasks_per_contact?.toFixed(2) || "0"}
          subText=""
          tooltipTitle="The average number of tasks per contact under each activated account"
        />
      </Grid>
      <Grid item xs={12} sm={6} md={4} lg={4}>
        <MetricCard
          title="Avg Contacts Per Account"
          value={summaryData.avg_contacts_per_account?.toFixed(2) || "0"}
          subText=""
          tooltipTitle="The average number of tasks per activated account"
        />
      </Grid>
      <Grid item xs={12} sm={6} md={4} lg={4}>
        <MetricCard
          title="Total Deals"
          value={summaryData.total_deals?.toString() || "0"}
          subText=""
          tooltipTitle="The total number of open opportunities related to any activated account in the selected period"
        />
      </Grid>
      <Grid item xs={12} sm={6} md={4} lg={4}>
        <MetricCard
          title="Total Pipeline Value"
          value={`$${summaryData.total_pipeline_value?.toLocaleString() || "0"}`}
          subText=""
          tooltipTitle="The total amount of open opportunities related to any activated account in the selected period"
        />
      </Grid>
      <Grid item xs={12} sm={6} md={4} lg={4}>
        <MetricCard
          title="Closed Won Opportunity Value"
          value={`$${summaryData.closed_won_opportunity_value?.toLocaleString() || "0"}`}
          subText=""
          tooltipTitle="The total value of opportunities that have been closed and won in the selected period"
        />
      </Grid>
      <Grid item xs={12} sm={6} md={4} lg={4}>
        <MetricCard
          title="Engaged Activations"
          value={summaryData.engaged_activations?.toString() || "0"}
          subText=""
          tooltipTitle="The number of activated Accounts which have had inbound engagement"
        />
      </Grid>
    </Grid>
  );
};

export default ProspectingMetrics;
