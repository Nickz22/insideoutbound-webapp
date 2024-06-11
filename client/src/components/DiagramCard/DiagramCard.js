import React from "react";
import { Box, Typography } from "@mui/material";

const DiagramCard = ({ title, children }) => {
  return (
    <Box
      sx={{
        border: "1px solid #ccc",
        borderRadius: "8px",
        padding: "16px",
        textAlign: "center",
        margin: "16px",
        boxShadow: "0px 2px 4px rgba(0,0,0,0.1)",
      }}
    >
      <Typography variant="h6" sx={{ marginBottom: "16px" }}>
        {title}
      </Typography>
      {children}
    </Box>
  );
};

export default DiagramCard;
