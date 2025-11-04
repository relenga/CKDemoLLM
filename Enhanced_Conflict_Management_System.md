# Enhanced Conflict Management System - Implementation Guide

## Overview

This document outlines the comprehensive conflict management system implemented to address the 1:1 relationship requirements between `BuyProductId` and `SellTCGplayerId`, along with sophisticated conflict resolution and match exclusion capabilities.

## Core Improvements

### 1. Part IDs as Primary Keys
- **Change**: Modified database schema to use `sell_tcgplayer_id` and `buy_product_id` as unique constraints
- **Benefit**: Enforces true 1:1 relationship at the database level
- **Implementation**: Added UNIQUE constraints in `match_decisions` table

### 2. Three-Table Conflict Management System

#### **match_decisions** Table (Enhanced)
```sql
CREATE TABLE match_decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sell_index INTEGER NOT NULL,
    buy_index INTEGER NOT NULL,
    sell_tcgplayer_id TEXT NOT NULL UNIQUE,      -- Enforces 1:1
    sell_product_name TEXT,
    sell_set_name TEXT,
    buy_product_id TEXT NOT NULL UNIQUE,         -- Enforces 1:1
    buy_card_name TEXT,
    buy_edition TEXT,
    similarity_score REAL NOT NULL,
    decision_status TEXT NOT NULL DEFAULT 'pending',
    auto_accept_threshold REAL,
    user_notes TEXT,
    save_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(sell_index, buy_index)
);
```

#### **matching_errors** Table (New)
```sql
CREATE TABLE matching_errors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    error_type TEXT NOT NULL,                    -- 'sell_conflict', 'buy_conflict', 'duplicate_match'
    conflicting_sell_tcgplayer_id TEXT,
    conflicting_buy_product_id TEXT,
    existing_match_id INTEGER,
    attempted_sell_index INTEGER,
    attempted_buy_index INTEGER,
    attempted_similarity_score REAL,
    attempted_decision_status TEXT,
    error_message TEXT,
    resolution_status TEXT DEFAULT 'unresolved', -- 'unresolved', 'resolved', 'ignored'
    resolution_action TEXT,
    resolution_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (existing_match_id) REFERENCES match_decisions(id)
);
```

#### **non_matches** Table (New)
```sql
CREATE TABLE non_matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sell_tcgplayer_id TEXT NOT NULL,
    buy_product_id TEXT NOT NULL,
    sell_product_name TEXT,
    sell_set_name TEXT,
    buy_card_name TEXT,
    buy_edition TEXT,
    rejection_reason TEXT,
    similarity_score_when_rejected REAL,
    rejected_by TEXT DEFAULT 'user',             -- 'user', 'system', 'auto_filter'
    rejection_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    permanent_exclusion BOOLEAN DEFAULT TRUE,    -- Persists across sessions
    notes TEXT,
    UNIQUE(sell_tcgplayer_id, buy_product_id)
);
```

## Enhanced Backend Functionality

### 1. Conflict Detection in `save_match_decision()`
```python
def save_match_decision(self, match_data: Dict, decision_status: str, 
                       auto_accept_threshold: Optional[float] = None,
                       user_notes: Optional[str] = None) -> int:
    """
    Save match decision with comprehensive conflict detection.
    
    Detects and handles:
    - SellTCGplayerId already matched to different BuyProductId
    - BuyProductId already matched to different SellTCGplayerId
    - Logs conflicts to matching_errors table
    - Automatically adds rejected matches to non_matches table
    """
```

### 2. New API Endpoints

#### Conflict Management
- `GET /api/matcher/conflicts` - Get all unresolved conflicts with summary
- `POST /api/matcher/conflicts/{conflict_id}/resolve` - Resolve specific conflict
- `GET /api/matcher/non-matches` - List all non-match exclusions
- `POST /api/matcher/non-matches` - Manually add non-match exclusion
- `DELETE /api/matcher/non-matches/{sell_id}/{buy_id}` - Remove exclusion

#### Enhanced Matching Decision
- `POST /api/matcher/decide` - Now returns HTTP 409 for conflicts with detailed error info

### 3. Auto-Accept Logic Enhancement
```python
# Enhanced auto-accept with conflict handling
try:
    match_db.save_match_decision(
        match_data=best_match.to_dict(),
        decision_status='auto_accepted',
        auto_accept_threshold=auto_accept_threshold
    )
    auto_accepted_count += 1
    matches_df.loc[best_match_idx, 'decision_status'] = 'auto_accepted'
    
except ValueError as conflict_error:
    # Handle conflicts during auto-accept - log and skip
    logger.warning(f"🚨 Auto-accept conflict for sell_idx {sell_idx}: {conflict_error}")
    matches_df.loc[best_match_idx, 'decision_status'] = 'conflict_blocked'
```

### 4. Non-Match Filtering in Matching Algorithm
```python
# Filter out non-matches before processing
if len(matches_df) > 0 and non_matches:
    filtered_indices = []
    for idx, match in matches_df.iterrows():
        sell_id = str(match.get('sell_tcgplayer_id', ''))
        buy_id = str(match.get('buy_product_id', ''))
        non_match_key = (sell_id, buy_id)
        
        if non_match_key not in non_matches:
            filtered_indices.append(idx)
        else:
            logger.info(f"🚫 Filtered non-match: {sell_id} ↔ {buy_id}")
    
    matches_df = matches_df.loc[filtered_indices].reset_index(drop=True)
```

## Frontend Conflict Management Interface

### New ConflictManagementPage Features

#### 1. Summary Dashboard
- Total conflicts count
- Non-matches count
- Accepted matches count
- Pending matches count

#### 2. Conflicts Tab
- Table view of all unresolved conflicts
- Conflict type indicators (sell_conflict, buy_conflict, duplicate_match)
- Similarity scores and error messages
- Resolution dialog with:
  - Resolution action description
  - Option to replace existing match
  - Conflict resolution tracking

#### 3. Non-Matches Tab
- Table view of all match exclusions
- Add new non-match exclusions manually
- Remove existing exclusions
- Filter by rejection reason and source

#### 4. Navigation Integration
- New "Conflict Management" menu item in navigation
- Warning icon to indicate conflict management section

## Workflow Examples

### Scenario 1: Conflicting Auto-Accept
1. **Situation**: SellTCGplayerId "ABC123" tries to auto-accept with BuyProductId "XYZ789", but "ABC123" is already matched to "DEF456"
2. **Detection**: `save_match_decision()` detects sell_conflict
3. **Action**: 
   - Conflict logged to `matching_errors` table
   - Auto-accept blocked, status set to 'conflict_blocked'
   - Error message: "SellTCGplayerId ABC123 is already matched to another product"
4. **Resolution**: Admin reviews in Conflict Management page and decides to:
   - Keep existing match (mark conflict as resolved)
   - OR Replace existing match (update existing match status to 'replaced')

### Scenario 2: User Rejects Good Match
1. **Situation**: User rejects a match between SellTCGplayerId "ABC123" and BuyProductId "XYZ789"
2. **Action**:
   - Match decision saved with status 'rejected'
   - Automatically added to `non_matches` table with permanent_exclusion=TRUE
   - Future matching runs will skip this pair
3. **Benefit**: Prevents matcher from repeatedly suggesting the same incorrect match

### Scenario 3: Manual Non-Match Addition
1. **Situation**: Admin knows certain part pairs should never be matched
2. **Action**: Use Conflict Management interface to add non-match exclusions
3. **Form**: 
   - SellTCGplayerId
   - BuyProductId
   - Rejection reason
   - Permanent exclusion flag
4. **Result**: Matcher will never suggest this pairing

## Error Types and Resolution Strategies

### sell_conflict
- **Cause**: SellTCGplayerId already matched to different BuyProductId
- **Resolution Options**:
  - Keep existing match (most common)
  - Replace existing match with higher confidence match
  - Add both as non-matches if neither is correct

### buy_conflict
- **Cause**: BuyProductId already matched to different SellTCGplayerId
- **Resolution Options**:
  - Keep existing match (most common)
  - Replace existing match with higher confidence match
  - Add both as non-matches if neither is correct

### duplicate_match
- **Cause**: Exact same sell_index/buy_index pair attempted multiple times
- **Resolution Options**:
  - Keep existing decision
  - Update with new similarity score/decision

## Performance Considerations

### Database Indexes
```sql
-- Performance indexes for conflict detection
CREATE INDEX idx_sell_tcgplayer_id ON match_decisions(sell_tcgplayer_id);
CREATE INDEX idx_buy_product_id ON match_decisions(buy_product_id);
CREATE INDEX idx_error_type ON matching_errors(error_type);
CREATE INDEX idx_resolution_status ON matching_errors(resolution_status);
CREATE INDEX idx_non_match_sell_id ON non_matches(sell_tcgplayer_id);
CREATE INDEX idx_non_match_buy_id ON non_matches(buy_product_id);
CREATE INDEX idx_permanent_exclusion ON non_matches(permanent_exclusion);
```

### Non-Match Filtering Efficiency
- Non-matches loaded once per matching session
- Stored in memory as dictionary for O(1) lookup
- Filtered before intensive similarity calculations

## Production Deployment Considerations

### 1. Data Migration
- Existing match_decisions may have duplicate part IDs
- Run conflict detection script before adding UNIQUE constraints
- Backup existing data before schema changes

### 2. Monitoring
- Track conflict rates to identify data quality issues
- Monitor non-match growth to prevent excessive exclusions
- Alert on high conflict rates during auto-accept

### 3. Maintenance
- Periodic review of unresolved conflicts
- Clean up old non-matches that may no longer be relevant
- Regular performance analysis of conflict detection queries

## Testing Scenarios

### Unit Tests
- Conflict detection with various error types
- Non-match filtering with edge cases
- Resolution workflow validation

### Integration Tests
- End-to-end matching with conflicts
- Auto-accept conflict handling
- Frontend conflict resolution workflow

### Load Tests
- Large dataset matching with many conflicts
- Non-match filtering performance at scale
- Concurrent conflict resolution operations

## Configuration Options

### Environment Variables
```bash
# Conflict management settings
ENABLE_CONFLICT_DETECTION=true
AUTO_RESOLVE_LOW_CONFIDENCE_CONFLICTS=false
MAX_NON_MATCHES_PER_SESSION=10000
CONFLICT_RETENTION_DAYS=90
```

### Feature Flags
- `enable_auto_conflict_resolution`: Automatically resolve obvious conflicts
- `strict_1_1_enforcement`: Enforce strict 1:1 relationships vs. warnings
- `persistent_non_matches`: Whether non-matches persist across sessions

## Benefits Summary

### 1. Data Integrity
- ✅ Enforced 1:1 relationships at database level
- ✅ No duplicate part assignments
- ✅ Audit trail for all conflicts and resolutions

### 2. User Experience
- ✅ Clear conflict resolution interface
- ✅ Prevents repeated incorrect suggestions
- ✅ Transparent conflict resolution workflow

### 3. Production Ready
- ✅ Comprehensive error handling
- ✅ Performance optimized with proper indexes
- ✅ Scalable conflict detection system

### 4. Maintainability
- ✅ Clean separation of concerns
- ✅ Extensible error type system
- ✅ Comprehensive logging and monitoring

This enhanced conflict management system transforms the basic matching engine into a production-ready solution capable of handling complex real-world matching scenarios while maintaining data integrity and providing clear resolution pathways for conflicts.