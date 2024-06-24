import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { Box } from "@mui/material";
import Sidebar from "./components/Sidebar/Sidebar";
import MainContent from "./components/MainContent";
import Login from "./pages/Login";
import Onboard from "./pages/Onboard";
import "./App.css";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/onboard" element={<Onboard />} />
        <Route
          path="/app/*"
          element={
            <Box display="flex">
              <Sidebar />
              <MainContent />
            </Box>
          }
        />
      </Routes>
    </Router>
  );
}

export default App;
