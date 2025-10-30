from fastapi import FastAPI

app = FastAPI(title="CK LangGraph Test API")

@app.get("/")
async def root():
    return {"message": "Simple test server running"}

@app.get("/test")
async def test():
    return {"message": "Simple test endpoint works!"}

@app.get("/api/test") 
async def api_test():
    return {"message": "API test endpoint works!"}

@app.get("/api/buylist/test")
async def simple_buylist_test():
    return {"message": "Simple buylist test works!", "status": "ok"}

@app.post("/api/buylist/upload")
async def simple_buylist_upload():
    return {"message": "Simple buylist upload works!", "status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)