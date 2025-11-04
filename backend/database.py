"""
SQLite database models and connection handling for match results persistence.
"""

import sqlite3
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from contextlib import contextmanager
import json
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Database file path
DB_PATH = "match_results.db"

@dataclass
class MatchDecision:
    """Data class for match decision records."""
    id: Optional[int]
    sell_index: int
    buy_index: int
    sell_tcgplayer_id: str
    buy_product_id: str
    similarity_score: float
    decision_status: str  # 'pending', 'accepted', 'rejected', 'auto_accepted'
    save_date: datetime
    auto_accept_threshold: Optional[float] = None
    user_notes: Optional[str] = None


class MatchDatabase:
    """Database manager for match results and decisions."""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create match_decisions table with part IDs as unique constraints
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS match_decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sell_tcgplayer_id TEXT NOT NULL UNIQUE,
                    sell_product_name TEXT,
                    sell_set_name TEXT,
                    buy_product_id TEXT NOT NULL UNIQUE,
                    buy_card_name TEXT,
                    buy_edition TEXT,
                    similarity_score REAL NOT NULL,
                    decision_status TEXT NOT NULL DEFAULT 'pending',
                    auto_accept_threshold REAL,
                    user_notes TEXT,
                    save_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create matching_errors table for conflict tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS matching_errors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    error_type TEXT NOT NULL,  -- 'sell_conflict', 'buy_conflict', 'duplicate_match'
                    conflicting_sell_tcgplayer_id TEXT,
                    conflicting_buy_product_id TEXT,
                    existing_match_id INTEGER,
                    attempted_similarity_score REAL,
                    attempted_decision_status TEXT,
                    error_message TEXT,
                    resolution_status TEXT DEFAULT 'unresolved',  -- 'unresolved', 'resolved', 'ignored'
                    resolution_action TEXT,  -- What action was taken to resolve
                    resolution_date TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (existing_match_id) REFERENCES match_decisions(id)
                )
            """)
            
            # Create non_matches table for user-rejected pairs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS non_matches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sell_tcgplayer_id TEXT NOT NULL,
                    buy_product_id TEXT NOT NULL,
                    sell_product_name TEXT,
                    sell_set_name TEXT,
                    buy_card_name TEXT,
                    buy_edition TEXT,
                    rejection_reason TEXT,
                    similarity_score_when_rejected REAL,
                    rejected_by TEXT DEFAULT 'user',  -- 'user', 'system', 'auto_filter'
                    rejection_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    permanent_exclusion BOOLEAN DEFAULT TRUE,  -- Should this exclusion persist across sessions
                    notes TEXT,
                    UNIQUE(sell_tcgplayer_id, buy_product_id)
                )
            """)
            
            # Create match_sessions table for tracking matching runs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS match_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_selllist_items INTEGER,
                    total_buylist_items INTEGER,
                    total_matches_found INTEGER,
                    similarity_threshold REAL,
                    max_matches_per_item INTEGER,
                    auto_accept_threshold REAL,
                    processing_time_seconds REAL,
                    match_config TEXT,  -- JSON config
                    errors_encountered INTEGER DEFAULT 0,
                    conflicts_resolved INTEGER DEFAULT 0
                )
            """)
            
            # Create indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sell_tcgplayer_id ON match_decisions(sell_tcgplayer_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_buy_product_id ON match_decisions(buy_product_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_decision_status ON match_decisions(decision_status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_similarity_score ON match_decisions(similarity_score)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_save_date ON match_decisions(save_date)")
            
            # Indexes for error tracking
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_error_type ON matching_errors(error_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_resolution_status ON matching_errors(resolution_status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_conflicting_sell_id ON matching_errors(conflicting_sell_tcgplayer_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_conflicting_buy_id ON matching_errors(conflicting_buy_product_id)")
            
            # Indexes for non-matches
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_non_match_sell_id ON non_matches(sell_tcgplayer_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_non_match_buy_id ON non_matches(buy_product_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_permanent_exclusion ON non_matches(permanent_exclusion)")
            
            conn.commit()
            logger.info("✅ Database initialized successfully with enhanced conflict tracking")
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
        finally:
            conn.close()
    
    def save_match_decision(self, match_data: Dict, decision_status: str, 
                           auto_accept_threshold: Optional[float] = None,
                           user_notes: Optional[str] = None) -> int:
        """
        Save or update a match decision with conflict detection.
        
        Args:
            match_data: Match data dictionary from the matching engine
            decision_status: 'pending', 'accepted', 'rejected', 'auto_accepted'
            auto_accept_threshold: Threshold used for auto-acceptance
            user_notes: Optional user notes
            
        Returns:
            ID of the saved decision
            
        Raises:
            ValueError: If there's a conflict with existing matches
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                sell_tcgplayer_id = match_data.get('sell_tcgplayer_id', '')
                buy_product_id = match_data.get('buy_product_id', '')
                
                # Check for conflicts with existing matches (only for accepted matches)
                if decision_status in ['accepted', 'auto_accepted']:
                    # Check if sell_tcgplayer_id is already matched
                    cursor.execute("""
                        SELECT id, buy_product_id, decision_status FROM match_decisions 
                        WHERE sell_tcgplayer_id = ? AND decision_status IN ('accepted', 'auto_accepted')
                    """, (sell_tcgplayer_id,))
                    sell_conflict = cursor.fetchone()
                    
                    # Check if buy_product_id is already matched
                    cursor.execute("""
                        SELECT id, sell_tcgplayer_id, decision_status FROM match_decisions 
                        WHERE buy_product_id = ? AND decision_status IN ('accepted', 'auto_accepted')
                    """, (buy_product_id,))
                    buy_conflict = cursor.fetchone()
                    
                    if sell_conflict:
                        self._log_matching_error(
                            cursor, 'sell_conflict', sell_tcgplayer_id, buy_product_id,
                            sell_conflict['id'], match_data, 
                            f"SellTCGplayerId {sell_tcgplayer_id} already matched to BuyProductId {sell_conflict['buy_product_id']}"
                        )
                        raise ValueError(f"SellTCGplayerId {sell_tcgplayer_id} is already matched to another product")
                    
                    if buy_conflict:
                        self._log_matching_error(
                            cursor, 'buy_conflict', sell_tcgplayer_id, buy_product_id,
                            buy_conflict['id'], match_data,
                            f"BuyProductId {buy_product_id} already matched to SellTCGplayerId {buy_conflict['sell_tcgplayer_id']}"
                        )
                        raise ValueError(f"BuyProductId {buy_product_id} is already matched to another product")
                
                # Check if this exact decision already exists (by part IDs)
                cursor.execute("""
                    SELECT id FROM match_decisions 
                    WHERE sell_tcgplayer_id = ? AND buy_product_id = ?
                """, (sell_tcgplayer_id, buy_product_id))
                
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing decision
                    cursor.execute("""
                        UPDATE match_decisions SET
                            similarity_score = ?,
                            decision_status = ?,
                            auto_accept_threshold = ?,
                            user_notes = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE sell_tcgplayer_id = ? AND buy_product_id = ?
                    """, (
                        match_data['similarity_score'],
                        decision_status,
                        auto_accept_threshold,
                        user_notes,
                        sell_tcgplayer_id,
                        buy_product_id
                    ))
                    decision_id = existing['id']
                    logger.info(f"🔄 Updated match decision {decision_id}: {decision_status}")
                else:
                    # Insert new decision
                    cursor.execute("""
                        INSERT INTO match_decisions (
                            sell_tcgplayer_id, sell_product_name, sell_set_name, 
                            buy_product_id, buy_card_name, buy_edition,
                            similarity_score, decision_status, auto_accept_threshold, 
                            user_notes, save_date
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        sell_tcgplayer_id,
                        match_data.get('sell_product_name', ''),
                        match_data.get('sell_set_name', ''),
                        buy_product_id,
                        match_data.get('buy_card_name', ''),
                        match_data.get('buy_edition', ''),
                        match_data['similarity_score'],
                        decision_status,
                        auto_accept_threshold,
                        user_notes,
                        datetime.now()
                    ))
                    decision_id = cursor.lastrowid
                    logger.info(f"💾 Saved new match decision {decision_id}: {decision_status}")
                
                # If rejecting a match, add to non_matches table
                if decision_status == 'rejected':
                    self.add_non_match(sell_tcgplayer_id, buy_product_id, match_data, 
                                     user_notes or "User rejected match", 
                                     match_data['similarity_score'])
                
                conn.commit()
                return decision_id
                
        except ValueError:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.error(f"Database error in save_match_decision: {e}")
            logger.error(f"Match data: {match_data}")
            raise
    
    def _log_matching_error(self, cursor, error_type: str, sell_id: str, buy_id: str, 
                           existing_match_id: int, match_data: Dict, error_message: str):
        """Log a matching conflict to the matching_errors table."""
        cursor.execute("""
            INSERT INTO matching_errors (
                error_type, conflicting_sell_tcgplayer_id, conflicting_buy_product_id,
                existing_match_id, attempted_similarity_score, attempted_decision_status, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            error_type, sell_id, buy_id, existing_match_id,
            match_data['similarity_score'], 'attempted_accept', error_message
        ))
        logger.warning(f"🚨 Logged matching error: {error_message}")
    
    def add_non_match(self, sell_tcgplayer_id: str, buy_product_id: str, 
                     match_data: Dict, rejection_reason: str, 
                     similarity_score: float, rejected_by: str = 'user') -> int:
        """
        Add a pair to the non_matches table to prevent future matching.
        
        Args:
            sell_tcgplayer_id: TCG Player ID of sell item
            buy_product_id: Product ID of buy item
            match_data: Original match data
            rejection_reason: Why this match was rejected
            similarity_score: Score when rejected
            rejected_by: Who rejected it ('user', 'system', 'auto_filter')
            
        Returns:
            ID of the non-match record
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO non_matches (
                    sell_tcgplayer_id, buy_product_id, sell_product_name, sell_set_name,
                    buy_card_name, buy_edition, rejection_reason, similarity_score_when_rejected,
                    rejected_by, permanent_exclusion
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sell_tcgplayer_id, buy_product_id,
                match_data.get('sell_product_name', ''),
                match_data.get('sell_set_name', ''),
                match_data.get('buy_card_name', ''),
                match_data.get('buy_edition', ''),
                rejection_reason, similarity_score, rejected_by, True
            ))
            
            non_match_id = cursor.lastrowid
            conn.commit()
            
            logger.info(f"🚫 Added non-match: {sell_tcgplayer_id} ↔ {buy_product_id}")
            return non_match_id
    
    def get_non_matches(self) -> Dict[Tuple[str, str], Dict]:
        """
        Get all non-matches to filter out during matching.
        
        Returns:
            Dictionary mapping (sell_tcgplayer_id, buy_product_id) -> non_match_data
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT sell_tcgplayer_id, buy_product_id, rejection_reason, 
                       similarity_score_when_rejected, rejected_by, permanent_exclusion
                FROM non_matches 
                WHERE permanent_exclusion = 1
            """)
            
            non_matches = {}
            for row in cursor.fetchall():
                key = (row['sell_tcgplayer_id'], row['buy_product_id'])
                non_matches[key] = {
                    'rejection_reason': row['rejection_reason'],
                    'similarity_score_when_rejected': row['similarity_score_when_rejected'],
                    'rejected_by': row['rejected_by']
                }
            
            logger.info(f"📋 Retrieved {len(non_matches)} non-match exclusions")
            return non_matches
    
    def get_matching_errors(self, status_filter: Optional[str] = None) -> List[Dict]:
        """
        Get matching errors for review and resolution.
        
        Args:
            status_filter: Filter by resolution status ('unresolved', 'resolved', 'ignored')
            
        Returns:
            List of matching error dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT me.*, md.sell_product_name, md.buy_card_name
                FROM matching_errors me
                LEFT JOIN match_decisions md ON me.existing_match_id = md.id
            """
            params = []
            
            if status_filter:
                query += " WHERE me.resolution_status = ?"
                params.append(status_filter)
            
            query += " ORDER BY me.created_at DESC"
            
            cursor.execute(query, params)
            
            errors = []
            for row in cursor.fetchall():
                error_dict = dict(row)
                errors.append(error_dict)
            
            logger.info(f"📋 Retrieved {len(errors)} matching errors")
            return errors
    
    def resolve_matching_error(self, error_id: int, resolution_action: str, 
                              replace_existing: bool = False) -> Dict:
        """
        Resolve a matching error.
        
        Args:
            error_id: ID of the error to resolve
            resolution_action: Description of resolution action taken
            replace_existing: If True, replace the existing match with the new one
            
        Returns:
            Resolution result dictionary
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get error details
            cursor.execute("SELECT * FROM matching_errors WHERE id = ?", (error_id,))
            error = cursor.fetchone()
            
            if not error:
                raise ValueError(f"Matching error {error_id} not found")
            
            if replace_existing and error['existing_match_id']:
                # Remove the existing match
                cursor.execute("""
                    UPDATE match_decisions 
                    SET decision_status = 'replaced', 
                        user_notes = COALESCE(user_notes, '') || '; Replaced due to conflict resolution',
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (error['existing_match_id'],))
                
                logger.info(f"🔄 Marked existing match {error['existing_match_id']} as replaced")
            
            # Mark error as resolved
            cursor.execute("""
                UPDATE matching_errors 
                SET resolution_status = 'resolved',
                    resolution_action = ?,
                    resolution_date = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (resolution_action, error_id))
            
            conn.commit()
            
            result = {
                'error_id': error_id,
                'resolution_action': resolution_action,
                'existing_match_replaced': replace_existing,
                'resolved_at': datetime.now().isoformat()
            }
            
            logger.info(f"✅ Resolved matching error {error_id}: {resolution_action}")
            return result
    
    def get_conflict_summary(self) -> Dict:
        """Get a summary of matching conflicts and their status."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Count errors by type and status
            cursor.execute("""
                SELECT 
                    error_type,
                    resolution_status,
                    COUNT(*) as count
                FROM matching_errors 
                GROUP BY error_type, resolution_status
            """)
            
            error_summary = {}
            for row in cursor.fetchall():
                error_type = row['error_type']
                if error_type not in error_summary:
                    error_summary[error_type] = {}
                error_summary[error_type][row['resolution_status']] = row['count']
            
            # Count non-matches
            cursor.execute("SELECT COUNT(*) as count FROM non_matches WHERE permanent_exclusion = 1")
            non_match_count = cursor.fetchone()['count']
            
            # Count total matches by status
            cursor.execute("""
                SELECT decision_status, COUNT(*) as count 
                FROM match_decisions 
                GROUP BY decision_status
            """)
            
            match_summary = {}
            for row in cursor.fetchall():
                match_summary[row['decision_status']] = row['count']
            
            return {
                'matching_errors': error_summary,
                'non_matches': non_match_count,
                'match_decisions': match_summary,
                'generated_at': datetime.now().isoformat()
            }
    
    def get_existing_decisions(self) -> Dict[Tuple[str, str], str]:
        """
        Get all existing match decisions as a lookup dictionary.
        
        Returns:
            Dictionary mapping (sell_tcgplayer_id, buy_product_id) -> decision_status
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT sell_tcgplayer_id, buy_product_id, decision_status 
                FROM match_decisions 
                WHERE decision_status IN ('accepted', 'rejected', 'auto_accepted')
            """)
            
            decisions = {}
            for row in cursor.fetchall():
                key = (row['sell_tcgplayer_id'], row['buy_product_id'])
                decisions[key] = row['decision_status']
            
            logger.info(f"📋 Retrieved {len(decisions)} existing match decisions")
            return decisions
    
    def get_accepted_sell_ids(self) -> Dict[str, str]:
        """
        Get sell TCGPlayer IDs that already have accepted matches.
        
        Returns:
            Dictionary mapping sell_tcgplayer_id -> decision_status
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT sell_tcgplayer_id, decision_status 
                FROM match_decisions 
                WHERE decision_status IN ('accepted', 'auto_accepted')
            """)
            
            decisions = {}
            for row in cursor.fetchall():
                decisions[row['sell_tcgplayer_id']] = row['decision_status']
            
            logger.info(f"📋 Retrieved {len(decisions)} sell items with accepted matches")
            return decisions
    
    def save_match_session(self, session_data: Dict) -> int:
        """
        Save matching session metadata.
        
        Args:
            session_data: Session metadata dictionary
            
        Returns:
            Session ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO match_sessions (
                    total_selllist_items, total_buylist_items, total_matches_found,
                    similarity_threshold, max_matches_per_item, auto_accept_threshold,
                    processing_time_seconds, match_config
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_data.get('total_selllist_items', 0),
                session_data.get('total_buylist_items', 0),
                session_data.get('total_matches_found', 0),
                session_data.get('similarity_threshold', 0.0),
                session_data.get('max_matches_per_item', 0),
                session_data.get('auto_accept_threshold'),
                session_data.get('processing_time_seconds', 0.0),
                json.dumps(session_data.get('config', {}))
            ))
            
            session_id = cursor.lastrowid
            conn.commit()
            
            logger.info(f"💾 Saved match session {session_id}")
            return session_id
    
    def get_match_statistics(self) -> Dict:
        """Get statistics about match decisions."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Overall statistics
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_decisions,
                    COUNT(CASE WHEN decision_status = 'accepted' THEN 1 END) as accepted_count,
                    COUNT(CASE WHEN decision_status = 'auto_accepted' THEN 1 END) as auto_accepted_count,
                    COUNT(CASE WHEN decision_status = 'rejected' THEN 1 END) as rejected_count,
                    COUNT(CASE WHEN decision_status = 'pending' THEN 1 END) as pending_count,
                    AVG(similarity_score) as avg_similarity,
                    MAX(similarity_score) as max_similarity,
                    MIN(similarity_score) as min_similarity
                FROM match_decisions
            """)
            
            stats = dict(cursor.fetchone())
            
            # Recent activity
            cursor.execute("""
                SELECT COUNT(*) as recent_decisions
                FROM match_decisions 
                WHERE save_date >= datetime('now', '-1 day')
            """)
            
            stats['recent_decisions'] = cursor.fetchone()['recent_decisions']
            
            return stats
    
    def clear_pending_decisions(self):
        """Clear all pending decisions (useful for fresh matching runs)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM match_decisions WHERE decision_status = 'pending'")
            deleted_count = cursor.rowcount
            conn.commit()
            
            logger.info(f"🗑️ Cleared {deleted_count} pending decisions")
            return deleted_count
    
    def get_all_match_data(self) -> List[Dict]:
        """
        Retrieve all match decisions with full details for export.
        
        Returns:
            List of dictionaries containing complete match information
        """
        import json
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    id,
                    sell_tcgplayer_id,
                    sell_product_name,
                    sell_set_name,
                    buy_product_id,
                    buy_card_name,
                    buy_edition,
                    similarity_score,
                    decision_status,
                    auto_accept_threshold,
                    user_notes,
                    save_date,
                    created_at,
                    updated_at
                FROM match_decisions 
                ORDER BY save_date DESC, sell_tcgplayer_id, similarity_score DESC
            """)
            
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            
            # Convert to list of dictionaries
            match_data = []
            for row in rows:
                row_dict = dict(zip(columns, row))
                match_data.append(row_dict)
            
            return match_data
    
    def export_decisions(self, filepath: str, status_filter: Optional[List[str]] = None):
        """
        Export match decisions to CSV.
        
        Args:
            filepath: Output file path
            status_filter: List of statuses to include (default: all)
        """
        import pandas as pd
        
        with self.get_connection() as conn:
            query = "SELECT * FROM match_decisions"
            if status_filter:
                placeholders = ','.join(['?' for _ in status_filter])
                query += f" WHERE decision_status IN ({placeholders})"
                df = pd.read_sql_query(query, conn, params=status_filter)
            else:
                df = pd.read_sql_query(query, conn)
        
        df.to_csv(filepath, index=False)
        logger.info(f"📊 Exported {len(df)} decisions to {filepath}")


# Global database instance
match_db = MatchDatabase()