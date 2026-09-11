from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.main import api_router

app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
)

# Set up CORS
if settings.APP_ENV == "development":
    origins = [
        settings.FRONTEND_URL,
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]
else:
    # Production CORS settings should be strict
    origins = [settings.FRONTEND_URL]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "name": f"{settings.APP_NAME} API",
        "status": "running",
        "version": "0.1.0"
    }
