from fastapi import APIRouter
from app.api.endpoints import router as graph_router

api_router = APIRouter()
api_router.include_router(graph_router, tags=["graph"])