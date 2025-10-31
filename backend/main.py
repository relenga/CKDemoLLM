"""
CK LangGraph Backend API
A FastAPI backend for processing Card Kingdom buylist data.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import logging
import time
import aiohttp
import json
import asyncio
import psutil
import os
import numpy as np
import pandas as pd
from typing import Dict, List, Any

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
        
        # Get sample records (first 5)
        sample_size = min(5, len(transformed_records))
        sample_data = transformed_records[:sample_size]
        
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