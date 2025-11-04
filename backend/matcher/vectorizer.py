"""
Text vectorization module for Part Matching Engine
Handles TF-IDF vectorization and similarity computation
"""

import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import logging
from typing import Tuple, Dict, List, Optional
import pickle
import os

logger = logging.getLogger(__name__)


class TextVectorizer:
    """
    Handles TF-IDF vectorization and cosine similarity computation
    for card matching between BuyList and SellList datasets.
    """
    
    def __init__(self, 
                 max_features: int = 10000,
                 ngram_range: Tuple[int, int] = (1, 3),
                 min_df: int = 2,
                 max_df: float = 0.8):
        """
        Initialize the vectorizer with TF-IDF parameters.
        
        Args:
            max_features: Maximum number of TF-IDF features
            ngram_range: N-gram range for tokenization
            min_df: Minimum document frequency
            max_df: Maximum document frequency
        """
        self.max_features = max_features
        self.ngram_range = ngram_range
        self.min_df = min_df
        self.max_df = max_df
        
        self.vectorizer = TfidfVectorizer(
            max_features=self.max_features,
            ngram_range=self.ngram_range,
            min_df=self.min_df,
            max_df=self.max_df,
            stop_words=None,  # Keep all words for card names
            lowercase=True,
            analyzer='word'
        )
        
        self.buylist_vectors = None
        self.selllist_vectors = None
        self.is_fitted = False
        
        logger.info(f"🔧 Initialized TextVectorizer with {max_features} features, "
                   f"n-grams: {ngram_range}, min_df: {min_df}, max_df: {max_df}")
    
    
    def fit_transform(self, 
                     buylist_df: pd.DataFrame, 
                     selllist_df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Fit the vectorizer on combined corpus and transform both datasets.
        
        Args:
            buylist_df: Preprocessed BuyList DataFrame with composite_match_text
            selllist_df: Preprocessed SellList DataFrame with composite_match_text
            
        Returns:
            Tuple of (buylist_vectors, selllist_vectors)
        """
        logger.info("🔄 Starting TF-IDF vectorization...")
        
        # Extract composite text fields
        buylist_texts = buylist_df['composite_match_text'].fillna('').tolist()
        selllist_texts = selllist_df['composite_match_text'].fillna('').tolist()
        
        # Combine for vocabulary building
        all_texts = buylist_texts + selllist_texts
        
        logger.info(f"📊 Fitting vectorizer on {len(all_texts)} total documents "
                   f"({len(buylist_texts)} BuyList + {len(selllist_texts)} SellList)")
        
        # Fit vectorizer on combined corpus
        self.vectorizer.fit(all_texts)
        self.is_fitted = True
        
        # Transform each dataset
        self.buylist_vectors = self.vectorizer.transform(buylist_texts)
        self.selllist_vectors = self.vectorizer.transform(selllist_texts)
        
        logger.info(f"✅ Vectorization complete. Vocabulary size: {len(self.vectorizer.vocabulary_)}")
        logger.info(f"📈 BuyList vectors shape: {self.buylist_vectors.shape}")
        logger.info(f"📈 SellList vectors shape: {self.selllist_vectors.shape}")
        
        return self.buylist_vectors, self.selllist_vectors
    
    
    def compute_similarity_matrix(self, 
                                 similarity_threshold: float = 0.1) -> np.ndarray:
        """
        Compute cosine similarity matrix between SellList and BuyList.
        
        Args:
            similarity_threshold: Minimum similarity to store (for memory efficiency)
            
        Returns:
            Similarity matrix [selllist_rows x buylist_rows]
        """
        if not self.is_fitted or self.buylist_vectors is None or self.selllist_vectors is None:
            raise ValueError("Must call fit_transform() before computing similarity")
        
        logger.info("🔄 Computing cosine similarity matrix...")
        
        # Compute similarity: SellList (rows) x BuyList (columns)
        similarity_matrix = cosine_similarity(
            self.selllist_vectors, 
            self.buylist_vectors
        )
        
        # Apply threshold for memory efficiency
        similarity_matrix[similarity_matrix < similarity_threshold] = 0
        
        logger.info(f"✅ Similarity matrix computed: {similarity_matrix.shape}")
        logger.info(f"📊 Non-zero similarities: {np.count_nonzero(similarity_matrix):,} / "
                   f"{similarity_matrix.size:,} ({100 * np.count_nonzero(similarity_matrix) / similarity_matrix.size:.2f}%)")
        
        return similarity_matrix
    
    
    def get_top_matches(self, 
                       similarity_matrix: np.ndarray,
                       selllist_df: pd.DataFrame,
                       buylist_df: pd.DataFrame,
                       top_k: int = 5,
                       min_similarity: float = 0.2) -> pd.DataFrame:
        """
        Extract top matches for each SellList item.
        
        Args:
            similarity_matrix: Precomputed similarity matrix
            selllist_df: Original SellList DataFrame
            buylist_df: Original BuyList DataFrame  
            top_k: Maximum matches per SellList item
            min_similarity: Minimum similarity threshold
            
        Returns:
            DataFrame with match results
        """
        logger.info(f"🔍 Extracting top {top_k} matches with min similarity {min_similarity}")
        
        matches = []
        sellitem_counter = 1  # Sequential selllist item number
        
        for sell_idx in range(len(selllist_df)):
            # Get similarities for this SellList item
            sell_similarities = similarity_matrix[sell_idx]
            
            # Find indices of top matches above threshold
            valid_indices = np.where(sell_similarities >= min_similarity)[0]
            
            if len(valid_indices) > 0:
                # Sort by similarity (descending) and take top_k
                top_indices = valid_indices[np.argsort(sell_similarities[valid_indices])][::-1][:top_k]
                
                # Create match records
                for match_rank, buy_idx in enumerate(top_indices, 1):
                    similarity_score = sell_similarities[buy_idx]
                    
                    # Get original data
                    sell_record = selllist_df.iloc[sell_idx]
                    buy_record = buylist_df.iloc[buy_idx]
                    
                    match_record = {
                        'sell_index': sell_idx,
                        'buy_index': buy_idx,
                        'similarity_score': float(similarity_score),
                        'match_rank': f"{sellitem_counter}-{match_rank}",
                        
                        # SellList fields
                        'sell_tcgplayer_id': sell_record.get('TCGplayerId', ''),
                        'sell_product_name': sell_record.get('SellProductName', ''),
                        'sell_set_name': sell_record.get('SellSetName', ''),
                        'sell_rarity': sell_record.get('SellRarity', ''),
                        'sell_market_price': sell_record.get('SellMarketPrice', 0),
                        'sell_quantity': sell_record.get('SellQuantity', 0),
                        
                        # BuyList fields  
                        'buy_product_id': buy_record.get('BuyProductId', ''),
                        'buy_card_name': buy_record.get('BuyCardName', ''),
                        'buy_edition': buy_record.get('BuyEdition', ''),
                        'buy_rarity': buy_record.get('BuyRarity', ''),
                        'buy_foil': buy_record.get('BuyFoil', False),
                        'buy_price': buy_record.get('BuyPrice', 0),
                        'buy_quantity': buy_record.get('BuyQty', 0),
                        'buy_image': buy_record.get('BuyImage', ''),
                    }
                    
                    matches.append(match_record)
                
                # Increment sellitem counter after processing each selllist item with matches
                sellitem_counter += 1
        
        matches_df = pd.DataFrame(matches)
        
        if len(matches_df) > 0:
            logger.info(f"✅ Found {len(matches_df)} total matches for {matches_df['sell_index'].nunique()} "
                       f"SellList items (avg {len(matches_df) / matches_df['sell_index'].nunique():.1f} matches per item)")
        else:
            logger.warning("⚠️  No matches found above similarity threshold")
        
        return matches_df
    
    
    def save_vectorizer(self, filepath: str) -> None:
        """Save fitted vectorizer to disk."""
        if not self.is_fitted:
            raise ValueError("Cannot save unfitted vectorizer")
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'wb') as f:
            pickle.dump({
                'vectorizer': self.vectorizer,
                'max_features': self.max_features,
                'ngram_range': self.ngram_range,
                'min_df': self.min_df,
                'max_df': self.max_df,
                'is_fitted': self.is_fitted
            }, f)
        
        logger.info(f"💾 Vectorizer saved to {filepath}")
    
    
    @classmethod
    def load_vectorizer(cls, filepath: str) -> 'TextVectorizer':
        """Load fitted vectorizer from disk."""
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
        
        instance = cls(
            max_features=data['max_features'],
            ngram_range=data['ngram_range'],
            min_df=data['min_df'],
            max_df=data['max_df']
        )
        
        instance.vectorizer = data['vectorizer']
        instance.is_fitted = data['is_fitted']
        
        logger.info(f"📂 Vectorizer loaded from {filepath}")
        return instance