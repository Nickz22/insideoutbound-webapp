import React, { useState, useEffect } from "react";
import { getInstanceUrl, getLoggedInUser } from "./../components/Api/Api";
import { Box, Typography, Avatar, Link, CircularProgress } from "@mui/material";

const Account = () => {
  const [user, setUser] = useState(null);
  const [instanceUrl, setInstanceUrl] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [userResponse, instanceUrlResponse] = await Promise.all([
          getLoggedInUser(),
          getInstanceUrl(),
        ]);

        if (userResponse.success && instanceUrlResponse.success) {
          setUser(userResponse.data[0]);
          setInstanceUrl(instanceUrlResponse.data[0]);
        } else {
          setError("Failed to fetch user data or instance URL");
        }
      } catch (error) {
        setError("An error occurred while fetching data");
        console.error("Error fetching data:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return <CircularProgress />;
  }

  if (error) {
    return <Typography color="error">{error}</Typography>;
  }

  return (
    <Box display="flex" flexDirection="column" alignItems="center">
      <Avatar
        src={user.photoUrl}
        alt={`${user.firstName} ${user.lastName}`}
        sx={{ width: 100, height: 100, marginBottom: 2 }}
      />
      <Typography variant="h4" gutterBottom>
        Account Information
      </Typography>
      <Typography variant="body1">
        Name:{" "}
        <Link
          href={`${instanceUrl}/${user.id}`}
          target="_blank"
          rel="noopener noreferrer"
        >
          {user.firstName} {user.lastName}
        </Link>
      </Typography>
      <Typography variant="body1">Email: {user.email}</Typography>
      <Typography variant="body1">Username: {user.username}</Typography>
    </Box>
  );
};

export default Account;
