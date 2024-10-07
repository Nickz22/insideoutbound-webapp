import React, { useState } from "react";
import { Button, Box, Container, Typography, TextField } from "@mui/material";
import logo from "../assets/images/logo.jpeg";
import { adminLogin } from "../components/Api/Api";

const AdminLogin = () => {
  const [userId, setUserId] = useState("");
  const [error, setError] = useState("");

  const handleAdminLogin = async (e) => {
    e.preventDefault();

    if (!userId.trim()) {
      setError("Please enter a User ID");
      return;
    }

    try {
      const response = await adminLogin(userId.trim());

      if (response.success) {
        // Store the session token
        localStorage.setItem("sessionToken", response.session_token);
        // Redirect to the main application page or dashboard
        window.location.href = "/app/prospecting";
      } else {
        setError(response.error || "An error occurred during login");
      }
    } catch (error) {
      console.error("Error during admin login:", error);
      setError("An unexpected error occurred. Please try again.");
    }
  };

  return (
    <Container maxWidth="sm" sx={{ textAlign: "center", marginTop: "100px" }}>
      <Box display="flex" flexDirection="column" alignItems="center">
        <img
          src={logo}
          alt="InsideOutbound Logo"
          style={{ marginBottom: "20px", width: "200px" }}
        />
        <Typography variant="h4" gutterBottom>
          Admin Login
        </Typography>
        <TextField
          fullWidth
          label="User ID to login as"
          variant="outlined"
          value={userId}
          onChange={(e) => setUserId(e.target.value)}
          sx={{ marginBottom: "20px" }}
        />
        {error && (
          <Typography color="error" sx={{ marginBottom: "20px" }}>
            {error}
          </Typography>
        )}
        <Button
          variant="contained"
          color="error"
          onClick={handleAdminLogin}
          sx={{
            padding: "10px 20px",
            fontSize: "16px",
            display: "block",
            width: "15rem",
          }}
        >
          Login as Admin
        </Button>
      </Box>
    </Container>
  );
};

export default AdminLogin;
