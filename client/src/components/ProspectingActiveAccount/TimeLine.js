import { useEffect, useState } from "react";
import { Typography, Box, Tooltip } from "@mui/material";
import {
  AccessTime,
  Call,
  Message,
  Event,
  BusinessCenter,
} from "@mui/icons-material";

// Function to map icon names to actual icons
const getIcon = (iconName, color, total) => {
  let title = `${total} ${iconName}`;
  switch (iconName) {
    case "Message":
      return (
        <Tooltip title={title} placement="right-start">
          <Message sx={{ color, marginLeft: "-100%", background: "white" }} />
        </Tooltip>
      );
    case "Dial":
      return (
        <Tooltip title={title} placement="right-start">
          <Call sx={{ color, marginLeft: "-100%", background: "white" }} />
        </Tooltip>
      );
    case "Meeting":
      return (
        <Tooltip title={title} placement="right-start">
          <Event sx={{ color, marginLeft: "-100%", background: "white" }} />
        </Tooltip>
      );
    case "Opportunity":
      return (
        <Tooltip title={title} placement="right-start">
          <BusinessCenter
            sx={{ color, marginLeft: "-100%", background: "white" }}
          />
        </Tooltip>
      );
    default:
      return (
        <Tooltip title={title} placement="right-start">
          <AccessTime
            sx={{ color, marginLeft: "-100%", background: "white" }}
          />
        </Tooltip>
      );
  }
};

// Helper function to format the date
const formatDate = (dateStr) => {
  const date = new Date(dateStr);
  const year = date.getFullYear();
  const day = String(date.getDate()).padStart(2, "0");
  const month = String(date.getMonth() + 1).padStart(2, "0"); // Months are zero-indexed
  return `${day}/${month}/${year}`;
};

// Helper function to generate all dates for the past month
function generateDatesForLastMonth() {
  const now = new Date();
  const oneMonthAgo = new Date();
  oneMonthAgo.setDate(now.getDate() - 30); // Set the date 30 days ago

  const dates = [];
  let currentDate = new Date(oneMonthAgo);

  while (currentDate <= now) {
    dates.push(formatDate(currentDate));
    currentDate.setDate(currentDate.getDate() + 1); // Move to the next day
  }

  return dates;
}

const MyTimelineComponent = ({ tasks }) => {
  const [text, setText] = useState("");
  const [data, setData] = useState([]);
  const [page, setPage] = useState(1);
  const [maxPage, setMaxPage] = useState(1);

  useEffect(() => {
    const allDates = generateDatesForLastMonth();

    const result = allDates.map((formattedDate) => {
      // Find tasks for the current date
      const tasksForDate = tasks.filter(
        (task) => formatDate(new Date(task.CreatedDate)) === formattedDate
      );

      if (tasksForDate.length > 0) {
        // There are tasks for this date, process them as before
        const detail = [];
        let total = 0;
        let icons = [];
        let color = "#7AAD67"; // Default color

        tasksForDate.forEach((task) => {
          const icon = task.Subject;
          total++;
          color = task.Priority === "Priority" ? "#DD4040" : "#7AAD67"; // Set color based on Priority

          const detailEntry = detail.find((d) => d[0] === icon);
          if (detailEntry) {
            detailEntry[1]++;
          } else {
            detail.push([icon, 1]);
            icons.push(icon);
          }
        });

        return {
          total,
          detail,
          icons,
          date: formattedDate,
          color,
          format: "top",
        };
      } else {
        // No tasks for this date
        return {
          total: 0,
          detail: [],
          icons: [],
          date: formattedDate,
          color: "#7AAD67", // Default color
          format: "top",
        };
      }
    });

    // Update the state
    setData(result);
    setText(`${result[0].date} - ${result[result.length - 1].date}`);

    const maxPage = Math.ceil(result.length / 8);
    setPage(maxPage);
    setMaxPage(maxPage);
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
          justifyContent="center"
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
            .filter((e, i) => i >= (page - 1) * 8 && i <= page * 8)
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
                <Box
                  height="25px"
                  position="absolute"
                  top="0"
                  left="15%"
                  display="flex"
                  flexDirection="column"
                >
                  {el.detail.map((e) => getIcon(e[0], el.color, e[1]))}
                </Box>
                {el.format == "top" && index < data.length && (
                  <Box
                    sx={{
                      borderLeft: el.line || "1px dashed gray", // Dashed line between icons
                      height: "74px", // Adjust height of the dashed line
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
