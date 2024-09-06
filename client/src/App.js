import React, { useEffect } from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  useNavigate,
  useLocation,
} from "react-router-dom";
import { Box } from "@mui/material";
import Sidebar from "./components/Sidebar/Sidebar";
import MainContent from "./components/MainContent";
import Login from "./pages/Login";
import Onboard from "./pages/Onboard";
import "./App.css";

const AppRoutes = () => {
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const queryParams = new URLSearchParams(location.search);
    const sessionToken = queryParams.get("session_token");

    if (sessionToken) {
      // Store the session token (you might want to use a more secure method)
      localStorage.setItem("sessionToken", sessionToken);

      // Remove the session token from the URL and navigate to the appropriate page
      const newPath = location.pathname.replace(/\/?$/, "");
      const newSearch = location.search.replace(/[?&]session_token=[^&]+/, "");
      navigate(newPath + newSearch, { replace: true });
    }
  }, [location, navigate]);

  return (
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
  );
};

function App() {
  return (
    <Router>
      <AppRoutes />
    </Router>
  );
}

export default App;
