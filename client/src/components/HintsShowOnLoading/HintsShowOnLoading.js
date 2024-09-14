import React, { useEffect, useState } from "react";
import { Box, Paper, Typography } from "@mui/material";
import SettingIcon from "../icons/SettingIcon";
import DetailRowIcon from "../icons/DetailRowIcon";
import FilterIcon from "../icons/FilterIcon";
import FunnelFilterIcon from "../icons/FunnelFilterIcon";
import MemberIcon from "../icons/MemberIcon";
import DocumentIcon from "../icons/DocumentIcon";
import PaidIcon from "../icons/PaidIcon";

const HintsShowOnLoading = () => {
  const hints = [
    {
      icon: <SettingIcon />,
      hintDesc:
        "Go to Settings and set the “Last Queried Date” to pull more Tasks into your Prospecting page",
    },
    {
      icon: <PaidIcon />,
      hintDesc: "Convert to “Paid” in the Account tab",
    },
    {
      icon: <DetailRowIcon />,
      hintDesc:
        "Change to “Detail” view and click a row to see prospecting effort for an account",
    },
    {
      icon: <FilterIcon />,
      hintDesc:
        "Add additional prospecting activity filters in the Settings tab",
    },
    {
      icon: <FunnelFilterIcon />,
      hintDesc:
        "Apply Account-level filtering via the filter at top-left of the Prospecting page",
    },
    {
      icon: <MemberIcon />,
      hintDesc: "Add more members to your team in the Settings tab",
    },
    {
      icon: <DocumentIcon />,
      hintDesc: "Still fetching prospecting activity, hang tight",
    },
  ];

  const [currentIdx, setCurrentIdx] = useState(0);
  const [fade, setFade] = useState(true);
  const [isLastHint, setIsLastHint] = useState(false);

  useEffect(() => {
    if (isLastHint) return; // Stop the interval if we're at the last hint

    const interval = setInterval(() => {
      setFade(false);

      setTimeout(() => {
        setCurrentIdx((prev) => {
          const nextIdx = prev + 1;
          if (nextIdx >= hints.length - 1) {
            setIsLastHint(true);
            clearInterval(interval);
          }
          return nextIdx;
        });
        setFade(true);
      }, 1000);
    }, 5000);

    return () => clearInterval(interval);
  }, [hints.length, isLastHint]);

  return (
    <Paper
      elevation={3}
      sx={{
        width: "852px",
        height: "185px",
        borderRadius: "50px",
        display: "flex",
        flexDirection: "column",
        gap: "10px",
        justifyContent: "center",
        alignItems: "center",
        padding: "22px 82px 32px",
        boxShadow: "2px 13px 20.5px 1px #0000001A",
        opacity: fade ? 1 : 0,
        transition: "opacity 1s ease-in-out", // Apply fade-in/fade-out transition
      }}
    >
      <Box
        sx={{
          width: "49px",
          height: "49px",
          color: "#533AF3",
        }}
      >
        {hints[currentIdx].icon}
      </Box>
      <Typography
        sx={{
          color: "#4C4C4C",
          fontSize: "24px",
          fontWeight: "400",
          lineHeight: "1.5",
          letterSpacing: "-0.72px",
        }}
      >
        {hints[currentIdx].hintDesc}
      </Typography>
    </Paper>
  );
};

export default HintsShowOnLoading;
