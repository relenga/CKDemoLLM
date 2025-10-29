import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  TextField,
  Button,
  Card,
  CardContent,
  Grid,
  CircularProgress,
  Alert,
} from '@mui/material';
import { Send as SendIcon } from '@mui/icons-material';

interface GraphResponse {
  result: string;
  status: string;
  processing_time?: number;
}

const GraphPage: React.FC = () => {
  const [input, setInput] = useState('');
  const [response, setResponse] = useState<GraphResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!input.trim()) return;

    setLoading(true);
    setError(null);
    
    try {
      // This will connect to your Python backend
      const apiResponse = await fetch('/api/graph/process', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ input: input.trim() }),
      });

      if (!apiResponse.ok) {
        throw new Error(`HTTP error! status: ${apiResponse.status}`);
      }

      const data: GraphResponse = await apiResponse.json();
      setResponse(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && event.ctrlKey) {
      handleSubmit();
    }
  };

  return (
    <Box>
      <Typography variant="h3" component="h1" gutterBottom>
        LangGraph Processing
      </Typography>
      
      <Typography variant="h6" color="text.secondary" paragraph>
        Send input to the LangGraph backend for processing
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Input
            </Typography>
            
            <TextField
              fullWidth
              multiline
              rows={6}
              variant="outlined"
              placeholder="Enter your input here..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyPress}
              sx={{ mb: 2 }}
            />
            
            <Button
              variant="contained"
              startIcon={loading ? <CircularProgress size={20} /> : <SendIcon />}
              onClick={handleSubmit}
              disabled={loading || !input.trim()}
              fullWidth
            >
              {loading ? 'Processing...' : 'Send to LangGraph (Ctrl+Enter)'}
            </Button>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Response
            </Typography>
            
            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {error}
              </Alert>
            )}
            
            {response ? (
              <Card>
                <CardContent>
                  <Typography variant="body1" paragraph>
                    <strong>Result:</strong>
                  </Typography>
                  <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', mb: 2 }}>
                    {response.result}
                  </Typography>
                  
                  <Typography variant="caption" color="text.secondary">
                    Status: {response.status}
                    {response.processing_time && (
                      ` • Processing time: ${response.processing_time.toFixed(2)}s`
                    )}
                  </Typography>
                </CardContent>
              </Card>
            ) : (
              <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                No response yet. Send some input to see the LangGraph processing results.
              </Typography>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default GraphPage;