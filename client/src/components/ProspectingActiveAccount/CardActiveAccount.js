import React, { useEffect, useState } from 'react';
import { Card, CardContent, Typography, Divider, Box } from '@mui/material';

const ActivatedContacts = ({ data }) => {
  const [contacts, setContacts] = useState([])
  useEffect(() => {
    if (data) {
      let raw = data.active_contacts.map(e => {
        let { id, first_name, last_name } = e
        let len = data.tasks.filter(el => el.Contact.id === id)
        let obj = {
          id,
          name: first_name + " " + last_name,
          total: len.length,
          data: len,
          status: len[len.length - 1].Status
        }
        return obj
      })
      setContacts(raw)
    }
  }, [data])

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

        {contacts.map((el, index) => (
          <Box key={index}>
            <Typography
              variant="body1"
              align="center"
              sx={{ fontWeight: 700, color: '#FF6F00' }}
            >
              {el.name}
            </Typography>
            <Box display="flex" justifyContent="space-between" mt={1}>
              <Box display="flex" flexDirection="column" justifyItems="center">
                <Typography variant="caption" align="center" >STATUS:</Typography>
                <Typography variant="body2" fontWeight="600" align="center">
                  {el.status}
                </Typography>
              </Box>
              <Box display="flex" flexDirection="column" justifyItems="center">
                <Typography variant="caption" align="center">TOTAL ACTIVITIES:</Typography>
                <Typography variant="body2" fontWeight="600" align="center">
                  {el.total}
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
