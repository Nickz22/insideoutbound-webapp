import React from "react";
import { Routes, Route } from "react-router-dom";
import { Box } from "@mui/material";
import Prospecting from "../pages/Prospecting/Prospecting";
import Settings from "../pages/Settings/Settings";
import Account from "../pages/Account";
import TaskQueryCounter from "../components/TaskQueryCounter/TaskQueryCounter";
import { SettingsProvider } from "src/pages/Settings/SettingProvider";

const MainContent = () => {
  return (
    <Box flex={1} sx={{ width: "100%", maxWidth: "100%", overflow: "hidden", height: "100dvh", maxHeight: "100dvh" }}>
      <Routes>
        <Route path="prospecting" element={<Prospecting />} />
        <Route path="settings" element={<SettingsProvider><Settings /></SettingsProvider>} />
        <Route path="account" element={<Account />} />
        <Route path="task-query-counter" element={<TaskQueryCounter />} />
      </Routes>
    </Box>
  );
};

export default MainContent;
