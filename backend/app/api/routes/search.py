"""
Noviq Search API — /api/v1/search/

This endpoint:
  1. Calls LiveSearchPipeline to discover, fetch, and index real web pages
     for the query (Brave API or DDG fallback).
  2. Then runs HybridSearchEngine over the freshly indexed content.
  3. Returns results with retrieval_source metadata so the frontend can
     display LIVE WEB vs CACHED vs LOCAL INDEX labels.

Every arbitrary query (ronaldo, cancer, insects, …) will trigger real
web discovery before retrieval. Results are cached in Redis for 1 hour
to avoid redundant fetching of the same URLs.
"""
import logging
import time
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Query

from app.pipeline.live_search import LiveSearchPipeline
from app.retrieval.hybrid_search import HybridSearchEngine

logger = logging.getLogger(__name__)
router = APIRouter()

# Module-level singletons (initialized once per worker)
_search_engine: HybridSearchEngine | None = None
_live_pipeline: LiveSearchPipeline | None = None


def _get_search_engine() -> HybridSearchEngine:
    global _search_engine
    if _search_engine is None:
        _search_engine = HybridSearchEngine()
    return _search_engine


def _get_live_pipeline() -> LiveSearchPipeline:
    global _live_pipeline
    if _live_pipeline is None:
        _live_pipeline = LiveSearchPipeline()
    return _live_pipeline


class SearchMode(str, Enum):
    keyword = "keyword"
    semantic = "semantic"
    hybrid = "hybrid"


@router.get("/")
async def search(
    q: str = Query(..., description="Search query"),
    mode: SearchMode = Query(SearchMode.hybrid, description="Retrieval mode"),
    limit: int = Query(10, ge=1, le=50, description="Number of results"),
    page: int = Query(1, ge=1, description="Page number"),
) -> Dict[str, Any]:
    """
    Noviq Search: Performs live web discovery then hybrid retrieval.

    For every query, Noviq:
    - Calls a web search provider (Brave/DDG) to discover real URLs
    - Fetches and extracts those pages
    - Scans for prompt injection and scores trust
    - Chunks and embeds content into Qdrant + OpenSearch
    - Then retrieves using BM25, semantic, or hybrid RRF ranking
    """
    q = q.strip()
    if not q:
        return {
            "query": q,
            "mode": mode,
            "page": page,
            "page_size": limit,
            "total": 0,
            "results": [],
            "retrieval_source": "none",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "warnings": [],
        }

    start_time = time.time()
    offset = (page - 1) * limit

    # ── Phase 1: Live Web Discovery & Indexing ──────────────────────────────
    pipeline = _get_live_pipeline()
    pipeline_meta: Dict[str, Any] = {}
    warnings: List[str] = []

    try:
        pipeline_meta = await pipeline.run(query=q, limit=10)
        warnings.extend(pipeline_meta.get("warnings", []))

        retrieval_source = pipeline_meta.get("retrieval_source", "live_web")
        provider = pipeline_meta.get("provider", "unknown")

        logger.info(
            f"Discovery complete for '{q}': "
            f"discovered={pipeline_meta.get('discovered', 0)}, "
            f"indexed={pipeline_meta.get('indexed', 0)}, "
            f"provider={provider}"
        )

        if retrieval_source == "unavailable":
            warnings.append(
                "Live web discovery is currently unavailable. "
                "Results may come from previously cached pages."
            )
            retrieval_source = "cached"
        else:
            # Annotate source label
            retrieval_source = "live_web"

    except Exception as e:
        logger.error(f"Live pipeline error for '{q}': {e}")
        warnings.append(f"Live web discovery failed: {e}")
        retrieval_source = "cached"

    # ── Phase 2: Hybrid Retrieval over indexed content ──────────────────────
    engine = _get_search_engine()
    try:
        if mode == SearchMode.keyword:
            res = engine.search_keyword(query=q, limit=limit, offset=offset)
        elif mode == SearchMode.semantic:
            res = engine.search_semantic(query=q, limit=limit)
        else:
            res = engine.search_hybrid(query=q, limit=limit, offset=offset)

        results = res.get("results", [])
        total = res.get("total", len(results))

    except Exception as e:
        logger.error(f"Retrieval error for '{q}': {e}")
        raise HTTPException(status_code=500, detail=f"Search retrieval failed: {e}")

    # Annotate each result with retrieval_source for frontend badges
    for r in results:
        r["retrieval_source_label"] = retrieval_source
        if not r.get("source"):
            r["source"] = retrieval_source

    latency_ms = round((time.time() - start_time) * 1000)

    return {
        "query": q,
        "mode": mode,
        "page": page,
        "page_size": limit,
        "total": total,
        "results": results,
        "retrieval_source": retrieval_source,
        "discovery_meta": {
            "discovered": pipeline_meta.get("discovered", 0),
            "indexed": pipeline_meta.get("indexed", 0),
            "provider": pipeline_meta.get("provider", "unknown"),
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "latency_ms": latency_ms,
        "warnings": warnings,
    }
