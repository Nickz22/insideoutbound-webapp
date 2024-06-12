import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Container, Box } from '@mui/material';
import Sidebar from './components/Sidebar/Sidebar';
import MainContent from './components/MainContent';
import Login from './pages/Login';
import './App.css';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/app" element={
          <Container maxWidth="lg">
            <Box display="flex">
              <Sidebar />
              <MainContent />
            </Box>
          </Container>
        } />
      </Routes>
    </Router>
  );
}

export default App;
