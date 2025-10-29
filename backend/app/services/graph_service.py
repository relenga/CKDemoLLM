from app.graph.processor import LangGraphProcessor
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class GraphService:
    def __init__(self):
        self.processor = LangGraphProcessor(
            openai_api_key=settings.OPENAI_API_KEY if settings.OPENAI_API_KEY else None
        )
    
    async def process_input(self, input_text: str, options: dict = None):
        """Process input through LangGraph"""
        return await self.processor.process(input_text, options)
    
    def get_graph_info(self):
        """Get graph information"""
        return self.processor.get_graph_info()
    
    def get_status(self):
        """Get service status"""
        return {
            "status": "running",
            "version": settings.VERSION,
            "graph_available": True,
            "ai_available": bool(settings.OPENAI_API_KEY)
        }

# Global instance
graph_service = GraphService()