import React from "react";
import { IconButton, styled } from "@mui/material";
import ArrowForwardIosIcon from "@mui/icons-material/ArrowForwardIos";

const StyledIconButton = styled(IconButton)(({ theme }) => ({
  position: "absolute",
  right: theme.spacing(2),
  top: "50%",
  transform: "translateY(-50%)",
  transition: "right 0.25s ease-in-out", // Smooth transition for the right property
  "&:hover": {
    right: theme.spacing(1), // Move the button closer to the edge on hover
  },
}));

const AnimatedIconButton = ({ onClick }) => {
  return (
    <StyledIconButton onClick={onClick} aria-label="Next">
      <ArrowForwardIosIcon />
    </StyledIconButton>
  );
};

export default AnimatedIconButton;
