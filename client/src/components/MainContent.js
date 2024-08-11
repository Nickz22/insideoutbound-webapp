import React from "react";
import { Routes, Route } from "react-router-dom";
import { Box } from "@mui/material";
import Prospecting from "../pages/Prospecting/Prospecting";
import Settings from "../pages/Settings";
import Account from "../pages/Account";
import TaskQueryCounter from "../components/TaskQueryCounter/TaskQueryCounter";

const MainContent = () => {
  return (
    <Box flex={1} p={3}>
      <Routes>
        <Route path="prospecting" element={<Prospecting />} />
        <Route path="settings" element={<Settings />} />
        <Route path="account" element={<Account />} />
        <Route path="task-query-counter" element={<TaskQueryCounter />} />
      </Routes>
    </Box>
  );
};

export default MainContent;
