import React, { useState, useEffect } from "react";
import { NavLink, useLocation, useNavigate } from "react-router-dom";
import {
  Drawer,
  List,
  ListItemButton,
  ListItemText,
  ListItemIcon,
  Divider,
  Box,
  Avatar,
} from "@mui/material";
import { logout, getLoggedInUser } from "../Api/Api";
import "./Sidebar.css";

const CustomNavLink = ({ to, label, icon, alignIconRight = false }) => {
  const location = useLocation();
  const isActive = location.pathname === to;

  return (
    <ListItemButton
      component={NavLink}
      to={to}
      className={isActive ? "active" : ""}
      sx={{
        "&:hover": {
          color: "blue",
          fontWeight: "bold",
        },
        display: "flex",
        justifyContent: "space-between",
      }}
    >
      <ListItemText primary={label} />
      {icon && (
        <ListItemIcon
          sx={{
            minWidth: "auto",
            marginLeft: alignIconRight ? "auto" : 0,
          }}
        >
          {icon}
        </ListItemIcon>
      )}
    </ListItemButton>
  );
};

const Sidebar = () => {
  const navigate = useNavigate();
  const [userPhoto, setUserPhoto] = useState(null);

  useEffect(() => {
    const fetchUserPhoto = async () => {
      try {
        const userData = await getLoggedInUser();
        if (userData.success && userData.data[0].photoUrl) {
          setUserPhoto(userData.data[0].photoUrl);
        }
      } catch (error) {
        console.error("Failed to fetch user photo:", error);
      }
    };

    fetchUserPhoto();
  }, []);

  const handleLogout = async () => {
    try {
      await logout();
      navigate("/");
    } catch (error) {
      console.error("Logout failed:", error);
    }
  };

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: 240,
        flexShrink: 0,
        [`& .MuiDrawer-paper`]: {
          width: 240,
          boxSizing: "border-box",
          display: "flex",
          flexDirection: "column",
        },
      }}
    >
      <List>
        <CustomNavLink to="/app/prospecting" label="Prospecting" />
        <Divider />
        <CustomNavLink to="/app/settings" label="Settings" />
        <Divider />
        <CustomNavLink
          to="/app/task-query-counter"
          label="Task Query Counter"
        />
      </List>
      <Box sx={{ marginTop: "auto", marginBottom: 2 }}>
        <CustomNavLink
          to="/app/account"
          label="Account"
          icon={<Avatar src={userPhoto} sx={{ width: 24, height: 24 }} />}
          alignIconRight={true}
        />
        <Divider />
        <ListItemButton onClick={handleLogout}>
          <ListItemText primary="Logout" />
        </ListItemButton>
      </Box>
    </Drawer>
  );
};

export default Sidebar;
