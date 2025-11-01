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
  Pagination
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  ExpandMore as ExpandMoreIcon,
  GetApp as DownloadIcon,
  Analytics as AnalyticsIcon
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
  sell_quantity: number;
  buy_product_id?: number;
  buy_card_name?: string;
  buy_edition?: string;
  buy_rarity?: string;
  buy_price?: number;
  buy_foil?: string;
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
        return_stats: returnStats.toString()
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

  // Pagination logic
  const startIndex = (currentPage - 1) * rowsPerPage;
  const endIndex = startIndex + rowsPerPage;
  const paginatedMatches = matches.slice(startIndex, endIndex);
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

      {/* Configuration Panel */}
      <Accordion sx={{ mb: 3 }}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6">Matching Configuration</Typography>
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
        
        {matches.length > 0 && (
          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
            onClick={() => {
              // TODO: Implement CSV export
              console.log('Export functionality to be implemented');
            }}
          >
            Export Results
          </Button>
        )}
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
                  <Chip label={`High: ${stats.confidence_distribution.high}`} color="success" size="small" />
                  <Chip label={`Medium: ${stats.confidence_distribution.medium}`} color="warning" size="small" />
                  <Chip label={`Low: ${stats.confidence_distribution.low}`} color="error" size="small" />
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
                    <TableCell><strong>Rank</strong></TableCell>
                    <TableCell><strong>Sell Product Info</strong></TableCell>
                    <TableCell><strong>Buy Product Info</strong></TableCell>
                    <TableCell><strong>Price</strong></TableCell>
                    <TableCell><strong>Qty</strong></TableCell>
                    <TableCell><strong>Similarity</strong></TableCell>
                    <TableCell><strong>Confidence</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {paginatedMatches.map((match, index) => {
                    const confidence = getConfidenceLevel(match.similarity_score);
                    return (
                      <TableRow key={`${match.sell_index}-${match.buy_index}-${index}`}>
                        <TableCell>{match.match_rank}</TableCell>
                        <TableCell>
                          <Box>
                            <Typography variant="body2" sx={{ fontWeight: 'medium', mb: 0.5 }}>
                              {match.sell_product_name}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              TCG ID: {match.sell_tcgplayer_id} | {match.sell_set_name} | {match.sell_rarity}
                            </Typography>
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Box>
                            <Typography variant="body2" sx={{ fontWeight: 'medium', mb: 0.5 }}>
                              {match.buy_card_name || 'N/A'}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              Buy ID: {match.buy_product_id || 'N/A'} | {match.buy_edition || 'N/A'} | {match.buy_rarity || 'N/A'} {match.buy_foil ? `| ${match.buy_foil}` : ''}
                            </Typography>
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Box>
                            <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                              ${match.sell_market_price?.toFixed(2) || 'N/A'}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              Buy: ${typeof match.buy_price === 'number' ? match.buy_price.toFixed(2) : 'N/A'}
                            </Typography>
                          </Box>
                        </TableCell>
                        <TableCell>
                          {match.sell_quantity?.toLocaleString() || 'N/A'}
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                            {match.similarity_score.toFixed(3)}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip 
                            label={confidence.level}
                            color={confidence.color}
                            size="small"
                          />
                        </TableCell>
                      </TableRow>
                    );
                  })}
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