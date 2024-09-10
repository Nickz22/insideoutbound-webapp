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
import Logo from "../Logo/Logo";
import ProspectIcon from "../icons/ProspectIcon";
import SettingIcon from "../icons/SettingIcon";
import TaskQueryCounterIcon from "../icons/TaskQueryCounterIcon";

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
          fontWeight: "500",
          color: "#ffffff",
          background: "linear-gradient(168deg, #ff7d2f 24.98%, #491eff 97.93%)"
        },
        "&:hover > *": {
          color: "#ffffff",
        },
        fontSize: "18px",
        display: "flex",
        justifyContent: "flex-start",
        gap: "18px",
        fontWeight: isActive ? "500" : "300",
        color: isActive ? "#ffffff" : "#879FCA",
        background: isActive ? "linear-gradient(168deg, #ff7d2f 24.98%, #491eff 97.93%)" : "transparent",
      }}
    >
      {icon && (
        <ListItemIcon
          sx={{
            minWidth: "auto",
            marginLeft: alignIconRight ? "auto" : 0,
            color: isActive ? "#ffffff" : "#879FCA",
          }}
        >
          {icon}
        </ListItemIcon>
      )}
      <ListItemText primary={label} />
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
        backgroundColor: "rgba(30, 36, 47, 1)",
        flexShrink: 0,
        [`& .MuiDrawer-paper`]: {
          width: 240,
          boxSizing: "border-box",
          display: "flex",
          flexDirection: "column",
          backgroundColor: "rgba(30, 36, 47, 1)",
          paddingTop: "47px"
        },
      }}
    >
      <div style={{ display: "flex", flexDirection: "row", justifyContent: "center", width: "100%", marginBottom: "36px" }}>
        <Logo />
      </div>

      <Divider sx={{ backgroundColor: "rgba(135, 159, 202, 0.5)", margin: "0px 33px 28px" }} />
      <List>
        <CustomNavLink to="/app/prospecting" label="Prospecting" icon={<ProspectIcon />} />
        <CustomNavLink to="/app/settings" label="Settings" icon={<SettingIcon />} />
        <CustomNavLink
          to="/app/task-query-counter"
          label="Task Query Counter"
          icon={<TaskQueryCounterIcon />}
        />
      </List>
      <Box sx={{ marginTop: "auto", marginBottom: 2 }}>
        <CustomNavLink
          to="/app/account"
          label="Account"
          icon={<Avatar src={userPhoto} sx={{ width: 24, height: 24 }} />}
          alignIconRight={true}
        />
        <ListItemButton
          sx={{
            "&:hover": {
              fontWeight: "500",
              color: "#ffffff",
              background: "linear-gradient(168deg, #ff7d2f 24.98%, #491eff 97.93%)"
            },
            color: "#879FCA",
            fontSize: "18px",
            fontWeight: "300",
          }}
          onClick={handleLogout}
        >
          <ListItemText primary="Logout" />
        </ListItemButton>
      </Box>
    </Drawer>
  );
};

export default Sidebar;
