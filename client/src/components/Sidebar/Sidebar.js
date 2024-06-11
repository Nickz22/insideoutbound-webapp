import React from "react";
import { NavLink, useLocation } from "react-router-dom";
import {
  Drawer,
  List,
  ListItemButton,
  ListItemText,
  Divider,
} from "@mui/material";
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
  return (
    <Drawer
      variant="permanent"
      sx={{
        width: 240,
        flexShrink: 0,
        [`& .MuiDrawer-paper`]: { width: 240, boxSizing: "border-box" },
      }}
    >
      <List>
        <CustomNavLink to="/prospecting" label="Prospecting" />
        <Divider />
        <CustomNavLink to="/performance" label="Performance" />
        <Divider />
        <CustomNavLink to="/forecast" label="Forecast" />
        <Divider />
        <CustomNavLink to="/analysis" label="Analysis" />
        <Divider />
        <CustomNavLink to="/settings" label="Settings" />
        <Divider />
        <CustomNavLink to="/account" label="Account" />
      </List>
    </Drawer>
  );
};

export default Sidebar;
