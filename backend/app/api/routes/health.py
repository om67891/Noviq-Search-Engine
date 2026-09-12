"""Health endpoint for Noviq — exposes service connectivity status."""
import logging
from typing import Any, Dict

import httpx
from fastapi import APIRouter

from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint.
    Returns connectivity status for all Noviq services.
    Does NOT expose credentials.
    """
    services: Dict[str, str] = {}

    # PostgreSQL
    try:
        from app.database.session import SessionLocal
        db = SessionLocal()
        db.execute(__import__("sqlalchemy").text("SELECT 1"))
        db.close()
        services["postgres"] = "ok"
    except Exception as e:
        services["postgres"] = f"error: {type(e).__name__}"

    # Qdrant
    try:
        from app.retrieval.qdrant_client import QdrantStore
        qs = QdrantStore()
        # Try listing collections as a health check
        qs.client.get_collections()
        services["qdrant"] = "ok"
    except Exception as e:
        services["qdrant"] = f"error: {type(e).__name__}"

    # OpenSearch
    try:
        from app.services.search.opensearch_client import OpenSearchClient
        osc = OpenSearchClient()
        osc.client.info()
        services["opensearch"] = "ok"
    except Exception as e:
        services["opensearch"] = f"error: {type(e).__name__}"

    # Redis
    try:
        redis_url = getattr(settings, "REDIS_URL", None)
        if redis_url:
            import redis as redis_lib
            r = redis_lib.from_url(redis_url)
            r.ping()
            services["redis"] = "ok"
        else:
            services["redis"] = "not configured"
    except Exception as e:
        services["redis"] = f"error: {type(e).__name__}"

    # Search Provider
    provider_name = getattr(settings, "SEARCH_PROVIDER", "ddg")
    brave_key = getattr(settings, "BRAVE_SEARCH_API_KEY", "") or ""
    if provider_name == "brave":
        if brave_key:
            services["search_provider"] = "brave (configured)"
        else:
            services["search_provider"] = "brave (key missing — falling back to ddg)"
    else:
        services["search_provider"] = "ddg (no API key required)"

    overall = "healthy" if all(v == "ok" or "configured" in v for v in services.values()) else "degraded"

    return {
        "status": overall,
        "services": services,
        "search_provider": provider_name,
    }
