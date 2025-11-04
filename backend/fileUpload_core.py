"""
Core functions for file upload processing - buylist and selllist data.
Handles both Card Kingdom API data (buylist) and CSV file uploads (selllist).
Extracted for testing without FastAPI dependencies.
"""

import json
import logging
import pandas as pd
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global dataframes to store the buylist and selllist data
_buylist_dataframe: Optional[pd.DataFrame] = None
_selllist_dataframe: Optional[pd.DataFrame] = None

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

# CSV column mapping for selllist data
CSV_COLUMN_MAPPING = {
    "TCGplayer Id": "TCGplayerId",
    "Product Line": "SellProductLine", 
    "Set Name": "SellSetName",
    "Product Name": "SellProductName",
    "Number": "SellNumber",
    "Rarity": "SellRarity",
    "Condition": "SellCondition",
    "TCG Market Price": "SellMarketPrice",
    "TCG Low Price": "SellLowPrice",
    "Total Quantity": "SellQuantity"
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
    """Transform a single record using the column mapping with proper type conversion."""
    transformed_record = {}
    for old_key, new_key in COLUMN_MAPPING.items():
        if old_key in record:
            value = record[old_key]
            
            # Convert numeric fields to proper types
            if new_key in ['BuyPrice', 'BuyQty', 'BuyProductId']:
                try:
                    if new_key == 'BuyProductId':
                        # Product ID should be an integer
                        transformed_record[new_key] = int(value) if value != '' else None
                    else:
                        # Price and Quantity should be floats
                        transformed_record[new_key] = float(value) if value != '' else 0.0
                except (ValueError, TypeError):
                    # If conversion fails, set appropriate default
                    if new_key == 'BuyProductId':
                        transformed_record[new_key] = None
                    else:
                        transformed_record[new_key] = 0.0
            elif new_key == 'BuyFoil':
                # Convert foil status to boolean
                transformed_record[new_key] = str(value).lower() == 'true'
            else:
                # Keep strings as-is
                transformed_record[new_key] = value
                
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
        
        # Ensure proper data types after DataFrame creation
        try:
            _buylist_dataframe['BuyPrice'] = pd.to_numeric(_buylist_dataframe['BuyPrice'], errors='coerce').fillna(0.0)
            _buylist_dataframe['BuyQty'] = pd.to_numeric(_buylist_dataframe['BuyQty'], errors='coerce').fillna(0.0)
            _buylist_dataframe['BuyProductId'] = pd.to_numeric(_buylist_dataframe['BuyProductId'], errors='coerce').fillna(0).astype(int)
            _buylist_dataframe['BuyFoil'] = _buylist_dataframe['BuyFoil'].astype(bool)
            logger.info("✅ Applied proper data types to DataFrame")
        except Exception as e:
            logger.warning(f"⚠️ Could not apply all data types: {e}")
        
        logger.info(f"💾 Saved {len(transformed_records)} records to buylist dataframe")
        
        # Log dataframe info
        memory_usage = _buylist_dataframe.memory_usage(deep=True).sum() / (1024 * 1024)
        logger.info(f"📊 Dataframe size: {len(_buylist_dataframe)} rows, {len(_buylist_dataframe.columns)} columns, {memory_usage:.2f} MB")
    
    logger.info(f"Successfully processed {len(transformed_records)} records")
    
    return transformed_records, len(data)


# ============================================================================
# SELLLIST FUNCTIONS (CSV Processing)
# ============================================================================

def clear_selllist_dataframe():
    """Clear the existing selllist dataframe before loading new data."""
    global _selllist_dataframe
    _selllist_dataframe = None
    logger.info("🗑️ Cleared existing selllist dataframe")


def get_selllist_dataframe() -> Optional[pd.DataFrame]:
    """Get the current selllist dataframe."""
    return _selllist_dataframe


def get_selllist_stats() -> Dict[str, Any]:
    """Get statistics about the current selllist dataframe."""
    global _selllist_dataframe
    
    if _selllist_dataframe is None:
        return {"status": "empty", "records": 0, "memory_mb": 0}
    
    memory_usage = _selllist_dataframe.memory_usage(deep=True).sum() / (1024 * 1024)
    
    return {
        "status": "loaded",
        "records": len(_selllist_dataframe),
        "columns": list(_selllist_dataframe.columns),
        "memory_mb": round(float(memory_usage), 2),
        "dtypes": {col: str(dtype) for col, dtype in _selllist_dataframe.dtypes.to_dict().items()}
    }


def get_selllist_sample(num_records: int = 5) -> Dict[str, Any]:
    """Get a sample of records from the selllist dataframe for validation."""
    global _selllist_dataframe
    
    if _selllist_dataframe is None:
        return {"status": "empty", "message": "No data loaded"}
    
    sample_data = _selllist_dataframe.head(num_records).to_dict('records')
    
    return {
        "status": "loaded",
        "total_records": len(_selllist_dataframe),
        "sample_size": len(sample_data),
        "sample_data": sample_data,
        "columns": list(_selllist_dataframe.columns)
    }


def process_selllist_file(file_content: bytes, filename: str, save_to_dataframe: bool = True) -> tuple[pd.DataFrame, int, int]:
    """
    Process CSV or XLSX file content and return dataframe, original count, and filtered count.
    
    Args:
        file_content: Raw file content as bytes
        filename: Name of the file to determine format
        save_to_dataframe: Whether to save the filtered dataset to a dataframe
        
    Returns:
        Tuple of (filtered_dataframe, original_count, filtered_count)
        
    Raises:
        ValueError: If file parsing fails or required columns are missing
    """
    global _selllist_dataframe
    
    # Clear existing data before processing new data
    if save_to_dataframe:
        clear_selllist_dataframe()
    
    # Determine file type from filename
    file_ext = filename.lower().split('.')[-1]
    logger.info(f"🔄 Processing selllist {file_ext.upper()} data...")
    
    try:
        # Read file content into dataframe based on file type
        if file_ext == 'csv':
            from io import StringIO
            # Decode bytes to string for CSV
            try:
                file_str = file_content.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    file_str = file_content.decode('latin-1')
                    logger.info("📄 Used latin-1 encoding for CSV file")
                except UnicodeDecodeError:
                    file_str = file_content.decode('cp1252')
                    logger.info("📄 Used cp1252 encoding for CSV file")
            
            df_original = pd.read_csv(StringIO(file_str))
        elif file_ext in ['xlsx', 'xls']:
            from io import BytesIO
            # Use bytes directly for Excel files
            df_original = pd.read_excel(BytesIO(file_content), engine='openpyxl' if file_ext == 'xlsx' else 'xlrd')
        else:
            raise ValueError(f"Unsupported file format: {file_ext}. Please use CSV or XLSX files.")
        
        original_count = len(df_original)
        
        logger.info(f"📊 Original CSV: {original_count} rows, {len(df_original.columns)} columns")
        logger.info(f"📋 Original columns: {list(df_original.columns)}")
        
        # Validate required columns exist
        missing_columns = []
        for csv_col in CSV_COLUMN_MAPPING.keys():
            if csv_col not in df_original.columns:
                missing_columns.append(csv_col)
        
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # Apply column mapping (rename columns)
        df_mapped = df_original.rename(columns=CSV_COLUMN_MAPPING)
        logger.info(f"✅ Applied column mapping: {len(CSV_COLUMN_MAPPING)} columns renamed")
        
        # Apply filtering rules
        df_filtered = df_mapped.copy()
        
        # Filter 1: Remove rows with empty TCGplayerId
        before_tcg_filter = len(df_filtered)
        df_filtered = df_filtered[df_filtered['TCGplayerId'].notna()]
        df_filtered = df_filtered[df_filtered['TCGplayerId'] != '']
        df_filtered = df_filtered[df_filtered['TCGplayerId'] != 0]
        after_tcg_filter = len(df_filtered)
        logger.info(f"🔍 TCGplayerId filter: {before_tcg_filter} → {after_tcg_filter} rows ({before_tcg_filter - after_tcg_filter} removed)")
        
        # Filter 2: Keep only Magic products (contains "Magic" in Product Line)
        before_magic_filter = len(df_filtered)
        df_filtered = df_filtered[df_filtered['SellProductLine'].str.contains('Magic', na=False)]
        after_magic_filter = len(df_filtered)
        logger.info(f"🔍 Magic filter: {before_magic_filter} → {after_magic_filter} rows ({before_magic_filter - after_magic_filter} removed)")
        
        filtered_count = len(df_filtered)
        
        # Save to dataframe if requested
        if save_to_dataframe and not df_filtered.empty:
            _selllist_dataframe = df_filtered.copy()
            logger.info(f"💾 Saved {filtered_count} records to selllist dataframe")
            
            # Log dataframe info
            memory_usage = _selllist_dataframe.memory_usage(deep=True).sum() / (1024 * 1024)
            logger.info(f"📊 Selllist dataframe: {len(_selllist_dataframe)} rows, {len(_selllist_dataframe.columns)} columns, {memory_usage:.2f} MB")
        
        logger.info(f"✅ Successfully processed {file_ext.upper()}: {original_count} → {filtered_count} records after filtering")
        
        return df_filtered, original_count, filtered_count
        
    except pd.errors.EmptyDataError:
        raise ValueError(f"{file_ext.upper()} file is empty or contains no data")
    except pd.errors.ParserError as e:
        raise ValueError(f"Failed to parse {file_ext.upper()} data: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error processing {file_ext.upper()}: {e}")
        raise ValueError(f"Failed to process {file_ext.upper()} data: {str(e)}")


def process_selllist_csv(csv_content: str, save_to_dataframe: bool = True) -> tuple[pd.DataFrame, int, int]:
    """
    Backward compatibility function for CSV processing.
    
    Args:
        csv_content: Raw CSV content as string
        save_to_dataframe: Whether to save the filtered dataset to a dataframe
        
    Returns:
        Tuple of (filtered_dataframe, original_count, filtered_count)
    """
    # Convert string to bytes for the new function
    csv_bytes = csv_content.encode('utf-8')
    return process_selllist_file(csv_bytes, 'file.csv', save_to_dataframe)