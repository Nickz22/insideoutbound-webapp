import React from "react";
import { Box, Typography } from "@mui/material";

const MetricCard = ({ title, value, subText }) => {
  return (
    <Box
      sx={{
        border: "1px solid #ccc",
        borderRadius: "8px",
        padding: "16px",
        textAlign: "center",
        minWidth: "150px",
        margin: "16px",
        boxShadow: "0px 2px 4px rgba(0,0,0,0.1)",
      }}
    >
      <Typography variant="h6">{title}</Typography>
      <Typography variant="h4" sx={{ color: "teal", margin: "8px 0" }}>
        {value}
      </Typography>
      <Typography variant="body2">{subText}</Typography>
    </Box>
  );
};

export default MetricCard;
