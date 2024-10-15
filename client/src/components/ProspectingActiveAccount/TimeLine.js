import React, { useEffect, useState } from "react";
import { Typography, Box } from "@mui/material";
import {
  AccessTime,
  Call,
  Message,
  Event,
  BusinessCenter,
} from "@mui/icons-material";

// Function to map icon names to actual icons
const getIcon = (iconName, color) => {
  switch (iconName) {
    case "Message":
      return <Message sx={{ color, marginLeft: "-100%" }} />;
    case "Dial":
      return <Call sx={{ color, marginLeft: "-100%" }} />;
    case "Meeting":
      return <Event sx={{ color, marginLeft: "-100%" }} />;
    case "Opportunity":
      return <BusinessCenter sx={{ color, marginLeft: "-100%" }} />;
    default:
      return <AccessTime sx={{ color, marginLeft: "-100%" }} />;
  }
};

const MyTimelineComponent = ({ tasks }) => {
  // Sample data
  const [text, setText] = useState("");
  const [data, setData] = useState([]);
  const [page, setPage] = useState(1);
  const [maxPage, setMaxPage] = useState(1);

  useEffect(() => {
    let array = tasks.map((e, index) => {
      const date = new Date(e.CreatedDate);
      const day = String(date.getDate()).padStart(2, "0");
      const month = String(date.getMonth() + 1).padStart(2, "0"); // Months are zero-indexed
      const formattedDate = `${day}/${month}`;
      let format = "top";
      let color = "#7AAD67";
      let icon = e.Subject;
      if (e.Priority === "Priority") color = "#DD4040";
      let obj = { id: index, icon, date: formattedDate, color, format };
      return obj;
    });
    setText(array[0].date + " - " + array[array.length - 1].date);
    let maxPage = Math.ceil(array.length / 8);
    setPage(maxPage);
    setMaxPage(maxPage);
    setData(array);
  }, [tasks]);

  return (
    <div>
      <Typography
        variant="h2"
        align="center"
        sx={{
          fontFamily: "Albert Sans",
          fontWeight: 700,
          fontSize: "24px",
          lineHeight: "22.32px",
          letterSpacing: "-3%",
          paddingTop: 2,
          color: "#1E242F",
        }}
      >
        Timeline
      </Typography>
      <Typography
        variant="h2"
        align="center"
        sx={{
          fontFamily: "Albert Sans",
          fontSize: "18px",
          lineHeight: "22.32px",
          letterSpacing: "-3%",
          paddingTop: 1,
          paddingBottom: 4,
          color: "#4C4C4C",
        }}
      >
        {text}
      </Typography>
      <Box display="flex" justifyContent="center" alignItems="center">
        {/* Header */}
        <Box width="120px">
          {page > 1 && (
            <Box
              sx={{ cursor: "pointer" }}
              onClick={() => setPage(page - 1)}
              display="flex"
              alignItems="center"
              pb={6}
              mb={2}
              mx={2}
              height="80px"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="23"
                height="50"
                viewBox="0 0 23 50"
                fill="none"
              >
                <path d="M22 1L1 25.5L22 49.5" stroke="#4C4C4C" />
              </svg>
              <Typography
                sx={{ color: "#533AF3", marginLeft: "8px", cursor: "pointer" }}
              >
                Previous
              </Typography>
            </Box>
          )}
        </Box>

        {/* Timeline */}
        <Box
          sx={{ marginX: "20px" }}
          display="flex"
          flexGrow="1"
          alignItems="center"
          justifyContent="start"
        >
          <Box
            display="flex"
            flexDirection="column"
            alignItems="center"
            position="relative"
            justifyContent="center"
            sx={{ height: 200 }}
          >
            <Box
              sx={{
                height: "50px",
                marginTop: "34px",
                marginBottom: "8px",
                borderTop: "4px solid gray",
                width: "90px",
              }}
            />
          </Box>

          {data
            .filter((e, i) => i > (page - 1) * 8 && i <= page * 8)
            .map((el, index) => (
              <Box
                key={index}
                display="flex"
                flexDirection="column"
                alignItems="center"
                position="relative"
                justifyContent="center"
                sx={{ height: 200 }}
              >
                {el.format == "bottom" && index < data.length && (
                  <Box
                    sx={{
                      borderLeft: el.line || "1px dashed gray", // Dashed line between icons
                      height: "50px", // Adjust height of the dashed line
                      marginTop: "64px", // Adjust spacing between icon and dashed line
                      marginBottom: "8px", // Adjust spacing at the bottom
                      borderTop: "4px solid gray",
                      width: "90px",
                    }}
                  />
                )}
                {getIcon(el.icon, el.color)}
                {el.format == "top" && index < data.length && (
                  <Box
                    sx={{
                      borderLeft: el.line || "1px dashed gray", // Dashed line between icons
                      height: "50px", // Adjust height of the dashed line
                      marginTop: "8px", // Adjust spacing between icon and dashed line
                      marginBottom: "98px", // Adjust spacing at the bottom
                      borderBottom: "4px solid gray",
                      width: "90px",
                    }}
                  />
                )}
                {/* Date Below Icon */}
                <Typography
                  variant="caption"
                  align="center"
                  sx={{
                    textAlign: "center",
                    marginLeft: "-100%",
                    marginTop: "8px",
                    position: "absolute",
                    bottom: 0,
                  }}
                >
                  {el.line ? (
                    <b style={{ color: "gray" }}>
                      {el.label}
                      <br />
                    </b>
                  ) : (
                    <></>
                  )}{" "}
                  {el.date}
                </Typography>
              </Box>
            ))}
        </Box>
        <Box width="120px">
          {page < maxPage && (
            <Box
              sx={{ cursor: "pointer" }}
              onClick={() => setPage(page + 1)}
              display="flex"
              alignItems="center"
              gap="10px"
              pb={6}
              mb={2}
              mx={2}
              height="80px"
            >
              <Typography
                sx={{ color: "#533AF3", marginLeft: "8px", cursor: "pointer" }}
              >
                Next
              </Typography>
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="23"
                height="50"
                viewBox="0 0 23 50"
                fill="none"
              >
                <path
                  d="M22 1L1 25.5L22 49.5"
                  stroke="#4C4C4C"
                  transform="rotate(180 11.5 25)"
                />
              </svg>
            </Box>
          )}
        </Box>
      </Box>
    </div>
  );
};

export default MyTimelineComponent;
