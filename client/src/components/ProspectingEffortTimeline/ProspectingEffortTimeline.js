import React from "react";
import { Box, Typography, Tooltip } from "@mui/material";
import { styled } from '@mui/material/styles';

const TimelineContainer = styled(Box)(() => ({
  display: 'flex',
  alignItems: 'center',
  width: '100%',
  height: '80px',
  position: 'relative',
  overflow: 'visible',
  padding: '0 60px', // Add padding to contain first and last labels
}));

const TimelineBar = styled(Box)(() => ({
  height: '4px',
  background: 'linear-gradient(90deg, #FF7D2F 0%, #491EFF 100%)',
  position: 'absolute',
  left: '60px',
  right: '60px',
  top: '50%',
  transform: 'translateY(-50%)',
}));

const TimelinePoint = styled(Box)(({ completed }) => ({
  width: '16px',
  height: '16px',
  borderRadius: '50%',
  background: completed ? 'linear-gradient(168deg, #FF7D2F 24.98%, #491EFF 97.93%)' : 'rgba(217, 217, 217, 1)',
  position: 'absolute',
  top: '50%',
  transform: 'translate(-50%, -50%)',
  zIndex: 1,
}));

const TimelineLabel = styled(Box)(() => ({
  position: 'absolute',
  top: '100%',
  left: '50%',
  transform: 'translateX(-50%)',
  textAlign: 'center',
  width: '120px',
}));

const TooltipContent = styled(Box)(({ theme }) => ({
  padding: theme.spacing(1),
}));

const getStatusColor = (status) => {
  switch (status.toLowerCase()) {
    case 'activated': return '#FF7D2F';
    case 'engaged': return '#FF9B5F';
    case 'meeting set': return '#FFC285';
    case 'opportunity created': return '#491EFF';
    default: return '#DD4040'; // Unresponsive or unknown status
  }
};

const ProspectingEffortTimeline = ({ efforts }) => {
  const sortedEfforts = efforts.sort((a, b) => new Date(a.date_entered) - new Date(b.date_entered));

  const renderTooltipContent = (effort) => (
    <TooltipContent>
      <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1 }}>
        {effort.status} - {new Date(effort.date_entered).toLocaleDateString()}
      </Typography>
      {effort.prospecting_metadata.map((metadata, index) => (
        <Typography key={index} variant="body2">
          {metadata.name}: {metadata.total}
        </Typography>
      ))}
    </TooltipContent>
  );

  return (
    <TimelineContainer>
      <TimelineBar />
      {sortedEfforts.map((effort, index) => {
        const position = index === 0 ? 0 : index === sortedEfforts.length - 1 ? 100 : (index / (sortedEfforts.length - 1)) * 100;
        
        return (
          <Tooltip key={index} title={renderTooltipContent(effort)} arrow>
            <Box sx={{ position: 'absolute', left: `calc(${position}% + ${index === 0 ? 60 : index === sortedEfforts.length - 1 ? -60 : 0}px)` }}>
              <TimelinePoint completed={true} sx={{ background: getStatusColor(effort.status) }} />
              <TimelineLabel>
                <Typography variant="caption" sx={{ fontWeight: 'bold', color: 'rgba(30, 36, 47, 1)' }}>
                  {effort.status}
                </Typography>
                <Typography variant="caption" display="block" sx={{ color: 'rgba(30, 36, 47, 0.7)' }}>
                  {new Date(effort.date_entered).toLocaleDateString()}
                </Typography>
              </TimelineLabel>
            </Box>
          </Tooltip>
        );
      })}
    </TimelineContainer>
  );
};

export default ProspectingEffortTimeline;
