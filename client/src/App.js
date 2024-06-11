import React from 'react';
import { BrowserRouter as Router } from 'react-router-dom';
import { Container, Box } from '@mui/material';
import Sidebar from './components/Sidebar/Sidebar';
import MainContent from './components/MainContent';
import './App.css';

function App() {
  return (
    <Router>
      <Container maxWidth="lg">
        <Box display="flex">
          <Sidebar />
          <MainContent />
        </Box>
      </Container>
    </Router>
  );
}

export default App;
