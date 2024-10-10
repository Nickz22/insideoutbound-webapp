import React from 'react';
import { Card, CardContent, Typography, Divider, Box } from '@mui/material';

const ActivatedContacts = ({ data }) => {
  const contacts = [
    { name: 'Contact Name 1', status: 'Activated', activities: 4 },
    { name: 'Contact Name 2', status: 'Engaged', activities: 2 },
    { name: 'Contact Name 3', status: 'Activated', activities: 0 },
    { name: 'Contact Name 4', status: 'Activated', activities: 4 },
    { name: 'Contact Name 5', status: 'Engaged', activities: 2 },
    { name: 'Contact Name 6', status: 'Activated', activities: 0 },
  ];

  return (
    <Card
      sx={{
        borderRadius: '20px',
        boxShadow: '0px 0px 25px rgba(0, 0, 0, 0.1)',
        padding: 2,
        maxWidth: 300,
        margin: 'auto',
        height: 626.34
      }}
    >
      <CardContent sx={{
        overflowY: 'auto', // Enable vertical scrolling
        maxHeight: '100%', // Ensure the content doesn't overflow outside the card
        paddingRight: 1,   // Add padding to avoid scrollbar overlap
      }}>
        <Typography variant="h2" align="center" sx={{
          fontFamily: 'Albert Sans',
          fontWeight: 700,
          fontSize: '24px',
          lineHeight: '22.32px',
          letterSpacing: '-3%',
          marginBottom: 2
        }}>
          Activated Contacts
        </Typography>

        {data.map(({ first_name, last_name }, index) => (
          <Box key={index}>
            <Typography
              variant="body1"
              align="center"
              sx={{ fontWeight: 700, color: '#FF6F00' }}
            >
              {first_name} {last_name}
            </Typography>
            <Box display="flex" justifyContent="space-between" mt={1}>
              <Box display="flex" flexDirection="column" justifyItems="center">
                <Typography variant="caption" align="center" >STATUS:</Typography>
                <Typography variant="body2" fontWeight="600" align="center">
                  Activated
                </Typography>
              </Box>
              <Box display="flex" flexDirection="column" justifyItems="center">
                <Typography variant="caption" align="center">TOTAL ACTIVITIES:</Typography>
                <Typography variant="body2" fontWeight="600" align="center">
                  3
                </Typography>
              </Box>
            </Box>
            {index < contacts.length - 1 && <Divider sx={{ marginY: 0.5 }} />}
          </Box>
        ))}
      </CardContent>
    </Card>
  );
};

export default ActivatedContacts;
