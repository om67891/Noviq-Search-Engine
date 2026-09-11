from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()

@router.get("/health")
async def health_check():
    return {
        "name": settings.APP_NAME,
        "status": "running"
    }
