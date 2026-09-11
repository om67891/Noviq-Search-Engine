from fastapi import APIRouter, Query, HTTPException
from typing import Optional, Dict, Any
from app.retrieval.hybrid_search import HybridSearchEngine
from enum import Enum

router = APIRouter()
search_engine = HybridSearchEngine()

class SearchMode(str, Enum):
    keyword = "keyword"
    semantic = "semantic"
    hybrid = "hybrid"

@router.get("/")
async def search(
    q: str = Query(..., description="Search query"),
    mode: SearchMode = Query(SearchMode.hybrid, description="Retrieval mode"),
    limit: int = Query(10, ge=1, le=50, description="Number of results to return"),
    page: int = Query(1, ge=1, description="Page number")
) -> Dict[str, Any]:
    """
    Search endpoint supporting BM25 lexical search, semantic vector search, and hybrid retrieval.
    """
    if not q or not q.strip():
        return {"query": q, "mode": mode, "page": page, "page_size": limit, "total": 0, "results": []}
        
    offset = (page - 1) * limit
    
    try:
        if mode == SearchMode.keyword:
            results = search_engine.search_keyword(query=q, limit=limit, offset=offset)
        elif mode == SearchMode.semantic:
            # Note: Offset isn't directly used in simple semantic search implementation for simplicity
            # Usually vector DBs support limit/offset or scroll.
            results = search_engine.search_semantic(query=q, limit=limit) 
        else: # hybrid
            results = search_engine.search_hybrid(query=q, limit=limit, offset=offset)
            
        return {
            "query": q,
            "mode": mode,
            "page": page,
            "page_size": limit,
            "total": results["total"],
            "results": results["results"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
