import React from "react";
import { Grid, Card, CardContent, Typography } from "@mui/material";

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

export default ProspectingMetadataOverview;
