import React from "react";
import { NavLink, useLocation, useNavigate } from "react-router-dom";
import {
  Drawer,
  List,
  ListItemButton,
  ListItemText,
  Divider,
  Box,
} from "@mui/material";
import { logout } from "../Api/Api";
import "./Sidebar.css";

const CustomNavLink = ({ to, label }) => {
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
      }}
    >
      <ListItemText primary={label} />
    </ListItemButton>
  );
};

const Sidebar = () => {
  const navigate = useNavigate();

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
        <CustomNavLink to="/app/account" label="Account" />
        <CustomNavLink
          to="/app/task-query-counter"
          label="Task Query Counter"
        />
      </List>
      <Box sx={{ marginTop: "auto", marginBottom: 2, marginLeft: 2 }}>
        <ListItemButton onClick={handleLogout}>
          <ListItemText primary="Logout" />
        </ListItemButton>
      </Box>
    </Drawer>
  );
};

export default Sidebar;
