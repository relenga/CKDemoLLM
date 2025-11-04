"""
Preprocessing module for Part Matching Engine
Handles text normalization and composite field generation for matching
"""

import pandas as pd
import re
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


def normalize_text(text: str) -> str:
    """
    Normalize text for consistent matching.
    
    Args:
        text: Raw text string
        
    Returns:
        Normalized lowercase text with cleaned punctuation
    """
    if pd.isna(text) or text is None:
        return ""
    
    # Convert to string and lowercase
    text = str(text).lower().strip()
    
    # Remove extra whitespace and punctuation
    text = re.sub(r'[^\w\s]', ' ', text)  # Replace punctuation with spaces
    text = re.sub(r'\s+', ' ', text)      # Collapse multiple spaces
    
    return text.strip()


def create_composite_field(df: pd.DataFrame, dataset_type: str, feature_config: Optional[Dict] = None) -> pd.DataFrame:
    """
    Create a composite text field combining key matching attributes.
    
    Args:
        df: Input DataFrame (BuyList or SellList)
        dataset_type: Either 'buylist' or 'selllist' to determine column names
        feature_config: Optional dict to control which features to include
        
    Returns:
        DataFrame with added 'composite_match_text' column
    """
    df_copy = df.copy()
    
    # Default feature configuration if not provided
    if feature_config is None:
        feature_config = {
            'use_card_names': True,
            'use_set_names': True,
            'use_rarity': True,
            'use_foil_status': True
        }
    
    if dataset_type.lower() == 'buylist':
        # BuyList column names from COLUMN_MAPPING
        name_col = 'BuyCardName'
        edition_col = 'BuyEdition'  
        rarity_col = 'BuyRarity'
        foil_col = 'BuyFoil'
        # price_col = 'BuyPrice'  # Placeholder for future enhancement
        
    elif dataset_type.lower() == 'selllist':
        # SellList column names from CSV_COLUMN_MAPPING
        name_col = 'SellProductName'
        edition_col = 'SellSetName'  # Maps to Set Name
        rarity_col = 'SellRarity'
        # Note: SellList doesn't have explicit foil field, may need to extract from name
        foil_col = None  # Will handle this specially
        # price_col = 'SellMarketPrice'  # Placeholder for future enhancement
        
    else:
        raise ValueError(f"dataset_type must be 'buylist' or 'selllist', got: {dataset_type}")
    
    # Build composite text components based on feature configuration
    components = []
    
    # Add normalized card name (if enabled)
    if feature_config.get('use_card_names', True) and name_col in df_copy.columns:
        normalized_names = df_copy[name_col].apply(normalize_text)
        components.append(normalized_names)
    
    # Add normalized edition/set (if enabled)
    if feature_config.get('use_set_names', True) and edition_col in df_copy.columns:
        normalized_editions = df_copy[edition_col].apply(normalize_text)
        components.append(normalized_editions)
    
    # Add normalized rarity (if enabled)
    if feature_config.get('use_rarity', True) and rarity_col in df_copy.columns:
        normalized_rarity = df_copy[rarity_col].apply(normalize_text)
        components.append(normalized_rarity)
    
    # Handle foil information (if enabled)
    if feature_config.get('use_foil_status', True):
        if foil_col and foil_col in df_copy.columns:
            # For BuyList: explicit foil field
            foil_text = df_copy[foil_col].apply(lambda x: 'foil' if x else 'nonfoil')
            components.append(foil_text)
        elif dataset_type.lower() == 'selllist':
            # For SellList: try to extract foil from product name
            foil_indicators = df_copy[name_col].apply(detect_foil_from_name)
            components.append(foil_indicators)
    
    # Placeholder for future pricing inclusion
    # if include_pricing:
    #     if price_col in df_copy.columns:
    #         price_ranges = df_copy[price_col].apply(categorize_price_range)
    #         components.append(price_ranges)
    
    # Combine all components into composite field
    if components:
        df_copy['composite_match_text'] = pd.Series([' '.join(row) for row in zip(*components)])
    else:
        df_copy['composite_match_text'] = ''
        logger.warning(f"No valid columns found for {dataset_type} composite field")
    
    logger.info(f"✅ Created composite field for {len(df_copy)} {dataset_type} records")
    return df_copy


def detect_foil_from_name(product_name: str) -> str:
    """
    Attempt to detect if a card is foil from its product name.
    
    Args:
        product_name: Product name string
        
    Returns:
        'foil' or 'nonfoil'
    """
    if pd.isna(product_name):
        return 'nonfoil'
    
    name_lower = str(product_name).lower()
    foil_keywords = ['foil', 'borderless', 'showcase', 'extended art', 'alternate art']
    
    for keyword in foil_keywords:
        if keyword in name_lower:
            return 'foil'
    
    return 'nonfoil'


def preprocess_dataframe(df: pd.DataFrame, dataset_type: str, feature_config: Optional[Dict] = None) -> pd.DataFrame:
    """
    Complete preprocessing pipeline for a dataset.
    
    Args:
        df: Raw DataFrame 
        dataset_type: 'buylist' or 'selllist'
        feature_config: Optional dict to control which features to include
        
    Returns:
        Preprocessed DataFrame ready for vectorization
    """
    logger.info(f"🔄 Starting preprocessing for {dataset_type} with {len(df)} records")
    
    # Add composite matching field with feature selection
    processed_df = create_composite_field(df, dataset_type, feature_config)
    
    # Log sample composite fields for validation
    if len(processed_df) > 0:
        sample_composite = processed_df['composite_match_text'].head(3).tolist()
        logger.info(f"📝 Sample composite fields: {sample_composite}")
    
    logger.info(f"✅ Preprocessing complete for {dataset_type}")
    return processed_df


# Placeholder for future price categorization
def categorize_price_range(price: float) -> str:
    """
    Categorize price into ranges for matching (future enhancement).
    
    Args:
        price: Numeric price value
        
    Returns:
        Price category string
    """
    if pd.isna(price):
        return 'unknown'
    
    try:
        price_val = float(price)
        if price_val < 1:
            return 'budget'
        elif price_val < 10:
            return 'low'
        elif price_val < 50:
            return 'mid'
        else:
            return 'high'
    except (ValueError, TypeError):
        return 'unknown'