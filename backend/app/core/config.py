from pydantic_settings import BaseSettings
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

    # ---- Web Discovery ----
    SEARCH_PROVIDER: str = "ddg"          # "brave" | "ddg"
    BRAVE_SEARCH_API_KEY: Optional[str] = None

    # ---- Live Fetch Limits ----
    MAX_DISCOVERY_RESULTS: int = 10
    MAX_FETCH_CONCURRENCY: int = 5
    FETCH_TIMEOUT_SECONDS: int = 10
    MAX_RESPONSE_BYTES: int = 5_000_000   # 5 MB

    # ---- Retrieval ----
    BM25_TOP_K: int = 20
    SEMANTIC_TOP_K: int = 20
    HYBRID_TOP_K: int = 10
    RRF_K: int = 60
    SEMANTIC_SCORE_THRESHOLD: float = 0.50  # Lowered: real web content is diverse

    # ---- LLM ----
    LLM_PROVIDER: str = "mock"
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    LLM_TIMEOUT: int = 30
    LLM_MAX_RETRIES: int = 2

    # ---- Trust & Security ----
    TRUST_WEIGHT: float = 0.2
    SECURITY_RISK_WEIGHT: float = 0.5
    INJECTION_RISK_THRESHOLD: int = 50
    ENABLE_PROMPT_INJECTION_SCAN: bool = True
    ENABLE_TRUST_SCORING: bool = True
    ENABLE_SECURITY_GATE: bool = True

    # ---- Agentic ----
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
