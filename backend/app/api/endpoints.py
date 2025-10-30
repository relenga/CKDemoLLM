from fastapi import APIRouter, HTTPException
from app.models.schemas import (
    GraphProcessRequest, 
    GraphProcessResponse, 
    StatusResponse,
    GraphInfoResponse,
    BuylistUploadRequest,
    BuylistUploadResponse
)
from app.services.graph_service import graph_service
from app.services.ck_buylist_service_simple import ck_buylist_service
import logging
import time

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/graph/process", response_model=GraphProcessResponse)
async def process_graph_input(request: GraphProcessRequest):
    """Process input through LangGraph workflow"""
    try:
        result = await graph_service.process_input(
            input_text=request.input,
            options=request.options
        )
        return GraphProcessResponse(**result)
    except Exception as e:
        logger.error(f"Error processing graph input: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/graph/info", response_model=GraphInfoResponse)
async def get_graph_info():
    """Get information about the graph structure"""
    try:
        info = graph_service.get_graph_info()
        return GraphInfoResponse(**info)
    except Exception as e:
        logger.error(f"Error getting graph info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status", response_model=StatusResponse)
async def get_status():
    """Get API status"""
    try:
        status = graph_service.get_status()
        return StatusResponse(
            status=status["status"],
            version=status["version"]
        )
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test")
async def test_endpoint():
    """Simple test endpoint to verify routing works"""
    return {"message": "Test endpoint is working!", "status": "ok", "timestamp": "2025-10-29", "updated": True, "reload_test": "v2"}

@router.get("/debug/routes")
async def debug_routes():
    """Debug endpoint to show all registered routes"""
    from fastapi import Request
    from main import app
    routes_info = []
    for route in app.routes:
        if hasattr(route, 'path'):
            routes_info.append({
                "path": route.path,
                "methods": getattr(route, 'methods', []),
                "name": getattr(route, 'name', 'unnamed')
            })
    return {"total_routes": len(app.routes), "routes": routes_info}

@router.get("/buylist/test")
async def test_buylist_endpoint():
    """Test if buylist endpoint is working"""
    return {"message": "Buylist endpoint is registered!", "status": "ok"}

@router.post("/buylist/upload", response_model=BuylistUploadResponse)
async def upload_buylist(request: BuylistUploadRequest):
    """Upload and process Card Kingdom buylist data"""
    start_time = time.time()
    
    try:
        logger.info("=== STARTING BUYLIST UPLOAD ===")
        logger.info(f"Request URL: {request.url if hasattr(request, 'url') else 'default'}")
        
        # Fetch and process the buylist data
        processed_data = await ck_buylist_service.fetch_buylist_data()
        
        # Generate summary
        summary = ck_buylist_service.get_data_summary(processed_data)
        
        processing_time = time.time() - start_time
        
        logger.info(f"Buylist processing completed successfully in {processing_time:.2f}s")
        
        return BuylistUploadResponse(
            status="success",
            message=f"Successfully processed {processed_data['total_records']} records from Card Kingdom buylist",
            total_records=processed_data['total_records'],
            processing_time=processing_time,
            summary=summary
        )
        
    except Exception as e:
        processing_time = time.time() - start_time
        error_msg = f"Error processing buylist: {str(e)}"
        logger.error(f"=== BUYLIST ERROR === {error_msg}")
        logger.exception("Full traceback:")
        
        return BuylistUploadResponse(
            status="error",
            message=error_msg,
            total_records=0,
            processing_time=processing_time
        )