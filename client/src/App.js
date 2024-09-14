import React, { useEffect } from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  useNavigate,
  useLocation,
} from "react-router-dom";
import { Box, createTheme, ThemeProvider } from "@mui/material";
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
  const theme = createTheme({
    typography: {
      fontFamily: `"Albert Sans", system-ui, sans-serif`,
      display1: {
        fontSize: "88px",
        fontWeight: "700",
        lineHeight: "1.2",
      },
      "body1": {
        fontSize: "16px",
        lineHeight: "1.78",
        fontWeight: "400",
      },
      "body2": {
        fontSize: "18px",
        lineHeight: "1.78",
        fontWeight: "400",
      },
      subtitle1: {
        fontSize: "14px",
        lineHeight: "1.78",
        fontWeight: "500",
      },
      h1: {
        fontWeight: "700",
        fontSize: "54px",
        lineHeight: "0.93"
      },
      h2: {
        fontWeight: "500",
        fontSize: "40px",
        lineHeight: "1.78"
      },
      h3: {
        fontWeight: "500",
        fontSize: "32px",
        lineHeight: "1.78"
      }
    }
  });

  return (
    <ThemeProvider theme={theme}>
      <Router>
        <AppRoutes />
      </Router>
    </ThemeProvider>
  );
}

export default App;
