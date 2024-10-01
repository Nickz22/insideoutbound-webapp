import React from "react";
import { Box, Typography } from "@mui/material";
import Lottie from "lottie-react";
import ProspectingLoadingAnimation from "../../assets/lottie/prospecting-loading-animation.json";
import HintsShowOnLoading from "../HintsShowOnLoading/HintsShowOnLoading";

const LoadingComponent = ({ message }) => {
  return (
    <Box
      sx={{
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        height: "100vh",
        width: "100%",
      }}
    >
      <Box
        sx={{
          position: "relative",
          width: "100%",
          maxWidth: 852,
          textAlign: "center",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
        }}
      >
        <Typography
          variant="h6"
          gutterBottom
          sx={{
            fontWeight: "700",
            fontSize: "54px",
            letterSpacing: "-1.62px",
            lineHeight: "1",
          }}
        >
          {message}
        </Typography>
        <Box
          sx={{
            width: "271px",
            height: "271px",
            position: "relative",
            top: "-75px",
          }}
        >
          <Lottie animationData={ProspectingLoadingAnimation} loop={true} />
        </Box>

        <Typography
          variant="caption"
          gutterBottom
          sx={{
            marginTop: "-130px",
            marginBottom: "20px",
            width: "586px",
            fontSize: "18px",
            lineHeight: "1.78",
          }}
        >
          While the magic runs behind the scenes, here are some helpful hints to
          get the best use case from the app:
        </Typography>

        <HintsShowOnLoading />
      </Box>
    </Box>
  );
};

export default LoadingComponent;
