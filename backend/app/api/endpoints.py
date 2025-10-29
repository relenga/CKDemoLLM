from fastapi import APIRouter, HTTPException
from app.models.schemas import (
    GraphProcessRequest, 
    GraphProcessResponse, 
    StatusResponse,
    GraphInfoResponse
)
from app.services.graph_service import graph_service
import logging

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