import React, { useState, useRef } from 'react';
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
  LinearProgress,
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  ExpandMore as ExpandMoreIcon,
  Assessment as AssessmentIcon,
  FileUpload as FileUploadIcon,
  FilterList as FilterIcon,
} from '@mui/icons-material';

interface SelllistResponse {
  status: string;
  message: string;
  original_records: string;
  filtered_records: string;
  records_removed: string;
  processing_time?: number;
  process_time?: number;
  sample_records: any[];
  columns: string[];
  dataframe_stats: {
    status: string;
    records: number;
    columns: string[];
    memory_mb: number;
    dtypes: { [key: string]: string };
  };
  debug_info?: {
    memory_before_mb: number;
    memory_after_mb: number;
    memory_increase_mb: number;
    file_size_bytes: number;
    filename: string;
    file_type: string;
  };
}

const SelllistPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<SelllistResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const fileName = file.name.toLowerCase();
      if (!fileName.endsWith('.csv') && !fileName.endsWith('.xlsx') && !fileName.endsWith('.xls')) {
        setError('Please select a CSV or Excel file (.csv, .xlsx, .xls)');
        return;
      }
      setSelectedFile(file);
      setError(null);
      setResponse(null);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Please select a CSV or Excel file first');
      return;
    }

    setLoading(true);
    setError(null);
    setResponse(null);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const apiResponse = await fetch('/api/selllist/upload', {
        method: 'POST',
        body: formData,
      });

      if (!apiResponse.ok) {
        const errorData = await apiResponse.json();
        throw new Error(errorData.detail || `HTTP error! status: ${apiResponse.status}`);
      }

      const data: SelllistResponse = await apiResponse.json();
      setResponse(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleClearData = async () => {
    try {
      const apiResponse = await fetch('/api/selllist/clear', {
        method: 'DELETE',
      });

      if (!apiResponse.ok) {
        throw new Error(`HTTP error! status: ${apiResponse.status}`);
      }

      setResponse(null);
      setSelectedFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred';
      setError(errorMessage);
    }
  };

  const formatNumber = (numStr: string | number | undefined) => {
    if (numStr === undefined || numStr === null) return 'N/A';
    const num = typeof numStr === 'string' ? parseInt(numStr.replace(/,/g, '')) : numStr;
    return new Intl.NumberFormat().format(num);
  };

  const formatBytes = (bytes: number) => {
    return `${bytes.toFixed(2)} MB`;
  };

  const formatPrice = (price: any) => {
    if (price === undefined || price === null) return 'N/A';
    const numPrice = typeof price === 'string' ? parseFloat(price) : price;
    return `$${numPrice.toFixed(2)}`;
  };

  return (
    <Box>
      <Typography variant="h3" component="h1" gutterBottom>
        Vendor Selllist Processor
      </Typography>
      
      <Typography variant="h6" color="text.secondary" paragraph>
        Upload and process vendor CSV or Excel files with smart filtering
      </Typography>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            <FileUploadIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
            CSV File Upload
          </Typography>
          
          <Typography variant="body2" color="text.secondary" paragraph>
            <strong>Supported Formats:</strong> CSV (.csv) or Excel (.xlsx, .xls) files with 10 columns starting with TCGplayer Id, Product Line, Set Name, etc.
          </Typography>
          
          <Typography variant="body2" color="text.secondary" paragraph>
            <strong>Processing Rules:</strong>
          </Typography>
          <Box component="ul" sx={{ mt: 1, mb: 2, pl: 3 }}>
            <li>Removes rows with empty TCGplayer IDs</li>
            <li>Keeps only "Magic: The Gathering" products</li>
            <li>Maps column names to internal format</li>
          </Box>

          <input
            ref={fileInputRef}
            type="file"
            accept=".csv,.xlsx,.xls"
            onChange={handleFileSelect}
            style={{ display: 'none' }}
          />
          
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
            <Button
              variant="outlined"
              onClick={() => fileInputRef.current?.click()}
              startIcon={<FileUploadIcon />}
            >
              Select CSV/Excel File
            </Button>
            
            {selectedFile && (
              <Typography variant="body2" color="text.secondary">
                Selected: {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)
              </Typography>
            )}
          </Box>

          <Button
            variant="contained"
            size="large"
            startIcon={loading ? <CircularProgress size={20} /> : <UploadIcon />}
            onClick={handleUpload}
            disabled={loading || !selectedFile}
            sx={{ mt: 2, mr: 2 }}
          >
            {loading ? 'Processing...' : 'Upload & Process File'}
          </Button>

          {response && (
            <Button
              variant="outlined"
              color="secondary"
              onClick={handleClearData}
              sx={{ mt: 2 }}
            >
              Clear Data
            </Button>
          )}

          {loading && (
            <Box sx={{ mt: 2 }}>
              <LinearProgress />
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1 }}>
                Processing file...
              </Typography>
            </Box>
          )}
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

          {response.status === 'success' && (
            <Box>
              {/* Processing Results */}
              <Card sx={{ mb: 3 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    <FilterIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                    Processing Results
                  </Typography>
                  
                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={6} md={3}>
                      <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'info.light', color: 'info.contrastText' }}>
                        <Typography variant="h4">
                          {formatNumber(response.original_records)}
                        </Typography>
                        <Typography variant="body2">
                          Original Records
                        </Typography>
                      </Paper>
                    </Grid>
                    
                    <Grid item xs={12} sm={6} md={3}>
                      <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'success.light', color: 'success.contrastText' }}>
                        <Typography variant="h4">
                          {formatNumber(response.filtered_records)}
                        </Typography>
                        <Typography variant="body2">
                          Filtered Records
                        </Typography>
                      </Paper>
                    </Grid>
                    
                    <Grid item xs={12} sm={6} md={3}>
                      <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'warning.light', color: 'warning.contrastText' }}>
                        <Typography variant="h4">
                          {formatNumber(response.records_removed)}
                        </Typography>
                        <Typography variant="body2">
                          Records Removed
                        </Typography>
                      </Paper>
                    </Grid>
                    
                    <Grid item xs={12} sm={6} md={3}>
                      <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'primary.light', color: 'primary.contrastText' }}>
                        <Typography variant="h4">
                          {response.processing_time?.toFixed(1)}s
                        </Typography>
                        <Typography variant="body2">
                          Processing Time
                        </Typography>
                      </Paper>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>

              {/* Data Summary */}
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
                          {formatNumber(response.dataframe_stats?.records || 0)}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Active Records
                        </Typography>
                      </Paper>
                    </Grid>
                    
                    <Grid item xs={12} sm={6} md={3}>
                      <Paper sx={{ p: 2, textAlign: 'center' }}>
                        <Typography variant="h4" color="primary">
                          {response.dataframe_stats?.columns?.length || 0}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Columns
                        </Typography>
                      </Paper>
                    </Grid>
                    
                    <Grid item xs={12} sm={6} md={3}>
                      <Paper sx={{ p: 2, textAlign: 'center' }}>
                        <Typography variant="h4" color="primary">
                          {formatBytes(response.dataframe_stats?.memory_mb || 0)}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Memory Usage
                        </Typography>
                      </Paper>
                    </Grid>
                    
                    <Grid item xs={12} sm={6} md={3}>
                      <Paper sx={{ p: 2, textAlign: 'center' }}>
                        <Typography variant="h4" color="primary">
                          {response.debug_info ? `${(response.debug_info.file_size_bytes / 1024).toFixed(0)}KB` : 'N/A'}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          File Size
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
                    Data Columns ({response.columns?.length || 0})
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                    {(response.columns || []).map((column, index) => (
                      <Chip key={index} label={column} variant="outlined" />
                    ))}
                  </Box>
                </AccordionDetails>
              </Accordion>

              {/* Sample Data */}
              <Accordion sx={{ mb: 2 }}>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="h6">
                    Sample Records ({response.sample_records?.length || 0})
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <TableContainer component={Paper}>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          {(response.columns || []).map((column) => (
                            <TableCell key={column} sx={{ fontWeight: 'bold' }}>
                              {column}
                            </TableCell>
                          ))}
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {(response.sample_records || []).map((record, index) => (
                          <TableRow key={index}>
                            {(response.columns || []).map((column) => (
                              <TableCell key={column}>
                                {column.includes('Price') ? 
                                  formatPrice(record[column]) : 
                                  record[column]?.toString() || 'N/A'
                                }
                              </TableCell>
                            ))}
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </AccordionDetails>
              </Accordion>

              {/* Data Types */}
              <Accordion sx={{ mb: 2 }}>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="h6">
                    Column Data Types
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Grid container spacing={2}>
                    {Object.entries(response.dataframe_stats?.dtypes || {}).map(([column, dtype]) => (
                      <Grid item xs={12} sm={6} md={4} key={column}>
                        <Paper sx={{ p: 2 }}>
                          <Typography variant="subtitle2" gutterBottom>
                            {column}
                          </Typography>
                          <Chip label={dtype} size="small" variant="outlined" />
                        </Paper>
                      </Grid>
                    ))}
                  </Grid>
                </AccordionDetails>
              </Accordion>

              {/* Debug Information */}
              {response.debug_info && (
                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="h6">
                      Debug Information
                    </Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Grid container spacing={2}>
                      <Grid item xs={12} md={6}>
                        <Paper sx={{ p: 2 }}>
                          <Typography variant="subtitle1" gutterBottom>
                            Memory Usage
                          </Typography>
                          <Typography variant="body2">
                            Before: {response.debug_info.memory_before_mb.toFixed(1)} MB
                          </Typography>
                          <Typography variant="body2">
                            After: {response.debug_info.memory_after_mb.toFixed(1)} MB
                          </Typography>
                          <Typography variant="body2">
                            Increase: {response.debug_info.memory_increase_mb.toFixed(1)} MB
                          </Typography>
                        </Paper>
                      </Grid>
                      <Grid item xs={12} md={6}>
                        <Paper sx={{ p: 2 }}>
                          <Typography variant="subtitle1" gutterBottom>
                            File Information
                          </Typography>
                          <Typography variant="body2">
                            Name: {response.debug_info.filename}
                          </Typography>
                          <Typography variant="body2">
                            Size: {(response.debug_info.file_size_bytes / 1024).toFixed(1)} KB
                          </Typography>
                          <Typography variant="body2">
                            Type: {response.debug_info.file_type}
                          </Typography>
                        </Paper>
                      </Grid>
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

export default SelllistPage;