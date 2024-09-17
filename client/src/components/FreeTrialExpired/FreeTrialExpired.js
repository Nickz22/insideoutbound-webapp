import React from "react";
import { Box, Paper, Typography, Button } from "@mui/material";
import { useNavigate } from "react-router-dom";

const FreeTrialExpired = () => {
  const navigate = useNavigate();

  return (
    <Box
      sx={{
        position: "relative",
        width: "100%",
        height: "100dvh",
        maxHeight: "100dvh",
        overflow: "hidden",
        backgroundColor: "#FFFFFF",
        maxWidth: "100%",
        boxSizing: "border-box",
        padding: 0,
        margin: 0,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <Paper
        elevation={3}
        sx={{
          width: "852px",
          borderRadius: "50px",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
          padding: "34px 67px 47px",
          boxShadow: "2px 13px 20.5px 1px #0000001A",
        }}
      >
        <Typography
          sx={{
            marginBottom: "14px",
            fontSize: "14px",
            lineHeight: "1",
            letterSpacing: "4.76px",
            fontWeight: "500",
            textAlign: "center",
          }}
        >
          HEADS UP!
        </Typography>
        <Typography
          sx={{
            marginBottom: "28px",
            fontSize: "54px",
            lineHeight: "1",
            letterSpacing: "-1.62px",
            fontWeight: "700",
            textAlign: "center",
          }}
        >
          Your free trial is over
        </Typography>
        <Typography
          sx={{
            marginBottom: "40px",
            fontSize: "18px",
            lineHeight: "1.78",
            fontWeight: "400",
            textAlign: "center",
          }}
        >
          Tap into your prospecting data to get the most out of your sales team by upgrading to paid.
        </Typography>

        <Button
          onClick={() => navigate("/app/account")}
          sx={{
            background:
              "linear-gradient(168deg, #FF7D2F 24.98%, #491EFF 97.93%)",
            height: "57px",
            width: "388px",
            borderRadius: "40px",
            color: "white",
            fontSize: "32px",
            letterSpacing: "-0.96px",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            textTransform: "none",
          }}
        >
          Upgrade to Paid
        </Button>
      </Paper>
    </Box>
  );
};

export default FreeTrialExpired;
