import React from "react";
import { NavLink } from "react-router-dom";
import { Drawer, List, ListItem, ListItemText, Divider } from "@mui/material";
import "./Sidebar.css";

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
        <ListItem
          button
          component={NavLink}
          to="/prospecting"
          className={({ isActive }) => (isActive ? "active" : "")}
        >
          <ListItemText primary="Prospecting" />
        </ListItem>
        <Divider />
        <ListItem
          button
          component={NavLink}
          to="/performance"
          className={({ isActive }) => (isActive ? "active" : "")}
        >
          <ListItemText primary="Performance" />
        </ListItem>
        <Divider />
        <ListItem
          button
          component={NavLink}
          to="/forecast"
          className={({ isActive }) => (isActive ? "active" : "")}
        >
          <ListItemText primary="Forecast" />
        </ListItem>
        <Divider />
        <ListItem
          button
          component={NavLink}
          to="/analysis"
          className={({ isActive }) => (isActive ? "active" : "")}
        >
          <ListItemText primary="Analysis" />
        </ListItem>
        <Divider />
        <ListItem
          button
          component={NavLink}
          to="/settings"
          className={({ isActive }) => (isActive ? "active" : "")}
        >
          <ListItemText primary="Settings" />
        </ListItem>
        <Divider />
        <ListItem
          button
          component={NavLink}
          to="/account"
          className={({ isActive }) => (isActive ? "active" : "")}
        >
          <ListItemText primary="Account" />
        </ListItem>
      </List>
    </Drawer>
  );
};

export default Sidebar;
