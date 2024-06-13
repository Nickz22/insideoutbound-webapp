import React from "react";
import { Button, Box, Container } from "@mui/material";
import logo from "../assets/images/logo.jpeg";

// Helper function to generate a code verifier and code challenge
const generatePKCEChallenge = async () => {
  const array = new Uint8Array(32);
  window.crypto.getRandomValues(array);
  const codeVerifier = Array.from(array, (byte) =>
    byte.toString(16).padStart(2, "0")
  ).join("");
  const encoder = new TextEncoder();
  const codeData = encoder.encode(codeVerifier);
  const digest = await window.crypto.subtle.digest("SHA-256", codeData);
  const base64Digest = btoa(String.fromCharCode(...new Uint8Array(digest)));
  const codeChallenge = base64Digest
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/, "");
  return { codeVerifier, codeChallenge };
};

const Login = () => {
  const handleLogin = async (e, loginUrlBase) => {
    e.preventDefault();

    const { codeVerifier, codeChallenge } = await generatePKCEChallenge();
    localStorage.setItem("code_verifier", codeVerifier); // Save the verifier to use later in the token exchange

    const clientId = process.env.REACT_APP_CLIENT_ID;
    const redirectUri = "http://localhost:5000/oauth/callback"; // Flask OAuth handler endpoint
    const loginUrl = `${loginUrlBase}/services/oauth2/authorize?response_type=code&client_id=${clientId}&redirect_uri=${redirectUri}&code_challenge=${codeChallenge}&code_challenge_method=S256`;

    window.location.href = loginUrl;
  };

  return (
    <Container maxWidth="sm" sx={{ textAlign: "center", marginTop: "100px" }}>
      <Box display="flex" flexDirection="column" alignItems="center">
        <img
          src={logo}
          alt="InsideOutbound Logo"
          style={{ marginBottom: "20px", width: "200px" }}
        />
        <Box>
          <Button
            variant="contained"
            color="primary"
            onClick={(e) => handleLogin(e, "https://login.salesforce.com")}
            sx={{
              padding: "10px 20px",
              fontSize: "16px",
              display: "block",
              marginBottom: "10px",
              width: "15rem",
            }}
          >
            Login to Salesforce
          </Button>
          <Button
            variant="contained"
            color="secondary"
            onClick={(e) => handleLogin(e, "https://test.salesforce.com")}
            sx={{
              padding: "10px 20px",
              fontSize: "16px",
              display: "block",
              width: "15rem",
            }}
          >
            Login to Sandbox
          </Button>
        </Box>
      </Box>
    </Container>
  );
};

export default Login;
