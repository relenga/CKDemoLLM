"""
CK LangGraph Backend API
A FastAPI backend for processing Card Kingdom buylist data.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
import time
import aiohttp
import json
import asyncio
import psutil
import os
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional

def clean_for_json(obj):
    """Recursively clean data structure for JSON serialization."""
    if isinstance(obj, dict):
        return {key: clean_for_json(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [clean_for_json(item) for item in obj]
    elif isinstance(obj, (np.integer, int)):
        return int(obj)
    elif isinstance(obj, (np.floating, float)):
        if np.isnan(obj) or np.isinf(obj):
            return None
        return float(obj)
    elif pd.isna(obj):
        return None
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    else:
        return obj

# Import core functions for buylist and selllist processing
from fileUpload_core import (
    clean_jsonp_wrapper, 
    transform_record, 
    COLUMN_MAPPING,
    CSV_COLUMN_MAPPING,
    process_buylist_data,
    get_buylist_dataframe,
    get_buylist_stats,
    clear_buylist_dataframe,
    get_buylist_sample,
    process_selllist_csv,
    process_selllist_file,
    get_selllist_dataframe,
    get_selllist_stats,
    clear_selllist_dataframe,
    get_selllist_sample
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import Part Matching Engine
try:
    from matcher import PartMatcher
    MATCHER_AVAILABLE = True
    logger.info("Part Matching Engine loaded successfully")
except ImportError as e:
    logger.warning(f"Part Matching Engine not available: {e}")
    PartMatcher = None
    MATCHER_AVAILABLE = False

# Import Database
try:
    from database import match_db
    DATABASE_AVAILABLE = True
    logger.info("Match database loaded successfully")
except ImportError as e:
    logger.warning(f"Match database not available: {e}")
    match_db = None
    DATABASE_AVAILABLE = False

# Global variable to store current match results (not accumulated)
_current_match_results = pd.DataFrame()

# Create the app
app = FastAPI(
    title="CK LangGraph Backend API",
    version="1.0.0",
    description="A FastAPI backend for processing Card Kingdom buylist data with LangGraph integration."
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Constants
CARD_KINGDOM_BUYLIST_URL = "https://www.cardkingdom.com/json/buylist.jsonp"

REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}


async def fetch_card_kingdom_data() -> str:
    """Fetch raw data from Card Kingdom buylist API."""
    timeout = aiohttp.ClientTimeout(total=120)
    async with aiohttp.ClientSession(timeout=timeout, headers=REQUEST_HEADERS) as session:
        async with session.get(CARD_KINGDOM_BUYLIST_URL) as response:
            if response.status != 200:
                raise HTTPException(
                    status_code=response.status,
                    detail=f"Failed to fetch data from Card Kingdom: {response.reason}"
                )
            
            raw_data = await response.text()
            if not raw_data or not raw_data.strip():
                raise HTTPException(
                    status_code=500,
                    detail="Empty response received from Card Kingdom API"
                )
            
            logger.info(f"Fetched {len(raw_data)} characters from Card Kingdom API")
            return raw_data


# Core functions are now imported from buylist_core.py


# Basic endpoints
@app.get("/")
async def root():
    return {
        "message": "CK LangGraph Backend API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/api/test")
async def test_endpoint():
    return {"message": "Test endpoint is working!", "status": "ok"}


# Buylist endpoints
@app.get("/api/buylist/test")
async def test_buylist_endpoint():
    return {"message": "Buylist endpoint is registered!", "status": "ok"}


@app.get("/api/buylist/stats")
async def get_buylist_statistics():
    """Get statistics about the current buylist dataframe."""
    stats = get_buylist_stats()
    return {
        "status": "success",
        "dataframe_stats": stats
    }


@app.delete("/api/buylist/clear")
async def clear_buylist():
    """Clear the current buylist dataframe."""
    clear_buylist_dataframe()
    return {
        "status": "success",
        "message": "Buylist dataframe cleared successfully"
    }


@app.post("/api/buylist/upload")
async def upload_buylist():
    """Upload and process Card Kingdom buylist data."""
    start_time = time.time()
    
    try:
        # Fetch raw data
        raw_data = await fetch_card_kingdom_data()
        
        # Process using core function (run in thread pool to avoid blocking)
        try:
            # Log memory before processing
            process = psutil.Process(os.getpid())
            memory_before = process.memory_info().rss / 1024 / 1024  # MB
            logger.info(f"Memory before processing: {memory_before:.1f} MB")
            logger.info(f"Data size to process: {len(raw_data):,} characters")
            
            # Run blocking operation in thread pool with timeout
            process_start = time.time()
            
            # 60 second timeout for processing
            transformed_records, total_count = await asyncio.wait_for(
                asyncio.get_running_loop().run_in_executor(None, process_buylist_data, raw_data, True),
                timeout=60.0
            )
            
            process_time = time.time() - process_start
            memory_after = process.memory_info().rss / 1024 / 1024  # MB
            logger.info(f"Processing completed in {process_time:.2f}s")
            logger.info(f"Memory after processing: {memory_after:.1f} MB")
            logger.info(f"Memory increase: {memory_after - memory_before:.1f} MB")
            
        except asyncio.TimeoutError:
            logger.error("Data processing timed out after 60 seconds")
            raise HTTPException(
                status_code=504,
                detail="Data processing timed out - dataset too large"
            )
        except ValueError as e:
            logger.error(f"Data processing failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=str(e)
            )
        
        # Get sample records (first 5) and ensure proper types
        sample_size = min(5, len(transformed_records))
        sample_data = []
        for i in range(sample_size):
            record = transformed_records[i].copy()
            # Ensure numeric fields are properly typed for JSON serialization
            if 'BuyPrice' in record:
                try:
                    record['BuyPrice'] = float(record['BuyPrice']) if record['BuyPrice'] != '' else 0.0
                except (ValueError, TypeError):
                    record['BuyPrice'] = 0.0
            if 'BuyQty' in record:
                try:
                    record['BuyQty'] = float(record['BuyQty']) if record['BuyQty'] != '' else 0.0
                except (ValueError, TypeError):
                    record['BuyQty'] = 0.0
            if 'BuyProductId' in record:
                try:
                    record['BuyProductId'] = int(record['BuyProductId']) if record['BuyProductId'] != '' else 0
                except (ValueError, TypeError):
                    record['BuyProductId'] = 0
            if 'BuyFoil' in record:
                record['BuyFoil'] = bool(record['BuyFoil']) if isinstance(record['BuyFoil'], bool) else str(record['BuyFoil']).lower() == 'true'
            sample_data.append(record)
        
        # Get dataframe statistics
        dataframe_stats = get_buylist_stats()
        
        total_processing_time = time.time() - start_time
        
        # Final memory check
        memory_final = process.memory_info().rss / 1024 / 1024  # MB
        logger.info(f"Total request completed in {total_processing_time:.2f}s")
        logger.info(f"Final memory usage: {memory_final:.1f} MB")
        
        return {
            "status": "success",
            "message": f"Successfully processed {total_count:,} records from Card Kingdom buylist",
            "total_records": total_count,
            "processing_time": round(total_processing_time, 2),
            "fetch_time": round(time.time() - start_time - process_time, 2),
            "process_time": round(process_time, 2),
            "sample_records": sample_data,
            "columns": list(COLUMN_MAPPING.values()),
            "dataframe_stats": dataframe_stats,
            "debug_info": {
                "memory_before_mb": round(memory_before, 1),
                "memory_after_mb": round(memory_after, 1),
                "memory_increase_mb": round(memory_after - memory_before, 1),
                "data_size_chars": len(raw_data)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Unexpected error processing buylist: {e}")
        return {
            "status": "error",
            "message": f"Error processing buylist: {str(e)}",
            "total_records": 0,
            "processing_time": round(processing_time, 2)
        }


@app.get("/api/buylist/sample")
async def get_buylist_sample_endpoint(records: int = 5):
    """Get a sample of records from the buylist dataframe."""
    from fileUpload_core import get_buylist_sample
    
    try:
        if records < 1 or records > 100:
            raise HTTPException(status_code=400, detail="Number of records must be between 1 and 100")
        
        result = get_buylist_sample(records)
        return result
        
    except Exception as e:
        logger.error(f"Error getting buylist sample: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting sample: {str(e)}")


# ============================================================================
# SELLLIST ENDPOINTS (CSV Processing)
# ============================================================================

@app.post("/api/selllist/upload")
async def upload_selllist(file: UploadFile = File(...)):
    """Upload and process CSV selllist data."""
    start_time = time.time()
    
    try:
        # Validate file type
        if not file.filename:
            raise HTTPException(
                status_code=400,
                detail="File name is required"
            )
        
        file_ext = file.filename.lower().split('.')[-1]
        if file_ext not in ['csv', 'xlsx', 'xls']:
            raise HTTPException(
                status_code=400,
                detail="Only CSV and XLSX files are supported"
            )
        
        # Log file info
        logger.info(f"📁 Processing uploaded file: {file.filename}")
        logger.info(f"📄 Content type: {file.content_type}")
        
        # Read file content (keep as bytes for both CSV and Excel)
        file_content = await file.read()
        
        if not file_content:
            raise HTTPException(
                status_code=400,
                detail=f"{file_ext.upper()} file is empty"
            )
        
        # Log memory before processing
        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        logger.info(f"Memory before processing: {memory_before:.1f} MB")
        logger.info(f"{file_ext.upper()} size to process: {len(file_content):,} bytes")
        
        # Process file using core function (run in thread pool to avoid blocking)
        try:
            process_start = time.time()
            
            # 60 second timeout for processing
            filtered_df, original_count, filtered_count = await asyncio.wait_for(
                asyncio.get_running_loop().run_in_executor(None, process_selllist_file, file_content, file.filename, True),
                timeout=60.0
            )
            
            process_time = time.time() - process_start
            memory_after = process.memory_info().rss / 1024 / 1024  # MB
            logger.info(f"Processing completed in {process_time:.2f}s")
            logger.info(f"Memory after processing: {memory_after:.1f} MB")
            logger.info(f"Memory increase: {memory_after - memory_before:.1f} MB")
            
        except asyncio.TimeoutError:
            logger.error(f"{file_ext.upper()} processing timed out after 60 seconds")
            raise HTTPException(
                status_code=504,
                detail=f"{file_ext.upper()} processing timed out - file too large"
            )
        except ValueError as e:
            logger.error(f"{file_ext.upper()} processing failed: {e}")
            raise HTTPException(
                status_code=400,
                detail=str(e)
            )
        
        # Get sample records (first 5) - handle NaN values for JSON serialization
        sample_size = min(5, len(filtered_df))
        if not filtered_df.empty:
            # Replace NaN/infinite values with None for JSON compatibility
            sample_df = filtered_df.head(sample_size).copy()
            sample_df = sample_df.replace([np.inf, -np.inf], None)
            sample_df = sample_df.where(sample_df.notna(), None)
            sample_data = sample_df.to_dict('records')
        else:
            sample_data = []
        
        # Get dataframe statistics
        dataframe_stats = get_selllist_stats()
        
        total_processing_time = time.time() - start_time
        
        # Final memory check
        memory_final = process.memory_info().rss / 1024 / 1024  # MB
        logger.info(f"Total request completed in {total_processing_time:.2f}s")
        
        response_data = {
            "status": "success",
            "message": f"Successfully processed {file_ext.upper()} file: {file.filename}",
            "original_records": f"{original_count:,}",
            "filtered_records": f"{filtered_count:,}",
            "records_removed": f"{original_count - filtered_count:,}",
            "processing_time": round(total_processing_time, 2),
            "process_time": round(process_time, 2),
            "sample_records": sample_data,
            "columns": list(CSV_COLUMN_MAPPING.values()),
            "dataframe_stats": dataframe_stats,
            "debug_info": {
                "memory_before_mb": round(memory_before, 1),
                "memory_after_mb": round(memory_after, 1),
                "memory_increase_mb": round(memory_after - memory_before, 1),
                "file_size_bytes": len(file_content),
                "filename": file.filename,
                "file_type": file_ext.upper()
            }
        }
        
        # Clean all data for JSON serialization
        return clean_for_json(response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Unexpected error processing selllist: {e}")
        return {
            "status": "error",
            "message": f"Error processing selllist: {str(e)}",
            "original_records": "0",
            "filtered_records": "0",
            "processing_time": round(processing_time, 2)
        }


@app.get("/api/selllist/stats")
async def get_selllist_stats_endpoint():
    """Get statistics about the current selllist dataframe."""
    try:
        stats = get_selllist_stats()
        return stats
        
    except Exception as e:
        logger.error(f"Error getting selllist stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")


@app.get("/api/selllist/sample")
async def get_selllist_sample_endpoint(records: int = 5):
    """Get a sample of records from the selllist dataframe."""
    try:
        if records < 1 or records > 100:
            raise HTTPException(status_code=400, detail="Number of records must be between 1 and 100")
        
        result = get_selllist_sample(records)
        return result
        
    except Exception as e:
        logger.error(f"Error getting selllist sample: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting sample: {str(e)}")


@app.delete("/api/selllist/clear")
async def clear_selllist_endpoint():
    """Clear the selllist dataframe."""
    try:
        clear_selllist_dataframe()
        return {
            "status": "success", 
            "message": "Selllist dataframe cleared successfully"
        }
        
    except Exception as e:
        logger.error(f"Error clearing selllist: {e}")
        raise HTTPException(status_code=500, detail=f"Error clearing selllist: {str(e)}")


# ================================
# PART MATCHING ENGINE ENDPOINTS
# ================================

@app.post("/api/matcher/find_matches")
async def find_matches_endpoint(
    similarity_threshold: float = 0.2,
    max_matches_per_item: int = 5,
    return_stats: bool = True,
    auto_accept_threshold: float = 0.9,
    skip_decided_items: bool = True,
    # Vectorizer Configuration Parameters
    max_features: int = 10000,
    ngram_min: int = 1,
    ngram_max: int = 3,
    min_doc_freq: int = 2,
    max_doc_freq: float = 0.8,
    use_card_names: bool = True,
    use_set_names: bool = True,
    use_rarity: bool = True,
    use_foil_status: bool = True
):
    """
    Find matches between SellList and BuyList using TF-IDF similarity matching.
    
    Args:
        similarity_threshold: Minimum cosine similarity for valid matches (0.0-1.0)
        max_matches_per_item: Maximum matches to return per SellList item
        return_stats: Whether to include match statistics in response
        auto_accept_threshold: Threshold for auto-accepting high-confidence matches (0.0-1.0)
        skip_decided_items: Whether to skip selllist items that already have accepted matches
        max_features: Maximum number of TF-IDF features (1000-50000)
        ngram_min: Minimum n-gram size (1-5)
        ngram_max: Maximum n-gram size (1-5)
        min_doc_freq: Minimum document frequency for terms (1-100)
        max_doc_freq: Maximum document frequency for terms (0.1-1.0)
        use_card_names: Include card names in matching features
        use_set_names: Include set names in matching features
        use_rarity: Include rarity in matching features
        use_foil_status: Include foil status in matching features
    
    Returns:
        JSON response with match results and optionally statistics
    """
    try:
        # Get current DataFrames
        buylist_df = get_buylist_dataframe()
        selllist_df = get_selllist_dataframe()
        
        if buylist_df is None or len(buylist_df) == 0:
            raise HTTPException(
                status_code=400, 
                detail="No BuyList data loaded. Please upload BuyList data first."
            )
        
        if selllist_df is None or len(selllist_df) == 0:
            raise HTTPException(
                status_code=400, 
                detail="No SellList data loaded. Please upload SellList data first."
            )
        
        # Validate parameters
        if not 0.0 <= similarity_threshold <= 1.0:
            raise HTTPException(
                status_code=400,
                detail="similarity_threshold must be between 0.0 and 1.0"
            )
        
        if max_matches_per_item < 1:
            raise HTTPException(
                status_code=400,
                detail="max_matches_per_item must be at least 1"
            )
        
        # Get existing decisions and non-matches to skip already decided items and forbidden pairs
        existing_decisions = {}
        accepted_sell_ids = {}
        non_matches = {}
        auto_accepted_count = 0
        
        if DATABASE_AVAILABLE and match_db is not None:
            existing_decisions = match_db.get_existing_decisions()
            accepted_sell_ids = match_db.get_accepted_sell_ids()
            non_matches = match_db.get_non_matches()
            logger.info(f"📋 Found {len(existing_decisions)} existing match decisions")
            logger.info(f"📋 Found {len(accepted_sell_ids)} sell items with accepted matches")
            logger.info(f"🚫 Found {len(non_matches)} non-match exclusions")
        
        # Filter selllist items if skipping decided items
        original_selllist_count = len(selllist_df)
        if skip_decided_items and accepted_sell_ids:
            # Remove selllist items that already have accepted matches
            # Find indices of selllist items with TCGplayerIds that are already accepted
            accepted_tcgplayer_ids = set(accepted_sell_ids.keys())
            mask = selllist_df['TCGplayerId'].astype(str).isin(accepted_tcgplayer_ids)
            decided_count = mask.sum()
            selllist_df = selllist_df[~mask].reset_index(drop=True)
            logger.info(f"🔍 Filtered selllist: {original_selllist_count} → {len(selllist_df)} items (skipped {decided_count} decided items)")
        
        if len(selllist_df) == 0:
            return {
                "status": "success",
                "message": "No new items to match - all selllist items already have decisions",
                "data": {
                    "total_matches": 0,
                    "matches": [],
                    "statistics": {
                        "processing_time_seconds": 0.0,
                        "total_selllist_items": original_selllist_count,
                        "skipped_decided_items": len(accepted_sell_ids),
                        "total_buylist_items": len(buylist_df),
                        "total_matches_found": 0
                    }
                }
            }
        
        logger.info(f"🎯 Starting Part Matching: {len(selllist_df)} SellList vs {len(buylist_df)} BuyList items")
        logger.info(f"🔧 Vectorizer Config: max_features={max_features}, ngrams=({ngram_min},{ngram_max}), "
                   f"min_df={min_doc_freq}, max_df={max_doc_freq}")
        logger.info(f"🎯 Auto-accept threshold: {auto_accept_threshold:.1%}")
        
        # Prepare vectorizer configuration
        vectorizer_params = {
            'max_features': max_features,
            'ngram_range': (ngram_min, ngram_max),
            'min_df': min_doc_freq,
            'max_df': max_doc_freq
        }
        
        # Prepare feature selection configuration
        feature_config = {
            'use_card_names': use_card_names,
            'use_set_names': use_set_names,
            'use_rarity': use_rarity,
            'use_foil_status': use_foil_status
        }
        
        # Check if matcher is available
        if not MATCHER_AVAILABLE or PartMatcher is None:
            raise HTTPException(
                status_code=503,
                detail="Part Matching Engine is not available"
            )
        
        # Initialize Part Matcher with custom configuration
        matcher = PartMatcher(
            similarity_threshold=similarity_threshold,
            max_matches_per_item=max_matches_per_item,
            vectorizer_params=vectorizer_params,
            feature_config=feature_config
        )
        
        # Find matches
        matches_df = matcher.find_matches(
            buylist_df=buylist_df,
            selllist_df=selllist_df,
            return_stats=return_stats
        )
        
        # Filter out non-matches (user-rejected pairs) and log filtered count
        original_match_count = len(matches_df)
        if len(matches_df) > 0 and non_matches:
            # Create a mask to filter out non-matches
            filtered_indices = []
            for idx, match in matches_df.iterrows():
                sell_id = str(match.get('sell_tcgplayer_id', ''))
                buy_id = str(match.get('buy_product_id', ''))
                non_match_key = (sell_id, buy_id)
                
                if non_match_key not in non_matches:
                    filtered_indices.append(idx)
                else:
                    logger.info(f"🚫 Filtered non-match: {sell_id} ↔ {buy_id} (reason: {non_matches[non_match_key]['rejection_reason']})")
            
            matches_df = matches_df.loc[filtered_indices].reset_index(drop=True)
            filtered_count = original_match_count - len(matches_df)
            if filtered_count > 0:
                logger.info(f"🚫 Filtered {filtered_count} matches due to non-match exclusions")
        
        # Process matches for auto-acceptance and database storage
        if DATABASE_AVAILABLE and match_db is not None and len(matches_df) > 0:
            # Initialize all matches as pending first
            matches_df['decision_status'] = 'pending'
            
            # Group matches by sell TCGPlayer ID to find the best match for auto-acceptance
            for sell_tcgplayer_id, group in matches_df.groupby('sell_tcgplayer_id'):
                # Get the best match (highest similarity) for this sell item
                best_match_idx = group['similarity_score'].idxmax()
                best_match = group.loc[best_match_idx]
                best_similarity = group['similarity_score'].max()
                
                # Check if best match exceeds auto-accept threshold
                if best_similarity >= auto_accept_threshold:
                    try:
                        # Auto-accept ONLY the best match with conflict detection
                        match_db.save_match_decision(
                            match_data=best_match.to_dict(),
                            decision_status='auto_accepted',
                            auto_accept_threshold=auto_accept_threshold
                        )
                        auto_accepted_count += 1
                        
                        # Update ONLY the best match status in the dataframe
                        matches_df.loc[best_match_idx, 'decision_status'] = 'auto_accepted'
                        
                        # Mark other matches for this sell item as rejected to maintain 1:1 relationship
                        other_matches_mask = (matches_df['sell_tcgplayer_id'] == sell_tcgplayer_id) & (matches_df.index != best_match_idx)
                        matches_df.loc[other_matches_mask, 'decision_status'] = 'auto_rejected'
                        
                    except ValueError as conflict_error:
                        # Handle conflicts during auto-accept - log and skip
                        logger.warning(f"🚨 Auto-accept conflict for sell_tcgplayer_id {sell_tcgplayer_id}: {conflict_error}")
                        matches_df.loc[best_match_idx, 'decision_status'] = 'conflict_blocked'
                        
                        # Don't mark other matches as auto-rejected if the best one failed
                        conflict_matches_mask = (matches_df['sell_tcgplayer_id'] == sell_tcgplayer_id) & (matches_df.index != best_match_idx)
                        matches_df.loc[conflict_matches_mask, 'decision_status'] = 'pending'
            
        # Save session metadata  
        session_data = {
            'total_selllist_items': original_selllist_count,
            'total_buylist_items': len(buylist_df),
            'total_matches_found': len(matches_df),
            'similarity_threshold': similarity_threshold,
            'max_matches_per_item': max_matches_per_item,
            'auto_accept_threshold': auto_accept_threshold,
            'processing_time_seconds': matcher.last_match_time,
            'config': {
                'skip_decided_items': skip_decided_items,
                'vectorizer_params': vectorizer_params,
                'feature_config': feature_config
            }
        }
        match_db.save_match_session(session_data)
        
        # Count auto-rejected matches for logging
        auto_rejected_count = len(matches_df[matches_df['decision_status'] == 'auto_rejected'])
        logger.info(f"✅ Auto-accepted {auto_accepted_count} best matches above {auto_accept_threshold:.1%} threshold")
        logger.info(f"🚫 Auto-rejected {auto_rejected_count} additional matches to maintain 1:1 relationship")
        
        # Add decision status to matches if not present
        if 'decision_status' not in matches_df.columns:
            matches_df['decision_status'] = 'pending'
        
        # Count various decision statuses for response
        auto_rejected_count = len(matches_df[matches_df['decision_status'] == 'auto_rejected']) if len(matches_df) > 0 else 0
        
        # Store current run results for export (not in database)
        global _current_match_results
        _current_match_results = matches_df.copy() if len(matches_df) > 0 else pd.DataFrame()
        
        # Prepare response  
        response = {
            "status": "success",
            "message": f"Part matching completed successfully - {auto_accepted_count} auto-accepted, {auto_rejected_count} auto-rejected",
            "data": {
                "total_matches": len(matches_df),
                "current_run_matches": len(matches_df),  # Clear indicator this is current run
                "auto_accepted_count": auto_accepted_count,
                "auto_rejected_count": auto_rejected_count,
                "matches": clean_for_json(matches_df.to_dict('records')) if len(matches_df) > 0 else []
            }
        }
        
        # Add statistics if requested
        if return_stats:
            match_stats = matcher.get_match_summary()
            response["data"]["statistics"] = clean_for_json(match_stats)
        
        logger.info(f"✅ Part matching complete: {len(matches_df)} matches found")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in part matching: {e}")
        raise HTTPException(status_code=500, detail=f"Error in part matching: {str(e)}")


@app.get("/api/matcher/status")
async def matcher_status_endpoint():
    """Get the current status of available data for matching."""
    try:
        buylist_df = get_buylist_dataframe()
        selllist_df = get_selllist_dataframe()
        
        buylist_ready = buylist_df is not None and len(buylist_df) > 0
        selllist_ready = selllist_df is not None and len(selllist_df) > 0
        
        return {
            "status": "success",
            "data": {
                "buylist_loaded": buylist_ready,
                "selllist_loaded": selllist_ready,
                "buylist_count": len(buylist_df) if buylist_df is not None else 0,
                "selllist_count": len(selllist_df) if selllist_df is not None else 0,
                "ready_for_matching": buylist_ready and selllist_ready,
                "estimated_processing_time": "< 2 minutes" if buylist_ready and selllist_ready else "N/A"
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting matcher status: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting matcher status: {str(e)}")


@app.post("/api/matcher/preview")
async def matcher_preview_endpoint(sample_size: int = 10):
    """
    Get a preview of how the composite matching fields will look.
    
    Args:
        sample_size: Number of sample records to return from each dataset
    """
    try:
        # Get current DataFrames
        buylist_df = get_buylist_dataframe()
        selllist_df = get_selllist_dataframe()
        
        if buylist_df is None or selllist_df is None:
            raise HTTPException(
                status_code=400,
                detail="Both BuyList and SellList data must be loaded for preview"
            )
        
        # Import preprocessing functions
        from matcher.preprocess import preprocess_dataframe
        
        # Process small samples
        buylist_sample = buylist_df.head(sample_size)
        selllist_sample = selllist_df.head(sample_size)
        
        buylist_processed = preprocess_dataframe(buylist_sample, 'buylist')
        selllist_processed = preprocess_dataframe(selllist_sample, 'selllist')
        
        # Prepare preview data
        buylist_preview = []
        for idx, row in buylist_processed.iterrows():
            buylist_preview.append({
                "original_name": row.get('BuyCardName', ''),
                "original_edition": row.get('BuyEdition', ''),
                "original_rarity": row.get('BuyRarity', ''),
                "original_foil": row.get('BuyFoil', ''),
                "composite_match_text": row.get('composite_match_text', '')
            })
        
        selllist_preview = []
        for idx, row in selllist_processed.iterrows():
            selllist_preview.append({
                "original_name": row.get('SellProductName', ''),
                "original_set": row.get('SellSetName', ''),
                "original_rarity": row.get('SellRarity', ''),
                "composite_match_text": row.get('composite_match_text', '')
            })
        
        return {
            "status": "success",
            "data": {
                "buylist_preview": buylist_preview,
                "selllist_preview": selllist_preview,
                "sample_size": sample_size
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating matcher preview: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating matcher preview: {str(e)}")


# ================================
# MATCH DECISION ENDPOINTS
# ================================

class MatchDecisionRequest(BaseModel):
    sell_index: int
    buy_index: int
    decision: str  # 'accept' or 'reject'
    user_notes: str = ""

@app.post("/api/matcher/decide")
async def make_match_decision(request: MatchDecisionRequest):
    """
    Make a decision on a specific match (accept or reject) with conflict detection.
    
    Args:
        sell_index: SellList item index
        buy_index: BuyList item index  
        decision: 'accept' or 'reject'
        user_notes: Optional user notes
    """
    try:
        if not DATABASE_AVAILABLE or match_db is None:
            raise HTTPException(
                status_code=503,
                detail="Match database is not available"
            )
        
        if request.decision not in ['accept', 'reject']:
            raise HTTPException(
                status_code=400,
                detail="Decision must be 'accept' or 'reject'"
            )
        
        # Get current dataframes to build match data
        buylist_df = get_buylist_dataframe()
        selllist_df = get_selllist_dataframe()
        
        if buylist_df is None or selllist_df is None:
            raise HTTPException(
                status_code=400,
                detail="BuyList and SellList data must be loaded"
            )
        
        # Build match data dictionary
        sell_record = selllist_df.iloc[request.sell_index]
        buy_record = buylist_df.iloc[request.buy_index]
        
        match_data = {
            'sell_tcgplayer_id': str(sell_record.get('TCGplayerId', '')),
            'sell_product_name': str(sell_record.get('SellProductName', '')),
            'sell_set_name': str(sell_record.get('SellSetName', '')),
            'buy_product_id': str(buy_record.get('BuyProductId', '')),
            'buy_card_name': str(buy_record.get('BuyCardName', '')),
            'buy_edition': str(buy_record.get('BuyEdition', '')),
            'similarity_score': 0.0  # Will be updated with actual score if available
        }
        
        decision_status = 'accepted' if request.decision == 'accept' else 'rejected'
        
        # Save decision to database with conflict detection
        try:
            decision_id = match_db.save_match_decision(
                match_data=match_data,
                decision_status=decision_status,
                user_notes=request.user_notes
            )
            logger.info(f"✅ Successfully saved match decision: {match_data['sell_tcgplayer_id']} ↔ {match_data['buy_product_id']}, decision={decision_status}")
            
            return {
                "status": "success",
                "message": f"Match {request.decision}ed successfully",
                "data": {
                    "decision_id": decision_id,
                    "sell_index": request.sell_index,
                    "buy_index": request.buy_index,
                    "sell_tcgplayer_id": match_data['sell_tcgplayer_id'],
                    "buy_product_id": match_data['buy_product_id'],
                    "decision_status": decision_status
                }
            }
            
        except ValueError as conflict_error:
            # Handle 1:1 relationship conflicts
            logger.warning(f"🚨 Match conflict detected: {conflict_error}")
            raise HTTPException(
                status_code=409,
                detail={
                    "error_type": "match_conflict",
                    "message": str(conflict_error),
                    "sell_tcgplayer_id": match_data['sell_tcgplayer_id'],
                    "buy_product_id": match_data['buy_product_id'],
                    "suggested_action": "Review existing matches or resolve conflicts in the Matching Errors section"
                }
            )
        except Exception as db_error:
            logger.error(f"❌ Database error saving match decision: {db_error}")
            logger.error(f"Match data: {match_data}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save match decision: {str(db_error)}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error making match decision: {e}")
        raise HTTPException(status_code=500, detail=f"Error making match decision: {str(e)}")


@app.post("/api/matcher/auto_accept")
async def auto_accept_matches(
    threshold: float,
    selllist_indices: Optional[List[int]] = None
):
    """
    Auto-accept matches based on similarity threshold.
    
    Args:
        threshold: Similarity threshold (0.0-1.0) for auto-acceptance
        selllist_indices: Optional list of selllist indices to process (default: all)
    """
    try:
        if not DATABASE_AVAILABLE or match_db is None:
            raise HTTPException(
                status_code=503,
                detail="Match database is not available"
            )
        
        if not 0.0 <= threshold <= 1.0:
            raise HTTPException(
                status_code=400,
                detail="Threshold must be between 0.0 and 1.0"
            )
        
        # Get current match results - would need to be stored somewhere
        # For now, return success but note that this needs the current match results
        
        return {
            "status": "success", 
            "message": f"Auto-accept threshold set to {threshold:.1%}",
            "data": {
                "threshold": threshold,
                "processed_items": 0  # Will be updated when match results are available
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in auto-accept: {e}")
        raise HTTPException(status_code=500, detail=f"Error in auto-accept: {str(e)}")


@app.get("/api/matcher/decisions")
async def get_match_decisions():
    """Get existing match decisions and statistics."""
    try:
        if not DATABASE_AVAILABLE or match_db is None:
            raise HTTPException(
                status_code=503,
                detail="Match database is not available"
            )
        
        # Get existing decisions
        decisions = match_db.get_existing_decisions()
        accepted_sells = match_db.get_accepted_sell_ids()
        stats = match_db.get_match_statistics()
        
        return {
            "status": "success",
            "data": {
                "existing_decisions": len(decisions),
                "accepted_sell_items": len(accepted_sells),
                "statistics": stats,
                "decisions_lookup": {f"{k[0]}_{k[1]}": v for k, v in decisions.items()}
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting match decisions: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting match decisions: {str(e)}")


@app.delete("/api/matcher/decisions/pending")
async def clear_pending_decisions():
    """Clear all pending match decisions."""
    try:
        if not DATABASE_AVAILABLE or match_db is None:
            raise HTTPException(
                status_code=503,
                detail="Match database is not available"
            )
        
        deleted_count = match_db.clear_pending_decisions()
        
        return {
            "status": "success",
            "message": f"Cleared {deleted_count} pending decisions",
            "data": {"deleted_count": deleted_count}
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing pending decisions: {e}")
        raise HTTPException(status_code=500, detail=f"Error clearing pending decisions: {str(e)}")


@app.get("/api/matcher/export/current-run/excel")
async def export_current_run_to_excel():
    """Export ONLY current run match results to Excel file (not accumulated database records)."""
    global _current_match_results
    
    try:
        if _current_match_results.empty:
            raise HTTPException(
                status_code=404,
                detail="No current run results to export. Please run part matching first."
            )
        
        import io
        from fastapi.responses import StreamingResponse
        from datetime import datetime
        
        df = _current_match_results.copy()
        
        # Format data for export
        if not df.empty:
            # Format product IDs to remove decimal places
            if 'sell_tcgplayer_id' in df.columns:
                df['sell_tcgplayer_id'] = df['sell_tcgplayer_id'].astype(str).str.replace('.0', '', regex=False)
            
            if 'buy_product_id' in df.columns:
                df['buy_product_id'] = df['buy_product_id'].astype(str).str.replace('.0', '', regex=False)
        
        # Create Excel file in memory
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Write current run results
            df.to_excel(writer, sheet_name='Current_Run_Matches', index=False)
            
            # Create summary sheet
            if len(df) > 0:
                status_counts = df['decision_status'].value_counts().to_dict()
                summary_data = {
                    'Metric': [
                        'Current Run Total Matches',
                        'Auto Accepted',
                        'Auto Rejected', 
                        'Pending',
                        'Average Similarity Score',
                        'Export Date'
                    ],
                    'Value': [
                        len(df),
                        status_counts.get('auto_accepted', 0),
                        status_counts.get('auto_rejected', 0),
                        status_counts.get('pending', 0),
                        round(df['similarity_score'].mean(), 3) if 'similarity_score' in df.columns else 'N/A',
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    ]
                }
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        output.seek(0)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"current_run_matches_{timestamp}.xlsx"
        
        return StreamingResponse(
            io.BytesIO(output.read()),
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Error exporting current run results: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating current run export: {str(e)}"
        )

@app.get("/api/matcher/export/excel")
async def export_matches_to_excel():
    """Export all accumulated match decisions from database to Excel file."""
    try:
        if not DATABASE_AVAILABLE or match_db is None:
            raise HTTPException(
                status_code=503,
                detail="Match database is not available"
            )
        
        import pandas as pd
        import io
        from fastapi.responses import StreamingResponse
        from datetime import datetime
        
        # Get all match data from database
        match_data = match_db.get_all_match_data()
        
        if not match_data:
            raise HTTPException(
                status_code=404,
                detail="No match data found to export"
            )
        
        # Convert to DataFrame
        df = pd.DataFrame(match_data)
        
        # Fix data formatting issues
        if not df.empty:
            # Remove unnecessary buy fields per user request
            columns_to_remove = ['buy_card_name', 'buy_edition']
            df = df.drop(columns=[col for col in columns_to_remove if col in df.columns])
            
            # Format product IDs to remove decimal places
            if 'sell_tcgplayer_id' in df.columns:
                df['sell_tcgplayer_id'] = df['sell_tcgplayer_id'].astype(str).str.replace('.0', '', regex=False)
            
            if 'buy_product_id' in df.columns:
                df['buy_product_id'] = df['buy_product_id'].astype(str).str.replace('.0', '', regex=False)
        
        # Create Excel file in memory
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Write main data to 'Matches' sheet
            df.to_excel(writer, sheet_name='Matches', index=False)
            
            # Create summary sheet with statistics
            if len(df) > 0:
                summary_data = {
                    'Metric': [
                        'Total Matches',
                        'Auto Accepted',
                        'Auto Rejected', 
                        'Manually Accepted',
                        'Manually Rejected',
                        'Pending',
                        'Average Similarity Score',
                        'Export Date'
                    ],
                    'Value': [
                        len(df),
                        len(df[df['decision_status'] == 'auto_accepted']),
                        len(df[df['decision_status'] == 'auto_rejected']),
                        len(df[df['decision_status'] == 'accepted']),
                        len(df[df['decision_status'] == 'rejected']),
                        len(df[df['decision_status'] == 'pending']),
                        f"{df['similarity_score'].mean():.3f}" if 'similarity_score' in df.columns else 'N/A',
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    ]
                }
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        output.seek(0)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"card_matching_results_{timestamp}.xlsx"
        
        return StreamingResponse(
            io.BytesIO(output.read()),
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting matches to Excel: {e}")
        raise HTTPException(status_code=500, detail=f"Error exporting matches: {str(e)}")


@app.get("/api/matcher/export/matching-errors/excel")
async def export_matching_errors_to_excel():
    """Export all matching errors to Excel file."""
    try:
        if not DATABASE_AVAILABLE or match_db is None:
            raise HTTPException(
                status_code=503,
                detail="Match database is not available"
            )
        
        import pandas as pd
        import io
        from fastapi.responses import StreamingResponse
        from datetime import datetime
        
        # Get all matching errors from database
        errors = match_db.get_matching_errors()
        
        if not errors:
            raise HTTPException(
                status_code=404,
                detail="No matching errors found to export"
            )
        
        # Convert to DataFrame
        df = pd.DataFrame(errors)
        
        # Create Excel file in memory
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Matching_Errors', index=False)
        
        output.seek(0)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"matching_errors_{timestamp}.xlsx"
        
        return StreamingResponse(
            io.BytesIO(output.read()),
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting matching errors to Excel: {e}")
        raise HTTPException(status_code=500, detail=f"Error exporting matching errors: {str(e)}")


@app.get("/api/matcher/export/non-matches/excel")
async def export_non_matches_to_excel():
    """Export all non-matches to Excel file."""
    try:
        if not DATABASE_AVAILABLE or match_db is None:
            raise HTTPException(
                status_code=503,
                detail="Match database is not available"
            )
        
        import pandas as pd
        import io
        from fastapi.responses import StreamingResponse
        from datetime import datetime
        
        # Get all non-matches from database
        with match_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, sell_tcgplayer_id, buy_product_id, sell_product_name, 
                       sell_set_name, buy_card_name, buy_edition, rejection_reason,
                       similarity_score_when_rejected, rejected_by, rejection_date,
                       permanent_exclusion, notes
                FROM non_matches 
                ORDER BY rejection_date DESC
            """)
            
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
            
            non_matches = []
            for row in rows:
                non_matches.append(dict(zip(columns, row)))
        
        if not non_matches:
            raise HTTPException(
                status_code=404,
                detail="No non-matches found to export"
            )
        
        # Convert to DataFrame
        df = pd.DataFrame(non_matches)
        
        # Format product IDs to remove decimal places
        if 'sell_tcgplayer_id' in df.columns:
            df['sell_tcgplayer_id'] = df['sell_tcgplayer_id'].astype(str).str.replace('.0', '', regex=False)
        if 'buy_product_id' in df.columns:
            df['buy_product_id'] = df['buy_product_id'].astype(str).str.replace('.0', '', regex=False)
        
        # Create Excel file in memory
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Non_Matches', index=False)
        
        output.seek(0)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"non_matches_{timestamp}.xlsx"
        
        return StreamingResponse(
            io.BytesIO(output.read()),
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting non-matches to Excel: {e}")
        raise HTTPException(status_code=500, detail=f"Error exporting non-matches: {str(e)}")


@app.get("/api/matcher/export/match-sessions/excel")
async def export_match_sessions_to_excel():
    """Export all match sessions to Excel file."""
    try:
        if not DATABASE_AVAILABLE or match_db is None:
            raise HTTPException(
                status_code=503,
                detail="Match database is not available"
            )
        
        import pandas as pd
        import io
        from fastapi.responses import StreamingResponse
        from datetime import datetime
        
        # Get all match sessions from database
        with match_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, session_timestamp, total_selllist_items, total_buylist_items,
                       total_matches_found, similarity_threshold, max_matches_per_item,
                       auto_accept_threshold, processing_time_seconds, match_config,
                       errors_encountered, conflicts_resolved
                FROM match_sessions 
                ORDER BY session_timestamp DESC
            """)
            
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
            
            sessions = []
            for row in rows:
                sessions.append(dict(zip(columns, row)))
        
        if not sessions:
            raise HTTPException(
                status_code=404,
                detail="No match sessions found to export"
            )
        
        # Convert to DataFrame
        df = pd.DataFrame(sessions)
        
        # Create Excel file in memory
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Match_Sessions', index=False)
        
        output.seek(0)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"match_sessions_{timestamp}.xlsx"
        
        return StreamingResponse(
            io.BytesIO(output.read()),
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting match sessions to Excel: {e}")
        raise HTTPException(status_code=500, detail=f"Error exporting match sessions: {str(e)}")


# === CONFLICT MANAGEMENT ENDPOINTS ===

@app.get("/api/matcher/conflicts")
async def get_matching_conflicts():
    """Get all matching conflicts for review and resolution."""
    try:
        if not DATABASE_AVAILABLE or match_db is None:
            raise HTTPException(status_code=503, detail="Match database is not available")
        
        conflicts = match_db.get_matching_errors('unresolved')
        summary = match_db.get_conflict_summary()
        
        return {
            "status": "success",
            "data": {
                "unresolved_conflicts": conflicts,
                "summary": summary
            }
        }
        
    except Exception as e:
        logger.error(f"Error retrieving conflicts: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving conflicts: {str(e)}")


@app.post("/api/matcher/conflicts/{conflict_id}/resolve")
async def resolve_conflict(conflict_id: int, resolution_action: str, replace_existing: bool = False):
    """
    Resolve a matching conflict.
    
    Args:
        conflict_id: ID of the conflict to resolve
        resolution_action: Description of the resolution action
        replace_existing: Whether to replace the existing match
    """
    try:
        if not DATABASE_AVAILABLE or match_db is None:
            raise HTTPException(status_code=503, detail="Match database is not available")
        
        result = match_db.resolve_matching_error(conflict_id, resolution_action, replace_existing)
        
        return {
            "status": "success",
            "message": "Conflict resolved successfully",
            "data": result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error resolving conflict: {e}")
        raise HTTPException(status_code=500, detail=f"Error resolving conflict: {str(e)}")


@app.get("/api/matcher/non-matches")
async def get_non_matches():
    """Get all non-matches (user-rejected pairs)."""
    try:
        if not DATABASE_AVAILABLE or match_db is None:
            raise HTTPException(status_code=503, detail="Match database is not available")
        
        non_matches = match_db.get_non_matches()
        
        return {
            "status": "success",
            "data": {
                "non_matches": [
                    {
                        "sell_tcgplayer_id": key[0],
                        "buy_product_id": key[1],
                        **value
                    }
                    for key, value in non_matches.items()
                ],
                "total_count": len(non_matches)
            }
        }
        
    except Exception as e:
        logger.error(f"Error retrieving non-matches: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving non-matches: {str(e)}")


class NonMatchRequest(BaseModel):
    sell_tcgplayer_id: str
    buy_product_id: str
    rejection_reason: str
    permanent_exclusion: bool = True


@app.post("/api/matcher/non-matches")
async def add_non_match(request: NonMatchRequest):
    """Manually add a non-match to prevent future matching."""
    try:
        if not DATABASE_AVAILABLE or match_db is None:
            raise HTTPException(status_code=503, detail="Match database is not available")
        
        # Create minimal match_data for the non-match entry
        match_data = {
            'sell_product_name': '',
            'sell_set_name': '',
            'buy_card_name': '',
            'buy_edition': ''
        }
        
        non_match_id = match_db.add_non_match(
            sell_tcgplayer_id=request.sell_tcgplayer_id,
            buy_product_id=request.buy_product_id,
            match_data=match_data,
            rejection_reason=request.rejection_reason,
            similarity_score=0.0,
            rejected_by='manual'
        )
        
        return {
            "status": "success",
            "message": "Non-match added successfully",
            "data": {
                "non_match_id": non_match_id,
                "sell_tcgplayer_id": request.sell_tcgplayer_id,
                "buy_product_id": request.buy_product_id
            }
        }
        
    except Exception as e:
        logger.error(f"Error adding non-match: {e}")
        raise HTTPException(status_code=500, detail=f"Error adding non-match: {str(e)}")


@app.delete("/api/matcher/non-matches/{sell_id}/{buy_id}")
async def remove_non_match(sell_id: str, buy_id: str):
    """Remove a non-match to allow future matching."""
    try:
        if not DATABASE_AVAILABLE or match_db is None:
            raise HTTPException(status_code=503, detail="Match database is not available")
        
        with match_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM non_matches 
                WHERE sell_tcgplayer_id = ? AND buy_product_id = ?
            """, (sell_id, buy_id))
            
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Non-match not found")
            
            conn.commit()
        
        return {
            "status": "success",
            "message": "Non-match removed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing non-match: {e}")
        raise HTTPException(status_code=500, detail=f"Error removing non-match: {str(e)}")


@app.delete("/api/matcher/clear-all")
async def clear_all_matching_data():
    """Clear all matching data from all tables for a fresh start."""
    try:
        if not DATABASE_AVAILABLE or match_db is None:
            raise HTTPException(status_code=503, detail="Match database is not available")
        
        with match_db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Count records before deletion for reporting
            cursor.execute("SELECT COUNT(*) as count FROM match_decisions")
            match_decisions_count = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM matching_errors")
            matching_errors_count = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM non_matches")
            non_matches_count = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM match_sessions")
            match_sessions_count = cursor.fetchone()['count']
            
            # Clear all tables
            cursor.execute("DELETE FROM match_decisions")
            cursor.execute("DELETE FROM matching_errors")
            cursor.execute("DELETE FROM non_matches")
            cursor.execute("DELETE FROM match_sessions")
            
            # Reset auto-increment counters
            cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('match_decisions', 'matching_errors', 'non_matches', 'match_sessions')")
            
            conn.commit()
            
            total_cleared = match_decisions_count + matching_errors_count + non_matches_count + match_sessions_count
            
            logger.info(f"🗑️ Cleared all matching data: {match_decisions_count} decisions, {matching_errors_count} errors, {non_matches_count} non-matches, {match_sessions_count} sessions")
        
        return {
            "status": "success",
            "message": "All matching data cleared successfully",
            "data": {
                "match_decisions_cleared": match_decisions_count,
                "matching_errors_cleared": matching_errors_count,
                "non_matches_cleared": non_matches_count,
                "match_sessions_cleared": match_sessions_count,
                "total_records_cleared": total_cleared
            }
        }
        
    except Exception as e:
        logger.error(f"Error clearing matching data: {e}")
        raise HTTPException(status_code=500, detail=f"Error clearing matching data: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    # Increase timeout for large data processing
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8002, 
        log_level="info",
        timeout_keep_alive=120  # Keep connection alive for long requests
    )