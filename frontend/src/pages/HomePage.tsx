import React from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';

const HomePage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <Box>
      <Typography variant="h3" component="h1" gutterBottom>
        Welcome to CK LangGraph App
      </Typography>
      
      <Typography variant="h6" color="text.secondary" paragraph>
        A powerful application combining React + Material-UI frontend with Python + LangGraph backend
      </Typography>

      <Grid container spacing={3} sx={{ mt: 2 }}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h5" component="h2" gutterBottom>
                Graph Processing
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Interact with LangGraph-powered backend for advanced graph processing and AI workflows.
              </Typography>
            </CardContent>
            <CardActions>
              <Button size="small" onClick={() => navigate('/graph')}>
                Go to Graph
              </Button>
            </CardActions>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h5" component="h2" gutterBottom>
                Card Kingdom Buylist
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Load and process Card Kingdom buylist data with 1.4M+ records. Transforms JSONP format and provides data analysis.
              </Typography>
            </CardContent>
            <CardActions>
              <Button size="small" onClick={() => navigate('/buylist')}>
                Process Buylist
              </Button>
            </CardActions>
          </Card>
        </Grid>
      </Grid>

      <Paper sx={{ p: 3, mt: 4 }}>
        <Typography variant="h6" gutterBottom>
          Getting Started
        </Typography>
        <Typography variant="body1">
          This application provides a modern interface for interacting with LangGraph workflows.
          Navigate to the Graph section to start working with your AI-powered graph processing.
        </Typography>
      </Paper>
    </Box>
  );
};

export default HomePage;