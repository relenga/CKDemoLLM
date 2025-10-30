"""
WORKING FastAPI Server - Clean Version
Based on our proven working core functions.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import aiohttp
import time
import logging

# Import our WORKING core functions
from buylist_core import process_buylist_data, get_buylist_stats, get_buylist_sample

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create app
app = FastAPI(title="CK Buylist Server - Clean Version")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "CK Buylist Server - Working Version", "status": "ready"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/api/buylist/stats")
async def get_stats():
    """Get dataframe statistics."""
    return get_buylist_stats()

@app.get("/api/buylist/sample")
async def get_sample(records: int = 5):
    """Get sample data."""
    if records < 1 or records > 50:
        records = 5
    return get_buylist_sample(records)

@app.post("/api/buylist/upload")
async def upload_buylist():
    """Upload CK buylist - WORKING VERSION"""
    start_time = time.time()
    
    try:
        logger.info("Starting buylist upload...")
        
        # Use the EXACT same logic that works in our tests
        url = "https://www.cardkingdom.com/json/buylist.jsonp"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Fetch data (this works from our tests)
        fetch_start = time.time()
        timeout = aiohttp.ClientTimeout(total=120)
        async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise HTTPException(status_code=response.status, detail="Failed to fetch from Card Kingdom")
                raw_data = await response.text()
        
        fetch_time = time.time() - fetch_start
        logger.info(f"Data fetched in {fetch_time:.2f}s")
        
        # Process data (this works from our tests)
        process_start = time.time()
        transformed_records, total_count = process_buylist_data(raw_data, save_to_dataframe=True)
        process_time = time.time() - process_start
        
        # Get updated stats
        stats = get_buylist_stats()
        
        total_time = time.time() - start_time
        
        logger.info(f"Upload complete: {total_count} records in {total_time:.2f}s")
        
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
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting CLEAN CK Buylist Server...")
    print("✅ Using proven working core functions")
    print("🌐 Server will be available at: http://localhost:8002")
    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="info")