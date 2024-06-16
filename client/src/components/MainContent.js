import React from "react";
import { Routes, Route } from "react-router-dom";
import { Box } from "@mui/material";
import Prospecting from "../pages/Prospecting";
import Performance from "../pages/Performance";
import Forecast from "../pages/Forecast";
import Analysis from "../pages/Analysis";
import Settings from "../pages/Settings";
import Account from "../pages/Account";
import Onboard from "../pages/Onboard";

const MainContent = () => {
  return (
    <Box flex={1} p={3}>
      <Routes>
        <Route path="prospecting" element={<Prospecting />} />
        <Route path="performance" element={<Performance />} />
        <Route path="forecast" element={<Forecast />} />
        <Route path="analysis" element={<Analysis />} />
        <Route path="settings" element={<Settings />} />
        <Route path="account" element={<Account />} />
        <Route path="/" element={<Prospecting />} />
      </Routes>
    </Box>
  );
};

export default MainContent;
