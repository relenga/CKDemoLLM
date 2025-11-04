import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Box } from '@mui/material';
import Layout from './components/Layout';
import HomePage from './pages/HomePage';
import GraphPage from './pages/GraphPage';
import BuylistPage from './pages/BuylistPage';
import SelllistPage from './pages/SelllistPage';
import MatchingPage from './pages/MatchingPage';
import ConflictManagementPage from './pages/ConflictManagementPage';

function App() {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <Layout>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/graph" element={<GraphPage />} />
          <Route path="/buylist" element={<BuylistPage />} />
          <Route path="/selllist" element={<SelllistPage />} />
          <Route path="/matching" element={<MatchingPage />} />
          <Route path="/conflicts" element={<ConflictManagementPage />} />
        </Routes>
      </Layout>
    </Box>
  );
}

export default App;