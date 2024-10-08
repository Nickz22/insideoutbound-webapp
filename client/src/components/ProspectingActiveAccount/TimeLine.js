import React from 'react';
import { Box, Typography } from '@mui/material';
import { Email, Phone, Handshake, BusinessCenter } from '@mui/icons-material';

// Example of event icons based on event type (message, call, etc.)
const iconMapper = {
  message: <Email style={{ color: '#e74c3c' }} />,
  call: <Phone style={{ color: '#e74c3c' }} />,
  meeting: <Handshake style={{ color: '#e67e22' }} />,
  opportunity: <BusinessCenter style={{ color: '#8e44ad' }} />
};

const TimelineEvent = ({ date, time, icon, title }) => {
  return (
    <Box textAlign="center" sx={{ margin: '0 20px' }}>
      {iconMapper[icon]}
      <Typography variant="body2">{`${date}`}</Typography>
      <Typography variant="body2">{title}</Typography>
      <Typography variant="body2" color="textSecondary">{time}</Typography>
    </Box>
  );
};

const Timeline = () => {
  const data = [
    { date: '11/02/23', time: '12:00', icon: 'message', title: 'Activated', style: 'A' },
    { date: '11/09/23', time: '14:00', icon: 'call', title: 'Engaged', style: 'B' },
    { date: '11/17/23', time: '16:00', icon: 'meeting', title: 'Meeting Set', style: 'C' },
    { date: '11/24/23', time: '18:00', icon: 'opportunity', title: 'Opportunity', style: 'D' }
  ];

  return (
    <Box display="flex" justifyContent="center" alignItems="center" padding="20px" position="relative" sx={{ overflowX: 'auto', whiteSpace: 'nowrap' }}>
      {data.map((event, index) => (
        <React.Fragment key={index}>
          <TimelineEvent
            date={event.date}
            time={event.time}
            icon={event.icon}
            title={event.title}
          />
          {index !== data.length - 1 && <Box sx={{ height: 1, width: 60, backgroundColor: '#ccc', margin: '0 20px' }} />}
        </React.Fragment>
      ))}
    </Box>
  );
};

// Sample data

const TimeLine = () => (
  <div>
    <Typography variant="h5" textAlign="center">Timeline</Typography>
    <Timeline />
  </div>
);

export default TimeLine;
