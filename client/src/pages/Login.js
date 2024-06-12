import React, { useState } from "react";
import logo from "../assets/images/logo.jpeg";

const Login = () => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const handleLogin = (e) => {
    e.preventDefault();

    // Replace with your Salesforce client ID and redirect URI
    const clientId = "YOUR_CLIENT_ID";
    const redirectUri = "http://localhost:3000/oauth/callback";
    const loginUrl = `https://login.salesforce.com/services/oauth2/authorize?response_type=code&client_id=${clientId}&redirect_uri=${redirectUri}`;

    // Redirect to Salesforce OAuth2 authorization endpoint
    window.location.href = loginUrl;
  };

  return (
    <div style={{ textAlign: "center", marginTop: "100px" }}>
      <img
        src={logo}
        alt="InsideOutbound Logo"
        style={{ marginBottom: "20px", width: "200px" }}
      />
      <form onSubmit={handleLogin}>
        <div>
          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            style={{
              padding: "10px",
              fontSize: "16px",
              marginBottom: "10px",
              width: "200px",
            }}
          />
        </div>
        <div>
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            style={{
              padding: "10px",
              fontSize: "16px",
              marginBottom: "20px",
              width: "200px",
            }}
          />
        </div>
        <button
          type="submit"
          style={{ padding: "10px 20px", fontSize: "16px" }}
        >
          Login with Salesforce
        </button>
      </form>
    </div>
  );
};

export default Login;
