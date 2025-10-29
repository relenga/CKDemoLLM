from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
import time
import logging

logger = logging.getLogger(__name__)

class GraphState:
    def __init__(self):
        self.messages: List[Any] = []
        self.current_step: str = ""
        self.metadata: Dict[str, Any] = {}

class LangGraphProcessor:
    def __init__(self, openai_api_key: str = None):
        self.openai_api_key = openai_api_key
        self.llm = ChatOpenAI(
            api_key=openai_api_key,
            temperature=0.7,
            model="gpt-3.5-turbo"
        ) if openai_api_key else None
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        
        def input_processor(state: Dict[str, Any]) -> Dict[str, Any]:
            """Process the initial input"""
            logger.info(f"Processing input: {state.get('input', '')}")
            state["current_step"] = "input_processing"
            state["metadata"]["nodes_processed"] = state["metadata"].get("nodes_processed", 0) + 1
            return state
        
        def ai_processor(state: Dict[str, Any]) -> Dict[str, Any]:
            """Process with AI if available"""
            if self.llm:
                try:
                    response = self.llm.invoke([HumanMessage(content=state["input"])])
                    state["ai_response"] = response.content
                    state["current_step"] = "ai_processing"
                except Exception as e:
                    logger.error(f"AI processing error: {e}")
                    state["ai_response"] = f"AI processing unavailable: {str(e)}"
            else:
                state["ai_response"] = "AI processing unavailable: No API key provided"
            
            state["metadata"]["nodes_processed"] = state["metadata"].get("nodes_processed", 0) + 1
            return state
        
        def output_formatter(state: Dict[str, Any]) -> Dict[str, Any]:
            """Format the final output"""
            ai_response = state.get("ai_response", "No AI response")
            user_input = state.get("input", "No input")
            
            formatted_output = f"""
Input: {user_input}

AI Response: {ai_response}

Processing completed successfully.
Nodes processed: {state['metadata'].get('nodes_processed', 0)}
"""
            
            state["result"] = formatted_output.strip()
            state["current_step"] = "output_formatting"
            state["metadata"]["nodes_processed"] = state["metadata"].get("nodes_processed", 0) + 1
            return state
        
        # Build the graph
        workflow = StateGraph(dict)
        
        # Add nodes
        workflow.add_node("input_processor", input_processor)
        workflow.add_node("ai_processor", ai_processor)
        workflow.add_node("output_formatter", output_formatter)
        
        # Add edges
        workflow.set_entry_point("input_processor")
        workflow.add_edge("input_processor", "ai_processor")
        workflow.add_edge("ai_processor", "output_formatter")
        workflow.add_edge("output_formatter", END)
        
        return workflow.compile()
    
    async def process(self, input_text: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process input through the LangGraph workflow"""
        start_time = time.time()
        
        try:
            initial_state = {
                "input": input_text,
                "metadata": {"nodes_processed": 0, "edges_traversed": 0},
                "options": options or {}
            }
            
            # Run the graph
            result = self.graph.invoke(initial_state)
            
            processing_time = time.time() - start_time
            
            return {
                "result": result.get("result", "No result generated"),
                "status": "success",
                "processing_time": processing_time,
                "metadata": result.get("metadata", {})
            }
            
        except Exception as e:
            logger.error(f"Graph processing error: {e}")
            processing_time = time.time() - start_time
            
            return {
                "result": f"Error processing input: {str(e)}",
                "status": "error",
                "processing_time": processing_time,
                "metadata": {"error": str(e)}
            }
    
    def get_graph_info(self) -> Dict[str, Any]:
        """Get information about the graph structure"""
        return {
            "nodes": 3,
            "edges": 3,
            "graph_type": "Sequential Processing",
            "description": "A simple LangGraph workflow that processes input through AI and formats output"
        }