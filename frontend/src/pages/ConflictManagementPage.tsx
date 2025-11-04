import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Alert,
  AlertTitle,
  Chip,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControlLabel,
  Checkbox,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Tabs,
  Tab,
  Divider,
  IconButton,
  Tooltip,
  CircularProgress
} from '@mui/material';
import {
  Warning as WarningIcon,
  Error as ErrorIcon,
  Block as BlockIcon,
  Refresh as RefreshIcon,
  Delete as DeleteIcon,
  Add as AddIcon,
  DeleteSweep as ClearAllIcon
} from '@mui/icons-material';

interface MatchingError {
  id: number;
  error_type: string;
  conflicting_sell_tcgplayer_id?: string;
  conflicting_buy_product_id?: string;
  existing_match_id?: number;
  attempted_sell_index: number;
  attempted_buy_index: number;
  attempted_similarity_score: number;
  error_message: string;
  resolution_status: string;
  created_at: string;
  sell_product_name?: string;
  buy_card_name?: string;
}

interface NonMatch {
  sell_tcgplayer_id: string;
  buy_product_id: string;
  rejection_reason: string;
  similarity_score_when_rejected: number;
  rejected_by: string;
}

interface ConflictSummary {
  matching_errors: Record<string, Record<string, number>>;
  non_matches: number;
  match_decisions: Record<string, number>;
  generated_at: string;
}

const ConflictManagementPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [conflicts, setConflicts] = useState<MatchingError[]>([]);
  const [nonMatches, setNonMatches] = useState<NonMatch[]>([]);
  const [summary, setSummary] = useState<ConflictSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Resolution dialog state
  const [resolveDialog, setResolveDialog] = useState<{
    open: boolean;
    conflict: MatchingError | null;
    action: string;
    replaceExisting: boolean;
  }>({
    open: false,
    conflict: null,
    action: '',
    replaceExisting: false
  });
  
  // Add non-match dialog state
  const [addNonMatchDialog, setAddNonMatchDialog] = useState<{
    open: boolean;
    sellId: string;
    buyId: string;
    reason: string;
    permanent: boolean;
  }>({
    open: false,
    sellId: '',
    buyId: '',
    reason: '',
    permanent: true
  });

  // Fetch conflicts and summary data
  const fetchData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const [conflictsResponse, nonMatchesResponse] = await Promise.all([
        fetch('/api/matcher/conflicts'),
        fetch('/api/matcher/non-matches')
      ]);
      
      if (!conflictsResponse.ok || !nonMatchesResponse.ok) {
        throw new Error('Failed to fetch conflict data');
      }
      
      const conflictsData = await conflictsResponse.json();
      const nonMatchesData = await nonMatchesResponse.json();
      
      setConflicts(conflictsData.data.unresolved_conflicts);
      setSummary(conflictsData.data.summary);
      setNonMatches(nonMatchesData.data.non_matches);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error occurred');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Resolve conflict or clear all data
  const handleResolveConflict = async () => {
    const { conflict, action, replaceExisting } = resolveDialog;
    
    // Handle clear all data special case
    if (action === 'CLEAR_ALL_DATA') {
      try {
        const response = await fetch('/api/matcher/clear-all', {
          method: 'DELETE'
        });
        
        if (!response.ok) {
          throw new Error('Failed to clear all data');
        }
        
        const result = await response.json();
        setResolveDialog({ open: false, conflict: null, action: '', replaceExisting: false });
        fetchData(); // Refresh data
        
        // Show success message with details
        console.log('Cleared data:', result.data);
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to clear all data');
      }
      return;
    }
    
    // Handle normal conflict resolution
    if (!conflict) return;
    
    try {
      const response = await fetch(`/api/matcher/conflicts/${conflict.id}/resolve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          resolution_action: action,
          replace_existing: replaceExisting
        })
      });
      
      if (!response.ok) {
        throw new Error('Failed to resolve conflict');
      }
      
      setResolveDialog({ open: false, conflict: null, action: '', replaceExisting: false });
      fetchData(); // Refresh data
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to resolve conflict');
    }
  };

  // Add non-match
  const handleAddNonMatch = async () => {
    const { sellId, buyId, reason, permanent } = addNonMatchDialog;
    
    try {
      const response = await fetch('/api/matcher/non-matches', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sell_tcgplayer_id: sellId,
          buy_product_id: buyId,
          rejection_reason: reason,
          permanent_exclusion: permanent
        })
      });
      
      if (!response.ok) {
        throw new Error('Failed to add non-match');
      }
      
      setAddNonMatchDialog({ open: false, sellId: '', buyId: '', reason: '', permanent: true });
      fetchData(); // Refresh data
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add non-match');
    }
  };

  // Remove non-match
  const handleRemoveNonMatch = async (sellId: string, buyId: string) => {
    try {
      const response = await fetch(`/api/matcher/non-matches/${encodeURIComponent(sellId)}/${encodeURIComponent(buyId)}`, {
        method: 'DELETE'
      });
      
      if (!response.ok) {
        throw new Error('Failed to remove non-match');
      }
      
      fetchData(); // Refresh data
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to remove non-match');
    }
  };

  const getErrorTypeColor = (errorType: string) => {
    switch (errorType) {
      case 'sell_conflict': return 'error';
      case 'buy_conflict': return 'warning';
      case 'duplicate_match': return 'info';
      default: return 'default';
    }
  };

  const getSeverityIcon = (errorType: string) => {
    switch (errorType) {
      case 'sell_conflict':
      case 'buy_conflict':
        return <ErrorIcon />;
      default:
        return <WarningIcon />;
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Conflict Management
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            color="error"
            startIcon={<ClearAllIcon />}
            onClick={() => setResolveDialog({
              open: true,
              conflict: null,
              action: 'CLEAR_ALL_DATA',
              replaceExisting: false
            })}
            disabled={loading}
          >
            Clear All Data
          </Button>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={fetchData}
            disabled={loading}
          >
            Refresh
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          <AlertTitle>Error</AlertTitle>
          {error}
        </Alert>
      )}

      {/* Summary Cards */}
      {summary && (
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Total Conflicts
                </Typography>
                <Typography variant="h5" component="div">
                  {Object.values(summary.matching_errors).reduce((acc, statuses) => 
                    acc + Object.values(statuses).reduce((sum, count) => sum + count, 0), 0
                  )}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Non-Matches
                </Typography>
                <Typography variant="h5" component="div">
                  {summary.non_matches}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Accepted Matches
                </Typography>
                <Typography variant="h5" component="div">
                  {(summary.match_decisions.accepted || 0) + (summary.match_decisions.auto_accepted || 0)}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Pending Matches
                </Typography>
                <Typography variant="h5" component="div">
                  {summary.match_decisions.pending || 0}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Tabs */}
      <Tabs value={activeTab} onChange={(_, newValue) => setActiveTab(newValue)} sx={{ mb: 3 }}>
        <Tab label={`Conflicts (${conflicts.length})`} />
        <Tab label={`Non-Matches (${nonMatches.length})`} />
      </Tabs>

      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
          <CircularProgress />
        </Box>
      )}

      {/* Conflicts Tab */}
      {activeTab === 0 && !loading && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Unresolved Matching Conflicts
            </Typography>
            {conflicts.length === 0 ? (
              <Alert severity="success">
                <AlertTitle>No Conflicts</AlertTitle>
                All matching conflicts have been resolved!
              </Alert>
            ) : (
              <TableContainer component={Paper}>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Type</TableCell>
                      <TableCell>Conflicting IDs</TableCell>
                      <TableCell>Similarity</TableCell>
                      <TableCell>Error Message</TableCell>
                      <TableCell>Created</TableCell>
                      <TableCell>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {conflicts.map((conflict) => (
                      <TableRow key={conflict.id}>
                        <TableCell>
                          <Chip
                            icon={getSeverityIcon(conflict.error_type)}
                            label={conflict.error_type.replace('_', ' ').toUpperCase()}
                            color={getErrorTypeColor(conflict.error_type) as any}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            Sell: {conflict.conflicting_sell_tcgplayer_id || 'N/A'}
                          </Typography>
                          <Typography variant="body2">
                            Buy: {conflict.conflicting_buy_product_id || 'N/A'}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          {conflict.attempted_similarity_score.toFixed(3)}
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" sx={{ maxWidth: 200 }}>
                            {conflict.error_message}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          {new Date(conflict.created_at).toLocaleDateString()}
                        </TableCell>
                        <TableCell>
                          <Button
                            size="small"
                            variant="outlined"
                            onClick={() => setResolveDialog({
                              open: true,
                              conflict,
                              action: '',
                              replaceExisting: false
                            })}
                          >
                            Resolve
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </CardContent>
        </Card>
      )}

      {/* Non-Matches Tab */}
      {activeTab === 1 && !loading && (
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">
                Non-Match Exclusions
              </Typography>
              <Button
                variant="outlined"
                startIcon={<AddIcon />}
                onClick={() => setAddNonMatchDialog({
                  open: true,
                  sellId: '',
                  buyId: '',
                  reason: '',
                  permanent: true
                })}
              >
                Add Non-Match
              </Button>
            </Box>
            
            {nonMatches.length === 0 ? (
              <Alert severity="info">
                <AlertTitle>No Non-Matches</AlertTitle>
                No matching exclusions are currently configured.
              </Alert>
            ) : (
              <TableContainer component={Paper}>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Sell TCGPlayer ID</TableCell>
                      <TableCell>Buy Product ID</TableCell>
                      <TableCell>Rejection Reason</TableCell>
                      <TableCell>Similarity When Rejected</TableCell>
                      <TableCell>Rejected By</TableCell>
                      <TableCell>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {nonMatches.map((nonMatch, index) => (
                      <TableRow key={`${nonMatch.sell_tcgplayer_id}-${nonMatch.buy_product_id}`}>
                        <TableCell>{nonMatch.sell_tcgplayer_id}</TableCell>
                        <TableCell>{nonMatch.buy_product_id}</TableCell>
                        <TableCell>{nonMatch.rejection_reason}</TableCell>
                        <TableCell>{nonMatch.similarity_score_when_rejected.toFixed(3)}</TableCell>
                        <TableCell>
                          <Chip label={nonMatch.rejected_by} size="small" />
                        </TableCell>
                        <TableCell>
                          <Tooltip title="Remove Non-Match">
                            <IconButton
                              size="small"
                              onClick={() => handleRemoveNonMatch(nonMatch.sell_tcgplayer_id, nonMatch.buy_product_id)}
                            >
                              <DeleteIcon />
                            </IconButton>
                          </Tooltip>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </CardContent>
        </Card>
      )}

      {/* Resolve Conflict Dialog */}
      <Dialog 
        open={resolveDialog.open} 
        onClose={() => setResolveDialog({ ...resolveDialog, open: false })}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          {resolveDialog.action === 'CLEAR_ALL_DATA' ? 'Clear All Matching Data' : 'Resolve Matching Conflict'}
        </DialogTitle>
        <DialogContent>
          {resolveDialog.action === 'CLEAR_ALL_DATA' ? (
            <Alert severity="warning" sx={{ mb: 2 }}>
              <AlertTitle>Warning: This will permanently delete all matching data</AlertTitle>
              This action will clear:
              <ul>
                <li>All match decisions (accepted, rejected, pending)</li>
                <li>All matching errors and conflict logs</li>
                <li>All non-match exclusions</li>
                <li>All matching session history</li>
              </ul>
              This cannot be undone. Are you sure you want to proceed?
            </Alert>
          ) : (
            resolveDialog.conflict && (
              <>
                <Alert severity="warning" sx={{ mb: 2 }}>
                  <AlertTitle>{resolveDialog.conflict.error_type.replace('_', ' ').toUpperCase()}</AlertTitle>
                  {resolveDialog.conflict.error_message}
                </Alert>
                
                <TextField
                  fullWidth
                  label="Resolution Action"
                  multiline
                  rows={3}
                  value={resolveDialog.action}
                  onChange={(e) => setResolveDialog({ ...resolveDialog, action: e.target.value })}
                  placeholder="Describe the action taken to resolve this conflict..."
                  sx={{ mb: 2 }}
                />
                
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={resolveDialog.replaceExisting}
                      onChange={(e) => setResolveDialog({ ...resolveDialog, replaceExisting: e.target.checked })}
                    />
                  }
                  label="Replace existing match with new match"
                />
              </>
            )
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setResolveDialog({ ...resolveDialog, open: false })}>
            Cancel
          </Button>
          <Button 
            onClick={handleResolveConflict}
            variant="contained"
            color={resolveDialog.action === 'CLEAR_ALL_DATA' ? 'error' : 'primary'}
            disabled={resolveDialog.action !== 'CLEAR_ALL_DATA' && !resolveDialog.action.trim()}
          >
            {resolveDialog.action === 'CLEAR_ALL_DATA' ? 'Clear All Data' : 'Resolve Conflict'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Add Non-Match Dialog */}
      <Dialog 
        open={addNonMatchDialog.open} 
        onClose={() => setAddNonMatchDialog({ ...addNonMatchDialog, open: false })}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Add Non-Match Exclusion</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Sell TCGPlayer ID"
            value={addNonMatchDialog.sellId}
            onChange={(e) => setAddNonMatchDialog({ ...addNonMatchDialog, sellId: e.target.value })}
            sx={{ mb: 2, mt: 1 }}
          />
          
          <TextField
            fullWidth
            label="Buy Product ID"
            value={addNonMatchDialog.buyId}
            onChange={(e) => setAddNonMatchDialog({ ...addNonMatchDialog, buyId: e.target.value })}
            sx={{ mb: 2 }}
          />
          
          <TextField
            fullWidth
            label="Rejection Reason"
            multiline
            rows={2}
            value={addNonMatchDialog.reason}
            onChange={(e) => setAddNonMatchDialog({ ...addNonMatchDialog, reason: e.target.value })}
            sx={{ mb: 2 }}
          />
          
          <FormControlLabel
            control={
              <Checkbox
                checked={addNonMatchDialog.permanent}
                onChange={(e) => setAddNonMatchDialog({ ...addNonMatchDialog, permanent: e.target.checked })}
              />
            }
            label="Permanent exclusion (persists across matching sessions)"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddNonMatchDialog({ ...addNonMatchDialog, open: false })}>
            Cancel
          </Button>
          <Button 
            onClick={handleAddNonMatch}
            variant="contained"
            disabled={!addNonMatchDialog.sellId.trim() || !addNonMatchDialog.buyId.trim() || !addNonMatchDialog.reason.trim()}
          >
            Add Non-Match
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ConflictManagementPage;