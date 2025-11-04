"""
Core Part Matching Engine
Orchestrates preprocessing, vectorization, and matching logic
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional, Tuple
import time
from datetime import datetime

from .preprocess import preprocess_dataframe
from .vectorizer import TextVectorizer

logger = logging.getLogger(__name__)


class PartMatcher:
    """
    Main Part Matching Engine that orchestrates the complete matching pipeline
    from raw DataFrames to match results with similarity scores.
    """
    
    def __init__(self, 
                 similarity_threshold: float = 0.2,
                 max_matches_per_item: int = 5,
                 vectorizer_params: Optional[Dict] = None,
                 feature_config: Optional[Dict] = None):
        """
        Initialize the Part Matching Engine.
        
        Args:
            similarity_threshold: Minimum cosine similarity for valid matches
            max_matches_per_item: Maximum matches to return per SellList item
            vectorizer_params: Custom parameters for TF-IDF vectorizer
            feature_config: Configuration for feature selection in preprocessing
        """
        self.similarity_threshold = similarity_threshold
        self.max_matches_per_item = max_matches_per_item
        self.feature_config = feature_config
        
        # Initialize vectorizer with custom or default parameters
        if vectorizer_params is None:
            vectorizer_params = {
                'max_features': 10000,
                'ngram_range': (1, 3),
                'min_df': 2,
                'max_df': 0.8
            }
        
        self.vectorizer = TextVectorizer(**vectorizer_params)
        
        # State tracking
        self.last_match_time = None
        self.last_match_stats = {}
        self.buylist_processed = None
        self.selllist_processed = None
        
        logger.info(f"🚀 PartMatcher initialized with similarity_threshold={similarity_threshold}, "
                   f"max_matches_per_item={max_matches_per_item}")
    
    
    def process_datasets(self, 
                        buylist_df: pd.DataFrame, 
                        selllist_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Preprocess both datasets for matching.
        
        Args:
            buylist_df: Raw BuyList DataFrame
            selllist_df: Raw SellList DataFrame
            
        Returns:
            Tuple of (processed_buylist, processed_selllist)
        """
        logger.info("🔄 Processing datasets for matching...")
        
        # Preprocess datasets with feature configuration
        self.buylist_processed = preprocess_dataframe(buylist_df, 'buylist', self.feature_config)
        self.selllist_processed = preprocess_dataframe(selllist_df, 'selllist', self.feature_config)
        
        logger.info(f"✅ Datasets processed: {len(self.buylist_processed)} BuyList, "
                   f"{len(self.selllist_processed)} SellList records")
        
        return self.buylist_processed, self.selllist_processed
    
    
    def find_matches(self, 
                    buylist_df: pd.DataFrame, 
                    selllist_df: pd.DataFrame,
                    return_stats: bool = True) -> pd.DataFrame:
        """
        Find matches between SellList and BuyList using TF-IDF + cosine similarity.
        
        Args:
            buylist_df: Raw BuyList DataFrame  
            selllist_df: Raw SellList DataFrame
            return_stats: Whether to compute and store match statistics
            
        Returns:
            DataFrame with match results and similarity scores
        """
        start_time = time.time()
        logger.info("🎯 Starting Part Matching Engine...")
        
        # Step 1: Preprocess datasets
        buylist_processed, selllist_processed = self.process_datasets(buylist_df, selllist_df)
        
        # Step 2: Vectorize text fields
        logger.info("🔄 Vectorizing composite text fields...")
        buylist_vectors, selllist_vectors = self.vectorizer.fit_transform(
            buylist_processed, selllist_processed
        )
        
        # Step 3: Compute similarity matrix
        logger.info("🔄 Computing similarity matrix...")
        similarity_matrix = self.vectorizer.compute_similarity_matrix(
            similarity_threshold=self.similarity_threshold * 0.5  # Lower threshold for matrix computation
        )
        
        # Step 4: Extract top matches
        logger.info("🔄 Extracting top matches...")
        matches_df = self.vectorizer.get_top_matches(
            similarity_matrix=similarity_matrix,
            selllist_df=selllist_processed,
            buylist_df=buylist_processed,
            top_k=self.max_matches_per_item,
            min_similarity=self.similarity_threshold
        )
        
        # Step 5: Add match metadata
        if len(matches_df) > 0:
            matches_df['match_timestamp'] = datetime.now()
            matches_df['confidence_category'] = matches_df['similarity_score'].apply(self._categorize_confidence)
        
        # Track statistics
        processing_time = time.time() - start_time
        self.last_match_time = processing_time
        
        if return_stats:
            self.last_match_stats = self._compute_match_stats(matches_df, buylist_df, selllist_df, processing_time)
            self._log_match_summary()
        
        logger.info(f"✅ Matching complete in {processing_time:.2f} seconds")
        return matches_df
    
    
    def _categorize_confidence(self, similarity_score: float) -> str:
        """Categorize match confidence based on similarity score."""
        if similarity_score >= 0.8:
            return 'high'
        elif similarity_score >= 0.5:
            return 'medium'
        elif similarity_score >= 0.3:
            return 'low'
        else:
            return 'very_low'
    
    
    def _compute_match_stats(self, 
                            matches_df: pd.DataFrame,
                            buylist_df: pd.DataFrame,
                            selllist_df: pd.DataFrame,
                            processing_time: float) -> Dict:
        """Compute comprehensive matching statistics."""
        stats = {
            'processing_time_seconds': processing_time,
            'total_selllist_items': len(selllist_df),
            'total_buylist_items': len(buylist_df),
            'total_matches_found': len(matches_df),
            'selllist_items_with_matches': matches_df['sell_index'].nunique() if len(matches_df) > 0 else 0,
            'match_coverage_percent': 0,
            'average_matches_per_item': 0,
            'confidence_distribution': {}
        }
        
        if len(matches_df) > 0:
            stats['match_coverage_percent'] = (stats['selllist_items_with_matches'] / stats['total_selllist_items']) * 100
            stats['average_matches_per_item'] = stats['total_matches_found'] / stats['selllist_items_with_matches']
            
            # Confidence distribution
            confidence_counts = matches_df['confidence_category'].value_counts()
            stats['confidence_distribution'] = confidence_counts.to_dict()
            
            # Similarity score statistics
            stats['similarity_stats'] = {
                'min': float(matches_df['similarity_score'].min()),
                'max': float(matches_df['similarity_score'].max()),
                'mean': float(matches_df['similarity_score'].mean()),
                'median': float(matches_df['similarity_score'].median())
            }
        
        return stats
    
    
    def _log_match_summary(self) -> None:
        """Log a summary of matching results."""
        if not self.last_match_stats:
            return
        
        stats = self.last_match_stats
        logger.info("📊 === MATCH SUMMARY ===")
        logger.info(f"⏱️  Processing Time: {stats['processing_time_seconds']:.2f} seconds")
        logger.info(f"📦 SellList Items: {stats['total_selllist_items']:,}")
        logger.info(f"📦 BuyList Items: {stats['total_buylist_items']:,}")
        logger.info(f"🎯 Total Matches: {stats['total_matches_found']:,}")
        logger.info(f"📈 Coverage: {stats['match_coverage_percent']:.1f}% of SellList items have matches")
        
        if stats['total_matches_found'] > 0:
            logger.info(f"📊 Avg Matches/Item: {stats['average_matches_per_item']:.1f}")
            
            # Log confidence distribution
            conf_dist = stats['confidence_distribution']
            logger.info("🎯 Confidence Distribution:")
            for conf_level, count in conf_dist.items():
                percentage = (count / stats['total_matches_found']) * 100
                logger.info(f"   {conf_level}: {count:,} ({percentage:.1f}%)")
            
            # Log similarity stats
            sim_stats = stats['similarity_stats']
            logger.info(f"📏 Similarity Range: {sim_stats['min']:.3f} - {sim_stats['max']:.3f} "
                       f"(mean: {sim_stats['mean']:.3f}, median: {sim_stats['median']:.3f})")
        
        logger.info("📊 === END SUMMARY ===")
    
    
    def get_match_summary(self) -> Dict:
        """Get the last match statistics."""
        return self.last_match_stats.copy() if self.last_match_stats else {}
    
    
    def export_matches(self, 
                      matches_df: pd.DataFrame, 
                      filepath: str, 
                      format: str = 'excel') -> None:
        """
        Export match results to file.
        
        Args:
            matches_df: Match results DataFrame
            filepath: Output file path
            format: Export format ('excel', 'csv')
        """
        if format.lower() == 'excel':
            matches_df.to_excel(filepath, index=False)
        elif format.lower() == 'csv':
            matches_df.to_csv(filepath, index=False)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        logger.info(f"💾 Matches exported to {filepath}")
    
    
    def filter_matches(self, 
                      matches_df: pd.DataFrame,
                      min_similarity: Optional[float] = None,
                      confidence_levels: Optional[List[str]] = None,
                      max_matches_per_item: Optional[int] = None) -> pd.DataFrame:
        """
        Filter match results based on criteria.
        
        Args:
            matches_df: Original match results
            min_similarity: Minimum similarity threshold
            confidence_levels: List of confidence levels to include
            max_matches_per_item: Maximum matches per SellList item
            
        Returns:
            Filtered DataFrame
        """
        filtered_df = matches_df.copy()
        
        if min_similarity is not None:
            filtered_df = filtered_df[filtered_df['similarity_score'] >= min_similarity]
        
        if confidence_levels is not None:
            filtered_df = filtered_df[filtered_df['confidence_category'].isin(confidence_levels)]
        
        if max_matches_per_item is not None:
            # Keep top N matches per SellList item
            filtered_df = (filtered_df.sort_values(['sell_index', 'similarity_score'], ascending=[True, False])
                          .groupby('sell_index')
                          .head(max_matches_per_item)
                          .reset_index(drop=True))
        
        logger.info(f"🔍 Filtered matches: {len(filtered_df)} from {len(matches_df)} original matches")
        return filtered_df