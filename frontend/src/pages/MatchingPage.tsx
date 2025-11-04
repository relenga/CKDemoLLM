import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Grid,
  TextField,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  LinearProgress,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Slider,
  FormControlLabel,
  Switch,
  Pagination,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Divider,
  Tooltip,
  IconButton
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  ExpandMore as ExpandMoreIcon,
  GetApp as DownloadIcon,
  Analytics as AnalyticsIcon,
  Settings as SettingsIcon,
  Tune as TuneIcon,
  Assessment as AssessmentIcon,
  Save as SaveIcon,
  Info as InfoIcon,
  Check as CheckIcon,
  Close as CloseIcon
} from '@mui/icons-material';

interface MatchResult {
  sell_index: number;
  buy_index: number;
  similarity_score: number;
  match_rank: number;
  sell_tcgplayer_id: number;
  sell_product_name: string;
  sell_set_name: string;
  sell_rarity: string;
  sell_market_price: number;
  sell_low_price?: number;
  sell_quantity: number;
  sell_condition?: string;
  sell_number?: string;
  buy_product_id?: number;
  buy_card_name?: string;
  buy_edition?: string;
  buy_rarity?: string;
  buy_price?: number;
  buy_quantity?: number;
  buy_foil?: string;
  buy_image?: string;
  decision_status?: string;
}

interface MatchStats {
  processing_time_seconds: number;
  total_selllist_items: number;
  total_buylist_items: number;
  total_matches_found: number;
  selllist_items_with_matches: number;
  match_coverage_percent: number;
  average_matches_per_item: number;
  confidence_distribution: {
    high: number;
    medium: number;
    low: number;
  };
  similarity_stats: {
    min: number;
    max: number;
    mean: number;
    median: number;
  };
}

interface SystemStatus {
  buylist_loaded: boolean;
  selllist_loaded: boolean;
  buylist_count: number;
  selllist_count: number;
  ready_for_matching: boolean;
  estimated_processing_time: string;
}

const MatchingPage: React.FC = () => {
  // State management
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [matches, setMatches] = useState<MatchResult[]>([]);
  const [stats, setStats] = useState<MatchStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Configuration state
  const [similarityThreshold, setSimilarityThreshold] = useState(0.3);
  const [maxMatchesPerItem, setMaxMatchesPerItem] = useState(5);
  const [returnStats, setReturnStats] = useState(true);
  const [autoAcceptThreshold, setAutoAcceptThreshold] = useState(0.9);
  const [skipDecidedItems, setSkipDecidedItems] = useState(true);
  
  // Advanced Configuration State
  // 1. Vectorizer Configuration
  const [maxFeatures, setMaxFeatures] = useState(10000);
  const [ngramMin, setNgramMin] = useState(1);
  const [ngramMax, setNgramMax] = useState(3);
  const [minDocFreq, setMinDocFreq] = useState(2);
  const [maxDocFreq, setMaxDocFreq] = useState(0.8);
  const [useCardNames, setUseCardNames] = useState(true);
  const [useSetNames, setUseSetNames] = useState(true);
  const [useRarity, setUseRarity] = useState(true);
  const [useFoilStatus, setUseFoilStatus] = useState(true);
  
  // 2. Algorithm Configuration
  const [algorithmType, setAlgorithmType] = useState('cosine_similarity');
  const [scoreNormalization, setScoreNormalization] = useState(true);
  const [confidenceWeighting, setConfidenceWeighting] = useState(false);
  
  // 3. Results Analysis Configuration
  const [showDistributionCharts, setShowDistributionCharts] = useState(true);
  const [enableFeedback, setEnableFeedback] = useState(false);
  const [compareResults, setCompareResults] = useState(false);
  
  // 4. Model Management Configuration
  const [modelName, setModelName] = useState('');
  const [autoSave, setAutoSave] = useState(false);
  const [selectedModel, setSelectedModel] = useState('current');
  
  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const [rowsPerPage] = useState(25);

  // Load system status on component mount
  useEffect(() => {
    checkSystemStatus();
  }, []);

  const checkSystemStatus = async () => {
    try {
      const response = await fetch('/api/matcher/status');
      const data = await response.json();
      if (data.status === 'success') {
        setSystemStatus(data.data);
      }
    } catch (err) {
      console.error('Error checking system status:', err);
      setError('Failed to check system status');
    }
  };

  const runMatching = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const params = new URLSearchParams({
        similarity_threshold: similarityThreshold.toString(),
        max_matches_per_item: maxMatchesPerItem.toString(),
        return_stats: returnStats.toString(),
        auto_accept_threshold: autoAcceptThreshold.toString(),
        skip_decided_items: skipDecidedItems.toString(),
        // Vectorizer parameters
        max_features: maxFeatures.toString(),
        ngram_min: ngramMin.toString(),
        ngram_max: ngramMax.toString(),
        min_doc_freq: minDocFreq.toString(),
        max_doc_freq: maxDocFreq.toString(),
        use_card_names: useCardNames.toString(),
        use_set_names: useSetNames.toString(),
        use_rarity: useRarity.toString(),
        use_foil_status: useFoilStatus.toString()
      });

      const response = await fetch(`/api/matcher/find_matches?${params}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      const data = await response.json();
      
      if (data.status === 'success') {
        setMatches(data.data.matches || []);
        setStats(data.data.statistics || null);
        setCurrentPage(1); // Reset to first page
      } else {
        setError(data.message || 'Matching failed');
      }
    } catch (err) {
      console.error('Error running matching:', err);
      setError('Failed to run matching');
    } finally {
      setLoading(false);
    }
  };

  const getConfidenceLevel = (similarity: number): { level: string; color: 'success' | 'warning' | 'error' } => {
    if (similarity >= 0.8) return { level: 'High', color: 'success' };
    if (similarity >= 0.5) return { level: 'Medium', color: 'warning' };
    return { level: 'Low', color: 'error' };
  };

  // Match decision functions
  const makeMatchDecision = async (sellIndex: number, buyIndex: number, decision: 'accept' | 'reject') => {
    try {
      setLoading(true);
      const response = await fetch('/api/matcher/decide', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sell_index: sellIndex,
          buy_index: buyIndex,
          decision: decision,
          user_notes: `Decision made on ${new Date().toLocaleString()}`
        })
      });

      const data = await response.json();
      if (data.status === 'success') {
        // Update the matches state to reflect the decision
        setMatches(prevMatches => 
          prevMatches.map(match => 
            match.sell_index === sellIndex && match.buy_index === buyIndex
              ? { 
                  ...match, 
                  decision_status: decision === 'accept' ? 'accepted' : 'rejected',
                  decision_saved: true // Mark as permanently saved
                }
              : match
          )
        );
        
        // After a successful decision, refresh matches to remove decided items
        if (skipDecidedItems) {
          setTimeout(() => {
            runMatching(); // Refresh the match results to filter out decided items
          }, 500);
        }
        
        setError(null);
      } else {
        setError(data.message || 'Failed to save decision');
      }
    } catch (err) {
      console.error('Error making decision:', err);
      setError('Failed to save decision');
    } finally {
      setLoading(false);
    }
  };

  // Download current run results to Excel
  const downloadCurrentRunResults = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/matcher/export/current-run/excel');
      
      if (!response.ok) {
        const errorData = await response.json();
        if (response.status === 404) {
          setError('No current run results to export. Please run part matching first.');
          return;
        }
        throw new Error(errorData.detail || 'Failed to download match data');
      }
      
      // Get the filename from the response headers
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = 'current_run_matches.xlsx';
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
        if (filenameMatch && filenameMatch[1]) {
          filename = filenameMatch[1].replace(/['"]/g, '');
        }
      }
      
      // Create blob and download
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      // Show success message
      setError(null);
      
    } catch (err) {
      console.error('Error downloading match data:', err);
      setError(err instanceof Error ? err.message : 'Failed to download match data');
    } finally {
      setLoading(false);
    }
  };

  // Download accumulated decisions from database to Excel
  const downloadAccumulatedDecisions = async () => {
    try {
      setLoading(true);
      console.log('Fetching accumulated decisions from /api/matcher/export/excel');
      const response = await fetch('/api/matcher/export/excel');
      
      console.log('Response status:', response.status);
      console.log('Response ok:', response.ok);
      
      if (!response.ok) {
        console.log('Response not ok, attempting to parse error');
        let errorData;
        try {
          errorData = await response.json();
          console.log('Error data:', errorData);
        } catch (parseError) {
          console.log('Failed to parse error response:', parseError);
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        if (response.status === 404) {
          setError('No accumulated decisions found to export. Please make some accept/reject decisions first.');
          return;
        }
        throw new Error(errorData.detail || 'Failed to download accumulated decisions');
      }
      
      // Get the filename from the response headers
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = 'accumulated_match_decisions.xlsx';
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
        if (filenameMatch && filenameMatch[1]) {
          filename = filenameMatch[1].replace(/['"]/g, '');
        }
      }
      
      // Create blob and download
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      // Show success message
      setError(null);
      
    } catch (err) {
      console.error('Error downloading accumulated decisions:', err);
      console.error('Error type:', typeof err);
      console.error('Error instanceof Error:', err instanceof Error);
      if (err instanceof Error) {
        console.error('Error message:', err.message);
        console.error('Error stack:', err.stack);
      }
      setError(err instanceof Error ? err.message : 'Failed to download accumulated decisions');
    } finally {
      setLoading(false);
    }
  };

  // Download matching errors to Excel
  const downloadMatchingErrors = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/matcher/export/matching-errors/excel');
      
      if (!response.ok) {
        const errorData = await response.json();
        if (response.status === 404) {
          setError('No matching errors found to export.');
          return;
        }
        throw new Error(errorData.detail || 'Failed to download matching errors');
      }
      
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = 'matching_errors.xlsx';
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
        if (filenameMatch && filenameMatch[1]) {
          filename = filenameMatch[1].replace(/['"]/g, '');
        }
      }
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      setError(null);
    } catch (err) {
      console.error('Error downloading matching errors:', err);
      setError(err instanceof Error ? err.message : 'Failed to download matching errors');
    } finally {
      setLoading(false);
    }
  };

  // Download non-matches to Excel
  const downloadNonMatches = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/matcher/export/non-matches/excel');
      
      if (!response.ok) {
        const errorData = await response.json();
        if (response.status === 404) {
          setError('No non-matches found to export.');
          return;
        }
        throw new Error(errorData.detail || 'Failed to download non-matches');
      }
      
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = 'non_matches.xlsx';
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
        if (filenameMatch && filenameMatch[1]) {
          filename = filenameMatch[1].replace(/['"]/g, '');
        }
      }
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      setError(null);
    } catch (err) {
      console.error('Error downloading non-matches:', err);
      setError(err instanceof Error ? err.message : 'Failed to download non-matches');
    } finally {
      setLoading(false);
    }
  };

  // Download match sessions to Excel
  const downloadMatchSessions = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/matcher/export/match-sessions/excel');
      
      if (!response.ok) {
        const errorData = await response.json();
        if (response.status === 404) {
          setError('No match sessions found to export.');
          return;
        }
        throw new Error(errorData.detail || 'Failed to download match sessions');
      }
      
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = 'match_sessions.xlsx';
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
        if (filenameMatch && filenameMatch[1]) {
          filename = filenameMatch[1].replace(/['"]/g, '');
        }
      }
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      setError(null);
    } catch (err) {
      console.error('Error downloading match sessions:', err);
      setError(err instanceof Error ? err.message : 'Failed to download match sessions');
    } finally {
      setLoading(false);
    }
  };

  const getDecisionStatus = (match: MatchResult): string => {
    return (match as any).decision_status || 'pending';
  };

  const getDecisionChip = (status: string) => {
    switch (status) {
      case 'accepted':
        return <Chip label="MATCHED" color="success" size="small" />;
      case 'auto_accepted':
        return <Chip label="AUTO-MATCHED" color="success" size="small" variant="outlined" />;
      case 'rejected':
        return <Chip label="EXCLUDED" color="error" size="small" />;
      case 'auto_rejected':
        return <Chip label="AUTO-EXCLUDED" color="error" size="small" variant="outlined" />;
      default:
        return <Chip label="PENDING" color="default" size="small" />;
    }
  };

  // Group matches by selllist item to show all buyers for each sell item
  const groupMatchesBySellItem = (matches: MatchResult[]) => {
    const groups: { [key: string]: MatchResult[] } = {};
    matches.forEach(match => {
      const key = `${match.sell_index}_${match.sell_tcgplayer_id}`;
      if (!groups[key]) {
        groups[key] = [];
      }
      groups[key].push(match);
    });
    // Sort each group by similarity score (highest first)
    Object.values(groups).forEach(group => {
      group.sort((a, b) => b.similarity_score - a.similarity_score);
    });
    return Object.values(groups);
  };

  // Pagination logic
  const startIndex = (currentPage - 1) * rowsPerPage;
  const endIndex = startIndex + rowsPerPage;
  const paginatedMatches = matches.slice(startIndex, endIndex);
  const groupedMatches = groupMatchesBySellItem(paginatedMatches);
  const totalPages = Math.ceil(matches.length / rowsPerPage);

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom sx={{ mb: 4 }}>
        Part Matching Engine
      </Typography>

      {/* System Status Card */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            System Status
          </Typography>
          {systemStatus ? (
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <Typography variant="body2">BuyList Status:</Typography>
                  <Chip 
                    label={systemStatus.buylist_loaded ? `${systemStatus.buylist_count.toLocaleString()} records` : 'Not loaded'}
                    color={systemStatus.buylist_loaded ? 'success' : 'error'}
                    size="small"
                  />
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <Typography variant="body2">SellList Status:</Typography>
                  <Chip 
                    label={systemStatus.selllist_loaded ? `${systemStatus.selllist_count.toLocaleString()} records` : 'Not loaded'}
                    color={systemStatus.selllist_loaded ? 'success' : 'error'}
                    size="small"
                  />
                </Box>
              </Grid>
              <Grid item xs={12} md={6}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <Typography variant="body2">Ready for Matching:</Typography>
                  <Chip 
                    label={systemStatus.ready_for_matching ? 'Ready' : 'Not Ready'}
                    color={systemStatus.ready_for_matching ? 'success' : 'error'}
                    size="small"
                  />
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Typography variant="body2">Est. Processing Time:</Typography>
                  <Typography variant="body2" color="text.secondary">
                    {systemStatus.estimated_processing_time}
                  </Typography>
                </Box>
              </Grid>
            </Grid>
          ) : (
            <Typography color="text.secondary">Loading system status...</Typography>
          )}
        </CardContent>
      </Card>

      {/* Match Data Downloads Section */}
      <Accordion sx={{ mb: 2 }}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <DownloadIcon color="primary" />
            <Typography variant="h6">Match Data Downloads</Typography>
            <Tooltip title="Export all database tables to Excel format for analysis and record keeping">
              <IconButton size="small">
                <InfoIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle1" gutterBottom>Primary Match Data</Typography>
              
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mb: 2 }}>
                <Box>
                  <Button
                    variant="contained"
                    color="primary"
                    startIcon={<DownloadIcon />}
                    onClick={downloadCurrentRunResults}
                    disabled={loading}
                    fullWidth
                  >
                    Current Run Results
                  </Button>
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                    Results from the most recent matching run only (not accumulated)
                  </Typography>
                </Box>
                
                <Box>
                  <Button
                    variant="outlined"
                    color="primary"
                    startIcon={<DownloadIcon />}
                    onClick={downloadAccumulatedDecisions}
                    disabled={loading}
                    fullWidth
                  >
                    Accumulated Decisions
                  </Button>
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                    All accept/reject decisions saved to database across all runs
                  </Typography>
                </Box>
                
                <Box>
                  <Button
                    variant="outlined"
                    color="primary"
                    startIcon={<DownloadIcon />}
                    onClick={downloadMatchingErrors}
                    disabled={loading}
                    fullWidth
                  >
                    Matching Errors
                  </Button>
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                    Conflicts and errors during matching process for troubleshooting
                  </Typography>
                </Box>
              </Box>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle1" gutterBottom>Supporting Data</Typography>
              
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mb: 2 }}>
                <Box>
                  <Button
                    variant="outlined"
                    color="primary"
                    startIcon={<DownloadIcon />}
                    onClick={downloadNonMatches}
                    disabled={loading}
                    fullWidth
                  >
                    Non-Matches
                  </Button>
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                    User-rejected pairs to prevent future suggestions
                  </Typography>
                </Box>
                
                <Box>
                  <Button
                    variant="outlined"
                    color="primary"
                    startIcon={<DownloadIcon />}
                    onClick={downloadMatchSessions}
                    disabled={loading}
                    fullWidth
                  >
                    Match Sessions
                  </Button>
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                    Session metadata with processing times and configuration settings
                  </Typography>
                </Box>
              </Box>
            </Grid>
          </Grid>
        </AccordionDetails>
      </Accordion>

      {/* Basic Configuration Panel */}
      <Accordion sx={{ mb: 2 }}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6">Basic Matching Configuration</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Typography gutterBottom>
                Similarity Threshold: {similarityThreshold.toFixed(2)}
              </Typography>
              <Slider
                value={similarityThreshold}
                onChange={(_, value) => setSimilarityThreshold(value as number)}
                min={0.1}
                max={1.0}
                step={0.05}
                marks={[
                  { value: 0.1, label: '0.1' },
                  { value: 0.5, label: '0.5' },
                  { value: 0.8, label: '0.8' },
                  { value: 1.0, label: '1.0' }
                ]}
                sx={{ mt: 2, mb: 2 }}
              />
              <Typography variant="caption" color="text.secondary">
                Higher values = more strict matching (fewer, but higher quality matches)
              </Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                label="Max Matches Per Item"
                type="number"
                value={maxMatchesPerItem}
                onChange={(e) => setMaxMatchesPerItem(parseInt(e.target.value) || 1)}
                inputProps={{ min: 1, max: 20 }}
                fullWidth
                sx={{ mb: 2 }}
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={returnStats}
                    onChange={(e) => setReturnStats(e.target.checked)}
                  />
                }
                label="Include detailed statistics"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography gutterBottom>
                Auto-Accept Threshold: {(autoAcceptThreshold * 100).toFixed(0)}%
              </Typography>
              <Slider
                value={autoAcceptThreshold}
                onChange={(_, value) => setAutoAcceptThreshold(value as number)}
                min={0.5}
                max={1.0}
                step={0.05}
                marks={[
                  { value: 0.5, label: '50%' },
                  { value: 0.7, label: '70%' },
                  { value: 0.9, label: '90%' },
                  { value: 1.0, label: '100%' }
                ]}
                sx={{ mt: 2, mb: 2 }}
              />
              <Typography variant="caption" color="text.secondary">
                Matches above this threshold will be automatically accepted
              </Typography>
              
              <Box sx={{ mt: 2 }}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={skipDecidedItems}
                      onChange={(e) => setSkipDecidedItems(e.target.checked)}
                    />
                  }
                  label="Skip items with existing decisions"
                />
              </Box>
            </Grid>
          </Grid>
        </AccordionDetails>
      </Accordion>

      {/* Advanced Configuration Sections */}
      
      {/* 1. Vectorizer Configuration (Priority 1) */}
      <Accordion sx={{ mb: 2 }}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <TuneIcon color="primary" />
            <Typography variant="h6">Vectorizer & Feature Engineering</Typography>
            <Tooltip title="Configure how text is converted to numerical features for matching">
              <IconButton size="small">
                <InfoIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle1" gutterBottom>TF-IDF Configuration</Typography>
              
              <Typography gutterBottom>Max Features: {maxFeatures.toLocaleString()}</Typography>
              <Slider
                value={maxFeatures}
                onChange={(_, value) => setMaxFeatures(value as number)}
                min={1000}
                max={50000}
                step={1000}
                marks={[
                  { value: 1000, label: '1K' },
                  { value: 10000, label: '10K' },
                  { value: 25000, label: '25K' },
                  { value: 50000, label: '50K' }
                ]}
                sx={{ mb: 3 }}
              />
              
              <Typography gutterBottom>N-gram Range: ({ngramMin}, {ngramMax})</Typography>
              <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
                <TextField
                  label="Min N-gram"
                  type="number"
                  value={ngramMin}
                  onChange={(e) => setNgramMin(Math.max(1, parseInt(e.target.value) || 1))}
                  inputProps={{ min: 1, max: 5 }}
                  size="small"
                  sx={{ width: 120 }}
                />
                <TextField
                  label="Max N-gram"
                  type="number"
                  value={ngramMax}
                  onChange={(e) => setNgramMax(Math.max(ngramMin, parseInt(e.target.value) || 1))}
                  inputProps={{ min: ngramMin, max: 5 }}
                  size="small"
                  sx={{ width: 120 }}
                />
              </Box>

              <Typography gutterBottom>Document Frequency Thresholds</Typography>
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" gutterBottom>Min Doc Frequency: {minDocFreq}</Typography>
                <Slider
                  value={minDocFreq}
                  onChange={(_, value) => setMinDocFreq(value as number)}
                  min={1}
                  max={100}
                  step={1}
                  sx={{ mb: 2 }}
                />
                <Typography variant="body2" gutterBottom>Max Doc Frequency: {maxDocFreq.toFixed(2)}</Typography>
                <Slider
                  value={maxDocFreq}
                  onChange={(_, value) => setMaxDocFreq(value as number)}
                  min={0.1}
                  max={1.0}
                  step={0.05}
                />
              </Box>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle1" gutterBottom>Feature Selection</Typography>
              
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, mb: 2 }}>
                <FormControlLabel
                  control={<Switch checked={useCardNames} onChange={(e) => setUseCardNames(e.target.checked)} />}
                  label="Include Card Names"
                />
                <FormControlLabel
                  control={<Switch checked={useSetNames} onChange={(e) => setUseSetNames(e.target.checked)} />}
                  label="Include Set Names"
                />
                <FormControlLabel
                  control={<Switch checked={useRarity} onChange={(e) => setUseRarity(e.target.checked)} />}
                  label="Include Rarity"
                />
                <FormControlLabel
                  control={<Switch checked={useFoilStatus} onChange={(e) => setUseFoilStatus(e.target.checked)} />}
                  label="Include Foil Status"
                />
              </Box>
              
              <Divider sx={{ my: 2 }} />
              <Typography variant="caption" color="text.secondary">
                Feature engineering controls how card information is processed for matching. 
                More features can improve accuracy but increase processing time.
              </Typography>
            </Grid>
          </Grid>
        </AccordionDetails>
      </Accordion>

      {/* 2. Algorithm Configuration (Priority 2) */}
      <Accordion sx={{ mb: 2 }}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <SettingsIcon color="primary" />
            <Typography variant="h6">Algorithm Comparison & Selection</Typography>
            <Tooltip title="Choose and configure different matching algorithms">
              <IconButton size="small">
                <InfoIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Similarity Algorithm</InputLabel>
                <Select
                  value={algorithmType}
                  label="Similarity Algorithm"
                  onChange={(e) => setAlgorithmType(e.target.value)}
                >
                  <MenuItem value="cosine_similarity">Cosine Similarity (Current)</MenuItem>
                  <MenuItem value="euclidean_distance">Euclidean Distance</MenuItem>
                  <MenuItem value="manhattan_distance">Manhattan Distance</MenuItem>
                  <MenuItem value="jaccard_similarity">Jaccard Similarity</MenuItem>
                  <MenuItem value="hybrid_scoring">Hybrid Scoring</MenuItem>
                </Select>
              </FormControl>
              
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                <FormControlLabel
                  control={<Switch checked={scoreNormalization} onChange={(e) => setScoreNormalization(e.target.checked)} />}
                  label="Score Normalization"
                />
                <FormControlLabel
                  control={<Switch checked={confidenceWeighting} onChange={(e) => setConfidenceWeighting(e.target.checked)} />}
                  label="Confidence Weighting"
                />
              </Box>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle1" gutterBottom>Algorithm Comparison</Typography>
              <Button variant="outlined" fullWidth sx={{ mb: 1 }} disabled>
                Run A/B Comparison (Coming Soon)
              </Button>
              <Button variant="outlined" fullWidth sx={{ mb: 1 }} disabled>
                Performance Benchmarks (Coming Soon)
              </Button>
              <Button variant="outlined" fullWidth disabled>
                Statistical Analysis (Coming Soon)
              </Button>
              
              <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
                Compare different algorithms side-by-side to find the best approach for your data.
              </Typography>
            </Grid>
          </Grid>
        </AccordionDetails>
      </Accordion>

      {/* 3. Results Analysis (Priority 3) */}
      <Accordion sx={{ mb: 2 }}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <AssessmentIcon color="primary" />
            <Typography variant="h6">Results Analysis & Feedback</Typography>
            <Tooltip title="Advanced analytics and feedback tools for result evaluation">
              <IconButton size="small">
                <InfoIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle1" gutterBottom>Visualization Options</Typography>
              
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, mb: 2 }}>
                <FormControlLabel
                  control={<Switch checked={showDistributionCharts} onChange={(e) => setShowDistributionCharts(e.target.checked)} />}
                  label="Show Distribution Charts"
                />
                <FormControlLabel
                  control={<Switch checked={enableFeedback} onChange={(e) => setEnableFeedback(e.target.checked)} />}
                  label="Enable Manual Feedback"
                />
                <FormControlLabel
                  control={<Switch checked={compareResults} onChange={(e) => setCompareResults(e.target.checked)} />}
                  label="Compare Multiple Results"
                />
              </Box>
              
              <Button variant="outlined" fullWidth sx={{ mb: 1 }} disabled>
                Generate Match Report (Coming Soon)
              </Button>
              <Button variant="outlined" fullWidth disabled>
                Export Analytics Data (Coming Soon)
              </Button>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle1" gutterBottom>Quality Metrics</Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Advanced analytics coming soon:
              </Typography>
              <Box component="ul" sx={{ mt: 1, pl: 2 }}>
                <Typography component="li" variant="body2" color="text.secondary">
                  Similarity Score Histograms
                </Typography>
                <Typography component="li" variant="body2" color="text.secondary">
                  Coverage Analysis by Category
                </Typography>
                <Typography component="li" variant="body2" color="text.secondary">
                  False Positive Detection
                </Typography>
                <Typography component="li" variant="body2" color="text.secondary">
                  Manual Feedback Integration
                </Typography>
              </Box>
            </Grid>
          </Grid>
        </AccordionDetails>
      </Accordion>

      {/* 4. Model Management (Priority 4) */}
      <Accordion sx={{ mb: 3 }}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <SaveIcon color="primary" />
            <Typography variant="h6">Model Management & Persistence</Typography>
            <Tooltip title="Save, load, and manage different model configurations">
              <IconButton size="small">
                <InfoIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle1" gutterBottom>Save Current Configuration</Typography>
              
              <TextField
                label="Model Name"
                value={modelName}
                onChange={(e) => setModelName(e.target.value)}
                fullWidth
                sx={{ mb: 2 }}
                placeholder="e.g., High_Precision_Config_v1"
              />
              
              <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                <Button variant="contained" disabled sx={{ flex: 1 }}>
                  Save Configuration
                </Button>
                <Button variant="outlined" disabled>
                  Export
                </Button>
              </Box>
              
              <FormControlLabel
                control={<Switch checked={autoSave} onChange={(e) => setAutoSave(e.target.checked)} />}
                label="Auto-save successful configurations"
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle1" gutterBottom>Load Saved Configuration</Typography>
              
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Saved Models</InputLabel>
                <Select
                  value={selectedModel}
                  label="Saved Models"
                  onChange={(e) => setSelectedModel(e.target.value)}
                >
                  <MenuItem value="current">Current Configuration</MenuItem>
                  <MenuItem value="default">Default Settings</MenuItem>
                  <MenuItem value="high_precision" disabled>High Precision (Coming Soon)</MenuItem>
                  <MenuItem value="balanced" disabled>Balanced (Coming Soon)</MenuItem>
                  <MenuItem value="fast_matching" disabled>Fast Matching (Coming Soon)</MenuItem>
                </Select>
              </FormControl>
              
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button variant="outlined" fullWidth disabled>
                  Load Configuration
                </Button>
                <Button variant="outlined" color="error" disabled>
                  Delete
                </Button>
              </Box>
              
              <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
                Configurations will be saved to database for team sharing.
              </Typography>
            </Grid>
          </Grid>
        </AccordionDetails>
      </Accordion>

      {/* Action Button */}
      <Box sx={{ mb: 3 }}>
        <Button
          variant="contained"
          size="large"
          startIcon={loading ? null : <PlayIcon />}
          onClick={runMatching}
          disabled={loading || !systemStatus?.ready_for_matching}
          sx={{ mr: 2 }}
        >
          {loading ? 'Running Matching...' : 'Run Part Matching'}
        </Button>
        

      </Box>

      {loading && <LinearProgress sx={{ mb: 2 }} />}

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Statistics Panel */}
      {stats && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <AnalyticsIcon />
              Matching Statistics
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} md={3}>
                <Typography variant="h4" color="primary">
                  {stats.total_matches_found.toLocaleString()}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Total Matches
                </Typography>
              </Grid>
              <Grid item xs={12} md={3}>
                <Typography variant="h4" color="primary">
                  {stats.match_coverage_percent.toFixed(1)}%
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Coverage Rate
                </Typography>
              </Grid>
              <Grid item xs={12} md={3}>
                <Typography variant="h4" color="primary">
                  {stats.average_matches_per_item.toFixed(1)}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Avg Matches/Item
                </Typography>
              </Grid>
              <Grid item xs={12} md={3}>
                <Typography variant="h4" color="primary">
                  {stats.processing_time_seconds.toFixed(1)}s
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Processing Time
                </Typography>
              </Grid>
              <Grid item xs={12}>
                <Box sx={{ display: 'flex', gap: 1, mt: 2 }}>
                  <Chip label={`High: ${(stats.confidence_distribution.high || 0).toLocaleString()}`} color="success" size="small" />
                  <Chip label={`Medium: ${(stats.confidence_distribution.medium || 0).toLocaleString()}`} color="warning" size="small" />
                  <Chip label={`Low: ${(stats.confidence_distribution.low || 0).toLocaleString()}`} color="error" size="small" />
                </Box>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Results Table */}
      {matches.length > 0 && (
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">
                Match Results ({matches.length.toLocaleString()} matches)
              </Typography>
              <Pagination
                count={totalPages}
                page={currentPage}
                onChange={(_, page) => setCurrentPage(page)}
                color="primary"
              />
            </Box>
            
            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell><strong>Group</strong></TableCell>
                    <TableCell><strong>Type/Rank</strong></TableCell>
                    <TableCell><strong>Product ID</strong></TableCell>
                    <TableCell><strong>Card Name</strong></TableCell>
                    <TableCell><strong>Rarity/Condition</strong></TableCell>
                    <TableCell><strong>Pricing</strong></TableCell>
                    <TableCell><strong>Image</strong></TableCell>
                    <TableCell><strong>Quantity</strong></TableCell>
                    <TableCell><strong>Similarity</strong></TableCell>
                    <TableCell><strong>Status</strong></TableCell>
                    <TableCell><strong>Actions</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {groupedMatches.map((sellGroup, groupIndex) => {
                    const firstMatch = sellGroup[0]; // Use first match for sell info
                    const buyMatches = sellGroup; // All matches are buy matches for this sell item
                    
                    return [
                      // Sell Item Header Row
                      <TableRow 
                        key={`sellgroup-${groupIndex}-header`}
                        sx={{ backgroundColor: '#fff3e0', '& td': { fontWeight: 'bold' } }}
                      >
                        <TableCell rowSpan={buyMatches.length + 1} sx={{ verticalAlign: 'top', fontWeight: 'bold' }}>
                          <Typography variant="h6" color="secondary">
                            SELL #{groupIndex + 1}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip label="SELLLIST" color="secondary" size="small" />
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" sx={{ fontFamily: 'monospace', fontWeight: 'bold' }}>
                            {firstMatch.sell_tcgplayer_id || 'N/A'}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
                            {firstMatch.sell_product_name || 'N/A'}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {firstMatch.sell_set_name || 'N/A'}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                            {firstMatch.sell_rarity || 'N/A'}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {firstMatch.sell_condition || 'Condition N/A'}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body1" sx={{ fontWeight: 'bold', color: 'warning.main' }}>
                            ${firstMatch.sell_market_price?.toFixed(2) || 'N/A'}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Low: ${firstMatch.sell_low_price?.toFixed(2) || 'N/A'}
                          </Typography>
                        </TableCell>
                        <TableCell rowSpan={buyMatches.length + 1} sx={{ verticalAlign: 'middle', textAlign: 'center', padding: '8px' }}>
                          {buyMatches.length > 0 && buyMatches[0].buy_image ? (
                            <Tooltip title={`Image: ${buyMatches[0].buy_image}`} arrow>
                              <Box
                                component="img"
                                src={`https://www.cardkingdom.com${buyMatches[0].buy_image}`}
                                alt={buyMatches[0].buy_card_name || 'Card image'}
                                sx={{
                                  width: 60,
                                  height: 84,
                                  objectFit: 'contain',
                                  border: '1px solid #ddd',
                                  borderRadius: '4px',
                                  backgroundColor: '#f9f9f9'
                                }}
                                onError={(e) => {
                                  const target = e.target as HTMLImageElement;
                                  target.style.display = 'none';
                                  const parent = target.parentElement;
                                  if (parent) {
                                    parent.innerHTML = `<div style="width: 60px; height: 84px; display: flex; align-items: center; justify-content: center; border: 1px solid #ddd; border-radius: 4px; background-color: #f9f9f9; color: #666; font-size: 10px; text-align: center;">No Image</div>`;
                                  }
                                }}
                              />
                            </Tooltip>
                          ) : (
                            <Box sx={{
                              width: 60,
                              height: 84,
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              border: '1px solid #ddd',
                              borderRadius: '4px',
                              backgroundColor: '#f9f9f9',
                              color: 'text.secondary'
                            }}>
                              <Typography variant="caption" sx={{ fontSize: '10px', textAlign: 'center' }}>
                                No Image
                              </Typography>
                            </Box>
                          )}
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                            {firstMatch.sell_number || firstMatch.sell_quantity?.toLocaleString() || 'N/A'}
                          </Typography>
                        </TableCell>
                        <TableCell sx={{ backgroundColor: 'grey.100' }}>
                          <Typography variant="caption" color="text.secondary">
                            BUYERS
                          </Typography>
                        </TableCell>
                        <TableCell sx={{ backgroundColor: 'grey.100' }}>
                          <Typography variant="caption" color="text.secondary">
                            STATUS
                          </Typography>
                        </TableCell>
                        <TableCell sx={{ backgroundColor: 'grey.100' }}>
                          <Typography variant="caption" color="text.secondary">
                            ACTIONS
                          </Typography>
                        </TableCell>
                      </TableRow>,
                      
                      // Buy Item Rows (potential buyers for this sell item)
                      ...buyMatches.map((match, buyIndex) => {
                        const confidence = getConfidenceLevel(match.similarity_score);
                        return (
                          <TableRow 
                            key={`buymatch-${groupIndex}-${buyIndex}`}
                            sx={{ backgroundColor: buyIndex % 2 === 0 ? 'background.default' : 'grey.50' }}
                          >
                            <TableCell>
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                <Chip label={match.match_rank} color="primary" size="small" />
                                <Chip label="BUY" color="primary" size="small" variant="outlined" />
                              </Box>
                            </TableCell>
                            <TableCell>
                              <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                                {match.buy_product_id || 'N/A'}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                                {match.buy_card_name || 'N/A'}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                {match.buy_edition || 'N/A'}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Typography variant="body2">
                                {match.buy_rarity || 'N/A'}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                {match.buy_foil ? 'Foil' : 'Non-foil'}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Typography variant="body2" sx={{ fontWeight: 'medium', color: 'success.main' }}>
                                ${typeof match.buy_price === 'number' ? match.buy_price.toFixed(2) : 'N/A'}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Typography variant="body2">
                                {match.buy_quantity?.toLocaleString() || 'N/A'}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Typography variant="body2" sx={{ fontFamily: 'monospace', fontWeight: 'bold' }}>
                                {match.similarity_score.toFixed(3)}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              {getDecisionChip(getDecisionStatus(match))}
                            </TableCell>
                            <TableCell>
                              {getDecisionStatus(match) === 'pending' ? (
                                <Box sx={{ display: 'flex', gap: 1 }}>
                                  <Button
                                    size="small"
                                    variant="contained"
                                    color="success"
                                    startIcon={<CheckIcon />}
                                    onClick={() => makeMatchDecision(match.sell_index, match.buy_index, 'accept')}
                                  >
                                    Accept
                                  </Button>
                                  <Button
                                    size="small"
                                    variant="outlined"
                                    color="error"
                                    startIcon={<CloseIcon />}
                                    onClick={() => makeMatchDecision(match.sell_index, match.buy_index, 'reject')}
                                  >
                                    Reject
                                  </Button>
                                </Box>
                              ) : (
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                  <CheckIcon color="success" fontSize="small" />
                                  <Typography variant="caption" color="success.main">
                                    Saved to Database
                                  </Typography>
                                </Box>
                              )}
                            </TableCell>
                          </TableRow>
                        );
                      })
                    ];
                  }).flat()}
                </TableBody>
              </Table>
            </TableContainer>
            
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
              <Pagination
                count={totalPages}
                page={currentPage}
                onChange={(_, page) => setCurrentPage(page)}
                color="primary"
              />
            </Box>
          </CardContent>
        </Card>
      )}

      {matches.length === 0 && !loading && systemStatus?.ready_for_matching && (
        <Card>
          <CardContent>
            <Typography variant="body1" color="text.secondary" textAlign="center">
              No matches found. Try adjusting the similarity threshold or check your data.
            </Typography>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default MatchingPage;