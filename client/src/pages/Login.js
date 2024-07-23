import React from "react";
import { Button, Box, Container } from "@mui/material";
import logo from "../assets/images/logo.jpeg";
import { generatePKCEChallenge } from "../utils/crypto";
import config from "../config";
import { storeCodeVerifier } from "src/components/Api/Api";

const Login = () => {
  const handleLogin = async (e, loginUrlBase) => {
    e.preventDefault();

    const { codeVerifier, codeChallenge } = await generatePKCEChallenge();
    sessionStorage.setItem("code_verifier", codeVerifier);

    const isSandbox = loginUrlBase.includes("test.salesforce.com");

    try {
      const response = await storeCodeVerifier(codeVerifier, isSandbox);

      if (response.statusCode !== 200) {
        console.error("Failed to start auth session");
        return;
      }

      const clientId = process.env.REACT_APP_CLIENT_ID;
      const redirectUri = `${config.apiBaseUrl}/oauth/callback`;
      const loginUrl = `${loginUrlBase}/services/oauth2/authorize?response_type=code&client_id=${clientId}&redirect_uri=${encodeURIComponent(
        redirectUri
      )}&code_challenge=${codeChallenge}&code_challenge_method=S256`;

      window.location.href = loginUrl;
    } catch (error) {
      console.error("Error starting auth session:", error);
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
