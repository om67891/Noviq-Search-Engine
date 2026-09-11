from fastapi import APIRouter
from app.api.routes import health, search, agentic_search

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(agentic_search.router, prefix="/agentic-search", tags=["agentic-search"])
