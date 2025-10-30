from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Create the app
app = FastAPI(
    title="CK LangGraph Backend API",
    version="1.0.0",
    description="CK LangGraph Backend API"
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

@app.post("/api/buylist/upload")
async def upload_buylist():
    """Upload and process Card Kingdom buylist data"""
    import time
    import aiohttp
    import json
    import re
    
    start_time = time.time()
    
    try:
        # Card Kingdom buylist URL
        url = "https://www.cardkingdom.com/json/buylist.jsonp"
        
        # Column mapping
        column_mapping = {
            "i": "BuyProductId",
            "n": "BuyCardName", 
            "e": "BuyEdition",
            "r": "BuyRarity",
            "f": "BuyFoil",
            "p": "BuyPrice",
            "q": "BuyQty",
            "u": "BuyImage"
        }
        
        # Fetch data with proper headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        timeout = aiohttp.ClientTimeout(total=120)
        async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}: {response.reason}")
                
                raw_data = await response.text()
                print(f"Raw data length: {len(raw_data)}")
                print(f"Raw data preview: {raw_data[:500] if raw_data else 'EMPTY'}")
                
                if not raw_data or not raw_data.strip():
                    raise Exception("Empty response received from Card Kingdom API")
                
                # Clean JSONP wrapper - specifically for ckCardList([...])
                stripped_data = raw_data.strip()
                print(f"Checking for JSONP wrapper...")
                print(f"Starts with 'ckCardList('? {stripped_data.startswith('ckCardList(')}")
                print(f"Ends with ');'? {stripped_data.endswith(');')}")
                print(f"First 50 chars: {stripped_data[:50]}")
                print(f"Last 50 chars: {stripped_data[-50:]}")
                
                if stripped_data.startswith('ckCardList(') and stripped_data.endswith(');'):
                    # Remove ckCardList( from start and ); from end
                    json_data = stripped_data[11:-2]  # Remove "ckCardList(" and ");"
                    print(f"✅ JSONP wrapper 'ckCardList();' detected and cleaned")
                elif stripped_data.startswith('(') and stripped_data.endswith(')'):
                    # Generic JSONP wrapper
                    json_data = stripped_data[1:-1]
                    print(f"✅ Generic JSONP wrapper detected and cleaned")
                else:
                    json_data = stripped_data
                    print(f"❌ No JSONP wrapper found, using raw data")
                
                print(f"Cleaned JSON length: {len(json_data)}")
                print(f"Cleaned JSON preview: {json_data[:200] if json_data else 'EMPTY'}")
                
                # Parse JSON
                data = json.loads(json_data)
                print(f"Successfully parsed JSON with {len(data)} records")
                
                # Transform first 5 records as sample
                sample_data = []
                for i, record in enumerate(data[:5] if len(data) > 5 else data):
                    transformed_record = {}
                    for old_key, new_key in column_mapping.items():
                        if old_key in record:
                            transformed_record[new_key] = record[old_key]
                    sample_data.append(transformed_record)
                
                processing_time = time.time() - start_time
                
                return {
                    "status": "success",
                    "message": f"Successfully processed {len(data)} records from Card Kingdom buylist",
                    "total_records": len(data),
                    "processing_time": round(processing_time, 2),
                    "sample_records": sample_data,
                    "columns": list(column_mapping.values())
                }
                
    except Exception as e:
        processing_time = time.time() - start_time
        return {
            "status": "error",
            "message": f"Error processing buylist: {str(e)}",
            "total_records": 0,
            "processing_time": round(processing_time, 2)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="info")