import React from "react";
import { Grid, Card, CardHeader, CardContent, Avatar, Typography, Link } from "@mui/material";
import PersonIcon from '@mui/icons-material/Person';
import { styled } from '@mui/material/styles';

// Look at this beautiful abomination
const BorderedCard = styled(Card)(({ theme }) => ({
  border: `2px solid ${theme.palette.divider}`,
  borderRadius: theme.shape.borderRadius,
  boxShadow: `0 0 10px ${theme.palette.action.hover}`,
  transition: 'box-shadow 0.3s ease-in-out',
  '&:hover': {
    boxShadow: `0 0 15px ${theme.palette.primary.light}`,
  },
}));

const ProspectingMetadataOverview = ({ activation, instanceUrl }) => {
  const getTaskCountForContact = (contactId, metadataName) => {
    const metadata = activation.prospecting_metadata.find(
      (m) => m.name === metadataName
    );
    if (!metadata) return 0;
    return metadata.tasks.filter((task) => task.WhoId === contactId).length;
  };

  return (
    <Grid container spacing={2}>
      {activation.active_contacts.map((contact) => (
        <Grid item xs={12} sm={6} md={4} key={contact.id}>
          <BorderedCard>
            <CardHeader
              avatar={
                <Avatar>
                  <PersonIcon />
                </Avatar>
              }
              title={
                <Link href={`${instanceUrl}/${contact.id}`} target="_blank" rel="noopener noreferrer">
                  {`${contact.first_name} ${contact.last_name}`}
                </Link>
              }
            />
            <CardContent>
              {activation.prospecting_metadata.map((metadata) => (
                <Typography key={metadata.name} variant="body2">
                  {metadata.name}: {getTaskCountForContact(contact.id, metadata.name)}
                </Typography>
              ))}
            </CardContent>
          </BorderedCard>
        </Grid>
      ))}
    </Grid>
  );
};

export default ProspectingMetadataOverview;
