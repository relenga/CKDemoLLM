import React, { useState } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Typography,
  CircularProgress,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Grid,
  Chip,
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  ExpandMore as ExpandMoreIcon,
  Assessment as AssessmentIcon,
} from '@mui/icons-material';

interface BuylistSummary {
  total_records: number;
  columns: string[];
  memory_usage_mb: number;
  sample_records: any[];
  statistics: { [key: string]: any };
}

interface BuylistResponse {
  status: string;
  message: string;
  total_records: number;
  processing_time?: number;
  summary?: BuylistSummary;
}

const BuylistPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<BuylistResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleUpload = async () => {
    setLoading(true);
    setError(null);
    setResponse(null);

    try {
      const apiResponse = await fetch('/api/buylist/upload', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url: 'https://www.cardkingdom.com/json/buylist.jsonp'
        }),
      });

      if (!apiResponse.ok) {
        throw new Error(`HTTP error! status: ${apiResponse.status}`);
      }

      const data: BuylistResponse = await apiResponse.json();
      setResponse(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const formatNumber = (num: number | undefined) => {
    if (num === undefined || num === null) return 'N/A';
    return new Intl.NumberFormat().format(num);
  };

  const formatBytes = (bytes: number) => {
    return `${(bytes).toFixed(2)} MB`;
  };

  return (
    <Box>
      <Typography variant="h3" component="h1" gutterBottom>
        Card Kingdom Buylist Processor
      </Typography>
      
      <Typography variant="h6" color="text.secondary" paragraph>
        Load and process Card Kingdom buylist data (1.4M+ records)
      </Typography>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Data Source Information
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            <strong>URL:</strong> https://www.cardkingdom.com/json/buylist.jsonp
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            <strong>Format:</strong> JSONP with approximately 1.4M records
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            <strong>Processing:</strong> Converts column names and data types for better readability
          </Typography>
          
          <Button
            variant="contained"
            size="large"
            startIcon={loading ? <CircularProgress size={20} /> : <UploadIcon />}
            onClick={handleUpload}
            disabled={loading}
            sx={{ mt: 2 }}
          >
            {loading ? 'Processing...' : 'Upload CK Buylist.jsonp'}
          </Button>
        </CardContent>
      </Card>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {response && (
        <Box>
          <Alert 
            severity={response.status === 'success' ? 'success' : 'error'} 
            sx={{ mb: 3 }}
          >
            {response.message}
            {response.processing_time && (
              <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                Processing time: {response.processing_time.toFixed(2)} seconds
              </Typography>
            )}
          </Alert>

          {response.summary && (
            <Box>
              {/* Summary Statistics */}
              <Card sx={{ mb: 3 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    <AssessmentIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                    Data Summary
                  </Typography>
                  
                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={6} md={3}>
                      <Paper sx={{ p: 2, textAlign: 'center' }}>
                        <Typography variant="h4" color="primary">
                          {formatNumber(response.summary.total_records)}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Total Records
                        </Typography>
                      </Paper>
                    </Grid>
                    
                    <Grid item xs={12} sm={6} md={3}>
                      <Paper sx={{ p: 2, textAlign: 'center' }}>
                        <Typography variant="h4" color="primary">
                          {response.summary.columns.length}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Columns
                        </Typography>
                      </Paper>
                    </Grid>
                    
                    <Grid item xs={12} sm={6} md={3}>
                      <Paper sx={{ p: 2, textAlign: 'center' }}>
                        <Typography variant="h4" color="primary">
                          {formatBytes(response.summary.memory_usage_mb)}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Memory Usage
                        </Typography>
                      </Paper>
                    </Grid>
                    
                    <Grid item xs={12} sm={6} md={3}>
                      <Paper sx={{ p: 2, textAlign: 'center' }}>
                        <Typography variant="h4" color="primary">
                          {response.processing_time?.toFixed(1)}s
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Processing Time
                        </Typography>
                      </Paper>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>

              {/* Columns */}
              <Accordion sx={{ mb: 2 }}>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="h6">
                    Data Columns ({response.summary.columns.length})
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                    {response.summary.columns.map((column, index) => (
                      <Chip key={index} label={column} variant="outlined" />
                    ))}
                  </Box>
                </AccordionDetails>
              </Accordion>

              {/* Sample Data */}
              <Accordion sx={{ mb: 2 }}>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="h6">
                    Sample Records ({response.summary.sample_records.length})
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <TableContainer component={Paper}>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          {response.summary.columns.map((column) => (
                            <TableCell key={column}>{column}</TableCell>
                          ))}
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {response.summary.sample_records.map((record, index) => (
                          <TableRow key={index}>
                            {response.summary!.columns.map((column) => (
                              <TableCell key={column}>
                                {record[column]?.toString() || 'N/A'}
                              </TableCell>
                            ))}
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </AccordionDetails>
              </Accordion>

              {/* Statistics */}
              {response.summary.statistics && Object.keys(response.summary.statistics).length > 0 && (
                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="h6">
                      Data Statistics
                    </Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Grid container spacing={2}>
                      {Object.entries(response.summary.statistics).map(([key, value]) => (
                        <Grid item xs={12} md={6} key={key}>
                          <Paper sx={{ p: 2 }}>
                            <Typography variant="subtitle1" gutterBottom>
                              {key}
                            </Typography>
                            <pre style={{ fontSize: '0.875rem', overflow: 'auto' }}>
                              {JSON.stringify(value, null, 2)}
                            </pre>
                          </Paper>
                        </Grid>
                      ))}
                    </Grid>
                  </AccordionDetails>
                </Accordion>
              )}
            </Box>
          )}
        </Box>
      )}
    </Box>
  );
};

export default BuylistPage;