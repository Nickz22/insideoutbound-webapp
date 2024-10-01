import React from "react";
import { Box } from "@mui/material";
import { useNavigate } from "react-router-dom";

interface FreeTrialRibbonProps {
  daysLeft: number;
}

const FreeTrialRibbon: React.FC<FreeTrialRibbonProps> = ({ daysLeft }) => {
  const navigate = useNavigate();

  return (
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
      {daysLeft} days left in trial
    </Box>
  );
};

export default FreeTrialRibbon;