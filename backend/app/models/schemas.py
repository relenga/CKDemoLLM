from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class GraphProcessRequest(BaseModel):
    input: str
    options: Optional[Dict[str, Any]] = None

class GraphProcessResponse(BaseModel):
    result: str
    status: str
    processing_time: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime = datetime.now()

class StatusResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime = datetime.now()

class GraphInfoResponse(BaseModel):
    nodes: int
    edges: int
    graph_type: str
    description: str