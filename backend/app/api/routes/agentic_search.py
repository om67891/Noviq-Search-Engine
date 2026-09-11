from fastapi import APIRouter, Query, HTTPException
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from app.graph.workflow import AgenticSearchWorkflow
import time
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
workflow = AgenticSearchWorkflow()

class AgenticSearchRequest(BaseModel):
    query: str
    mode: str = "agentic"

class AgenticSearchResponse(BaseModel):
    query: str
    answer: str
    citations: List[Dict[str, Any]]
    confidence_score: int
    trust_summary: Dict[str, Any]
    warnings: List[str]
    conflicts: List[Dict[str, Any]]
    sources: List[Dict[str, Any]]
    insufficient_evidence: bool
    execution_trace: List[str]
    latency: float

@router.post("/", response_model=AgenticSearchResponse)
async def search_agentic(request: AgenticSearchRequest) -> Any:
    """
    Executes a Multi-Agent Trust-Aware Search.
    """
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
        
    start_time = time.time()
    logger.info(f"Starting Agentic Search for query: '{request.query}'")
    
    try:
        final_state = workflow.run(request.query)
        
        latency = round(time.time() - start_time, 2)
        
        # Format sources from selected_sources
        formatted_sources = []
        for s in final_state.get("selected_sources", []):
            formatted_sources.append({
                "id": str(s.get("id") or s.get("url")),
                "url": s.get("url"),
                "domain": s.get("domain"),
                "title": s.get("title"),
                "trust_score": s.get("trust_score"),
                "trust_level": s.get("trust_level"),
                "security_status": s.get("security_status")
            })
            
        return AgenticSearchResponse(
            query=final_state.get("original_query", ""),
            answer=final_state.get("answer", ""),
            citations=final_state.get("citations", []),
            confidence_score=final_state.get("confidence", 0),
            trust_summary=final_state.get("trust_summary", {}),
            warnings=final_state.get("warnings", []),
            conflicts=final_state.get("conflicts", []),
            sources=formatted_sources,
            insufficient_evidence=final_state.get("insufficient_evidence", False),
            execution_trace=final_state.get("execution_trace", []),
            latency=latency
        )
    except Exception as e:
        logger.error(f"Agentic search API failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
