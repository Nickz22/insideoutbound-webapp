import React from "react";
import {
  Timeline,
  TimelineItem,
  TimelineSeparator,
  TimelineConnector,
  TimelineContent,
  TimelineDot,
} from "@mui/lab";
import { Typography, List, ListItem, ListItemText } from "@mui/material";

const getStatusColor = (status) => {
  switch (status.toLowerCase()) {
    case "completed":
      return "success";
    case "in progress":
      return "primary";
    case "planned":
      return "info";
    default:
      return "grey";
  }
};

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

export default ProspectingEffortTimeline;
