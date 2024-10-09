import React from 'react';
import { Typography, Box } from '@mui/material';
import { AccessTime, Call, Message, Event, BusinessCenter } from '@mui/icons-material';

// Function to map icon names to actual icons
const getIcon = (iconName, color) => {
  switch (iconName) {
    case 'message':
      return <Message sx={{ color, marginLeft: "-100%" }} />;
    case 'call':
      return <Call sx={{ color, marginLeft: "-100%" }} />;
    case 'meeting':
      return <Event sx={{ color, marginLeft: "-100%" }} />;
    case 'opportunity':
      return <BusinessCenter sx={{ color, marginLeft: "-100%" }} />;
    default:
      return <AccessTime sx={{ color, marginLeft: "-100%" }} />;
  }
};

const MyTimelineComponent = () => {
  // Sample data
  const data = [
    { icon: "message", date: "11/02", color: "#DD4040", format: "top" },
    { icon: "call", date: "11/05", color: "#DD4040", format: "top" },
    { icon: "meeting", date: "11/07", color: "#DD4040", format: "top", line: '6px solid grey', label: "Activated" },
    { icon: "opportunity", date: "11/09", color: "#DD4040", format: "top" },
    { icon: "call", date: "11/13", color: "#7AAD67", format: "top", line: '6px solid grey', label: "Engaged" },
    { icon: "meeting", date: "11/14", color: "#7AAD67", format: "top" },
    { icon: "message", date: "11/17", color: "#7AAD67", format: "top" },
    { icon: "opportunity", date: "11/19", color: "#FF7D2F", format: "top", line: '6px solid grey', label: "Opportunity" },
    { icon: "", date: "11/24", color: "#533AF3", format: "top", },

  ];

  return (
    <div>
      <Typography variant="h2" align="center" sx={{
        fontFamily: 'Albert Sans',
        fontWeight: 700,
        fontSize: '24px',
        lineHeight: '22.32px',
        letterSpacing: '-3%',
        paddingTop: 2,
        color: "#1E242F"
      }}>
        Timeline
      </Typography>
      <Typography variant="h2" align="center" sx={{
        fontFamily: 'Albert Sans',
        fontSize: '18px',
        lineHeight: '22.32px',
        letterSpacing: '-3%',
        paddingTop: 1,
        paddingBottom: 4,
        color: "#4C4C4C"
      }}>
        [Date] - [Date]
      </Typography>
      <Box display="flex" justifyContent="center" alignItems="center">
        {/* Header */}
        <Box display="flex" alignItems="center" pb={6} mb={2} mx={2} height="80px">
          <svg xmlns="http://www.w3.org/2000/svg" width="23" height="50" viewBox="0 0 23 50" fill="none">
            <path d="M22 1L1 25.5L22 49.5" stroke="#4C4C4C" />
          </svg>
          <Typography sx={{ color: "#533AF3", marginLeft: '8px' }}>Previous<br />30 days</Typography>
        </Box>

        {/* Timeline */}
        <Box display="flex" flexGrow="1" alignItems="center" justifyContent="center">
          {
            data.map((el, index) => (
              <Box
                key={index}
                display="flex"
                flexDirection="column"
                alignItems="center"
                position="relative"
                justifyContent="center"
                sx={{ height: 200 }}
              >
                {
                  el.format == "bottom" && index < data.length && (
                    <Box
                      sx={{
                        borderLeft: el.line || '1px dashed gray', // Dashed line between icons
                        height: '50px',                // Adjust height of the dashed line
                        marginTop: '64px',               // Adjust spacing between icon and dashed line
                        marginBottom: '8px',            // Adjust spacing at the bottom
                        borderTop: '4px solid gray',
                        width: '100px'
                      }}
                    />
                  )
                }
                {getIcon(el.icon, el.color)}
                {
                  el.format == "top" && index < data.length && (
                    <Box
                      sx={{
                        borderLeft: el.line || '1px dashed gray', // Dashed line between icons
                        height: '50px',                // Adjust height of the dashed line
                        marginTop: '8px',               // Adjust spacing between icon and dashed line
                        marginBottom: '98px',            // Adjust spacing at the bottom
                        borderBottom: '4px solid gray',
                        width: '100px'

                      }}
                    />
                  )
                }
                {/* Date Below Icon */}
                <Typography variant="caption" align='center' sx={{ textAlign: 'center', marginLeft: "-100%", marginTop: '8px', position: 'absolute', bottom: 0 }}>{el.line ? <b style={{ color: "gray" }}>{el.label}<br /></b> : <></>} {el.date}</Typography>
              </Box>
            ))
          }
        </Box>
      </Box>
    </div>
  );
};

export default MyTimelineComponent;
