"""
CK LangGraph Backend API
A FastAPI backend for processing Card Kingdom buylist data.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
import time
import aiohttp
import json
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the app
app = FastAPI(
    title="CK LangGraph Backend API",
    version="1.0.0",
    description="A FastAPI backend for processing Card Kingdom buylist data with LangGraph integration."
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# Buylist endpoints (simplified versions)
@app.get("/api/buylist/test")
async def test_buylist_endpoint():
    return {"message": "Buylist endpoint is registered!", "status": "ok"}

# Constants
CARD_KINGDOM_BUYLIST_URL = "https://www.cardkingdom.com/json/buylist.jsonp"
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


def clean_jsonp_wrapper(raw_data: str) -> str:
    """Clean JSONP wrapper from Card Kingdom response."""
    stripped_data = raw_data.strip()
    
    logger.debug(f"Checking for JSONP wrapper in data: {stripped_data[:50]}...{stripped_data[-50:]}")
    
    if stripped_data.startswith('ckCardList(') and stripped_data.endswith(');'):
        # Remove ckCardList( from start and ); from end
        json_data = stripped_data[11:-2]
        logger.info("✅ JSONP wrapper 'ckCardList();' detected and cleaned")
        return json_data
    elif stripped_data.startswith('(') and stripped_data.endswith(')'):
        # Generic JSONP wrapper
        json_data = stripped_data[1:-1]
        logger.info("✅ Generic JSONP wrapper detected and cleaned")
        return json_data
    else:
        logger.warning("❌ No JSONP wrapper found, using raw data")
        return stripped_data


def transform_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """Transform a single record using the column mapping."""
    transformed_record = {}
    for old_key, new_key in COLUMN_MAPPING.items():
        if old_key in record:
            transformed_record[new_key] = record[old_key]
    return transformed_record


@app.post("/api/buylist/upload")
async def upload_buylist():
    """Upload and process Card Kingdom buylist data."""
    start_time = time.time()
    
    try:
        # Fetch raw data
        raw_data = await fetch_card_kingdom_data()
        
        # Clean JSONP wrapper
        json_data = clean_jsonp_wrapper(raw_data)
        
        # Parse JSON
        try:
            data = json.loads(json_data)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to parse JSON data: {str(e)}"
            )
        
        logger.info(f"Successfully parsed JSON with {len(data)} records")
        
        # Transform sample records (first 5)
        sample_size = min(5, len(data))
        sample_data = [transform_record(record) for record in data[:sample_size]]
        
        processing_time = time.time() - start_time
        
        return {
            "status": "success",
            "message": f"Successfully processed {len(data)} records from Card Kingdom buylist",
            "total_records": len(data),
            "processing_time": round(processing_time, 2),
            "sample_records": sample_data,
            "columns": list(COLUMN_MAPPING.values())
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="info")