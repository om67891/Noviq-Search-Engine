from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from datetime import datetime

Base = declarative_base()

class PageMetadata(Base):
    __tablename__ = "page_metadata"
    
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, index=True, nullable=False)
    normalized_url = Column(String, unique=True, index=True, nullable=False)
    canonical_url = Column(String, nullable=True)
    title = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    domain = Column(String, index=True, nullable=False)
    path = Column(String, nullable=True)
    
    content_hash = Column(String, index=True, nullable=True)
    content_length = Column(Integer, nullable=True)
    content_snippet = Column(Text, nullable=True)  # First 2000 chars for FTS
    language = Column(String, nullable=True)
    mime_type = Column(String, nullable=True)
    
    source = Column(String, nullable=False, default="common_crawl")
    crawl_source = Column(String, nullable=True)
    http_status = Column(Integer, nullable=True)
    
    fetched_at = Column(DateTime, nullable=True)
    published_at = Column(DateTime, nullable=True)
    last_modified = Column(DateTime, nullable=True)
    
    ingestion_status = Column(String, index=True, nullable=False, default="DISCOVERED")
    failure_reason = Column(Text, nullable=True)
    
    # Trust & Security Part 4
    trust_score = Column(Integer, nullable=True)
    trust_level = Column(String, nullable=True)
    trust_signals = Column(String, nullable=True) # Stored as JSON string for SQLite compat if not using JSONB
    
    security_risk = Column(Integer, nullable=True) # Renamed to Integer (0-100)
    security_status = Column(String, nullable=True) # SAFE, SUSPICIOUS, HIGH_RISK
    security_signals = Column(String, nullable=True) # Stored as JSON string
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
