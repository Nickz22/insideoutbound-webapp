import React from "react";
import { Button, Box, Container } from "@mui/material";
import logo from "../assets/images/logo.jpeg";
import axios from "axios";
import { generatePKCEChallenge } from "../utils/crypto";

const Login = () => {
  const handleLogin = async (e, loginUrlBase) => {
    e.preventDefault();

    const { codeVerifier, codeChallenge } = await generatePKCEChallenge();
    sessionStorage.setItem("code_verifier", codeVerifier); // Save the verifier securely

    await axios.post("http://localhost:8000/store_code_verifier", {
      code_verifier: { data: codeVerifier },
    });

    const clientId = process.env.REACT_APP_CLIENT_ID;
    const redirectUri = `http://localhost:8000/oauth/callback?code_verifier=${encodeURIComponent(
      codeVerifier
    )}`;
    const loginUrl = `${loginUrlBase}/services/oauth2/authorize?response_type=code&client_id=${clientId}&redirect_uri=${encodeURIComponent(
      redirectUri
    )}&code_challenge=${codeChallenge}&code_challenge_method=S256`;

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
