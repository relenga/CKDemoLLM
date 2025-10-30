"""
Core functions for Card Kingdom buylist processing.
Extracted for testing without FastAPI dependencies.
"""

import json
import logging
import pandas as pd
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global dataframe to store the buylist data
_buylist_dataframe: Optional[pd.DataFrame] = None

# Constants
COLUMN_MAPPING = {
    "i": "BuyProductId",
    "n": "BuyCardName", 
    "e": "BuyEdition",
    "r": "BuyRarity",
    "f": "BuyFoil",
    "p": "BuyPrice",
    "q": "BuyQty",
    "u": "BuyImage"
}


def clean_jsonp_wrapper(raw_data: str) -> str:
    """Clean JSONP wrapper from Card Kingdom response."""
    stripped_data = raw_data.strip()
    
    if stripped_data.startswith('ckCardList(') and stripped_data.endswith(');'):
        # Remove ckCardList( from start and ); from end
        json_data = stripped_data[11:-2]
        logger.info("JSONP wrapper 'ckCardList();' detected and cleaned")
        return json_data
    elif stripped_data.startswith('(') and stripped_data.endswith(')'):
        # Generic JSONP wrapper
        json_data = stripped_data[1:-1]
        logger.info("Generic JSONP wrapper detected and cleaned")
        return json_data
    else:
        logger.warning("No JSONP wrapper found, using raw data")
        return stripped_data


def transform_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """Transform a single record using the column mapping."""
    transformed_record = {}
    for old_key, new_key in COLUMN_MAPPING.items():
        if old_key in record:
            transformed_record[new_key] = record[old_key]
    return transformed_record


def clear_buylist_dataframe():
    """Clear the existing buylist dataframe before loading new data."""
    global _buylist_dataframe
    _buylist_dataframe = None
    logger.info("🗑️ Cleared existing buylist dataframe")


def get_buylist_dataframe() -> Optional[pd.DataFrame]:
    """Get the current buylist dataframe."""
    return _buylist_dataframe


def get_buylist_stats() -> Dict[str, Any]:
    """Get statistics about the current buylist dataframe."""
    global _buylist_dataframe
    
    if _buylist_dataframe is None:
        return {"status": "empty", "records": 0, "memory_mb": 0}
    
    memory_usage = _buylist_dataframe.memory_usage(deep=True).sum() / (1024 * 1024)
    
    return {
        "status": "loaded",
        "records": len(_buylist_dataframe),
        "columns": list(_buylist_dataframe.columns),
        "memory_mb": round(memory_usage, 2),
        "dtypes": {col: str(dtype) for col, dtype in _buylist_dataframe.dtypes.to_dict().items()}
    }


def get_buylist_sample(num_records: int = 5) -> Dict[str, Any]:
    """Get a sample of records from the buylist dataframe for validation."""
    global _buylist_dataframe
    
    if _buylist_dataframe is None:
        return {"status": "empty", "message": "No data loaded"}
    
    sample_data = _buylist_dataframe.head(num_records).to_dict('records')
    
    return {
        "status": "loaded",
        "total_records": len(_buylist_dataframe),
        "sample_size": len(sample_data),
        "sample_data": sample_data,
        "columns": list(_buylist_dataframe.columns)
    }


def process_buylist_data(raw_jsonp: str, save_to_dataframe: bool = True) -> tuple[List[Dict[str, Any]], int]:
    """
    Process raw JSONP data and return transformed records and count.
    
    Args:
        raw_jsonp: Raw JSONP data from Card Kingdom API
        save_to_dataframe: Whether to save the full dataset to a dataframe
        
    Returns:
        Tuple of (transformed_records, total_count)
        
    Raises:
        ValueError: If JSON parsing fails
    """
    global _buylist_dataframe
    
    # Clear existing data before processing new data
    if save_to_dataframe:
        clear_buylist_dataframe()
    
    # Clean JSONP wrapper
    json_data = clean_jsonp_wrapper(raw_jsonp)
    
    # Parse JSON
    try:
        data = json.loads(json_data)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON data: {str(e)}")
    
    if not isinstance(data, list):
        raise ValueError("Expected JSON array, got different type")
    
    # Transform records
    transformed_records = [transform_record(record) for record in data]
    
    # Save to dataframe if requested
    if save_to_dataframe and transformed_records:
        _buylist_dataframe = pd.DataFrame(transformed_records)
        logger.info(f"💾 Saved {len(transformed_records)} records to buylist dataframe")
        
        # Log dataframe info
        memory_usage = _buylist_dataframe.memory_usage(deep=True).sum() / (1024 * 1024)
        logger.info(f"📊 Dataframe size: {len(_buylist_dataframe)} rows, {len(_buylist_dataframe.columns)} columns, {memory_usage:.2f} MB")
    
    logger.info(f"Successfully processed {len(transformed_records)} records")
    
    return transformed_records, len(data)