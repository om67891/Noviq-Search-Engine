from pydantic_settings import BaseSettings
import os
from typing import Optional

class Settings(BaseSettings):
    APP_ENV: str = "development"
    APP_NAME: str = "Noviq"
    
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    FRONTEND_URL: str = "http://localhost:3000"
    
    DATABASE_URL: Optional[str] = None
    
    QDRANT_URL: Optional[str] = None
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_COLLECTION: str = "noviq-page-chunks-v1"
    
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    EMBEDDING_DEVICE: str = "auto"
    
    OPENSEARCH_URL: Optional[str] = None
    OPENSEARCH_USERNAME: Optional[str] = None
    OPENSEARCH_PASSWORD: Optional[str] = None
    
    REDIS_URL: Optional[str] = None
    
    LLM_PROVIDER: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    
    # Trust & Security Part 4
    TRUST_WEIGHT: float = 0.2
    SECURITY_RISK_WEIGHT: float = 0.5
    INJECTION_RISK_THRESHOLD: int = 50
    
    # Agentic Search Part 5
    LLM_PROVIDER: str = "mock"
    LLM_TIMEOUT: int = 30
    LLM_MAX_RETRIES: int = 2
    MAX_SUBQUERIES: int = 4
    MAX_VERIFICATION_SOURCES: int = 5
    MAX_SOURCE_CHARS: int = 4000
    MAX_AGENT_ITERATIONS: int = 3
    MAX_RETRIEVAL_ROUNDS: int = 2

    class Config:
        env_file = "../.env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()
