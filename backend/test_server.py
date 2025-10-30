"""
Simple FastAPI server for testing CK buylist upload.
This is a minimal version to isolate any server issues.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import logging

# Import our working core functions
from buylist_core import process_buylist_data, get_buylist_stats, get_buylist_sample

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the app
app = FastAPI(title="CK Test Server")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/buylist/stats")
async def get_stats():
    """Get dataframe statistics."""
    try:
        stats = get_buylist_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/buylist/sample")
async def get_sample(records: int = 5):
    """Get sample data."""
    try:
        if records < 1 or records > 50:
            records = 5
        sample = get_buylist_sample(records)
        return sample
    except Exception as e:
        logger.error(f"Error getting sample: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/buylist/upload")
async def upload_test():
    """Test upload using our working core functions."""
    try:
        logger.info("Starting upload test...")
        
        # Import the test function that we know works
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tests'))
        
        # Use the working test logic
        import aiohttp
        import time
        
        start_time = time.time()
        
        # Fetch data (this works from our test)
        url = "https://www.cardkingdom.com/json/buylist.jsonp"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                raw_data = await response.text()
        
        fetch_time = time.time() - start_time
        
        # Process data (this works from our test)
        process_start = time.time()
        transformed_records, total_count = process_buylist_data(raw_data, save_to_dataframe=True)
        process_time = time.time() - process_start
        
        # Get stats
        stats = get_buylist_stats()
        
        total_time = time.time() - start_time
        
        return {
            "status": "success",
            "message": f"Successfully processed {total_count} records",
            "total_records": total_count,
            "fetch_time": round(fetch_time, 2),
            "process_time": round(process_time, 2),
            "total_time": round(total_time, 2),
            "dataframe_stats": stats,
            "sample_records": transformed_records[:3] if transformed_records else []
        }
        
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003, log_level="info")