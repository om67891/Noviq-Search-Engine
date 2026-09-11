import asyncio
import logging
from typing import List, Optional
from datetime import datetime
import hashlib
from urllib.parse import urlparse

from app.crawler.commoncrawl_client import CommonCrawlClient
from app.crawler.fetcher import Fetcher
from app.crawler.extractor import Extractor
from app.crawler.cleaner import Cleaner
from app.retrieval.chunker import TextChunker
from app.embeddings.service import EmbeddingService
from app.retrieval.qdrant_client import QdrantStore
from app.services.normalization.url_normalizer import normalize_url, validate_url
from app.models.page import PageMetadata
from app.database.session import get_db, SessionLocal
from app.trust.scorer import TrustScorer
from app.security.analyzer import SecurityAnalyzer
from app.services.search.opensearch_client import OpenSearchClient
import json

logger = logging.getLogger(__name__)

class IngestionPipeline:
    def __init__(self):
        self.cc_client = CommonCrawlClient()
        self.fetcher = Fetcher()
        self.extractor = Extractor()
        self.cleaner = Cleaner()
        self.chunker = TextChunker(chunk_size=400, overlap=100)
        self.embedding_service = EmbeddingService()
        self.qdrant = QdrantStore()
        self.trust_scorer = TrustScorer()
        self.security_analyzer = SecurityAnalyzer()
        self.opensearch = OpenSearchClient()
        
    def generate_hash(self, text: str) -> str:
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
        
    async def process_url(self, url: str, source: str = "common_crawl", crawl_source: Optional[str] = None):
        """Processes a single URL through the pipeline."""
        if not validate_url(url):
            logger.warning(f"Invalid URL: {url}")
            return
            
        norm_url = normalize_url(url)
        domain = urlparse(norm_url).netloc
        page_id = self.generate_hash(norm_url)
        
        logger.info(f"Fetching {norm_url}...")
        content, status_code, fetch_error = await self.fetcher.fetch_page(norm_url)
        
        if fetch_error:
            logger.error(f"Fetch failed: {fetch_error}")
            return
            
        logger.info("Extracting content...")
        extracted = self.extractor.extract(content)
        
        if not extracted.get("success") or not extracted.get("text"):
            logger.warning("Extraction failed or empty text")
            return
            
        logger.info("Cleaning content...")
        cleaned_text = self.cleaner.clean_text(extracted["text"])
        
        if not cleaned_text:
            logger.warning("Text is empty after cleaning")
            return
            
        content_hash = self.generate_hash(cleaned_text)
        
        logger.info("Assessing Trust and Security...")
        # Note: We use datetime.utcnow() for freshness in this simple example
        published_at = datetime.utcnow() 
        trust_res = self.trust_scorer.assess_trust(norm_url, domain, cleaned_text, published_at)
        sec_res = self.security_analyzer.assess_security(cleaned_text, domain)
        
        logger.info(f"Trust: {trust_res['trust_score']} | Security: {sec_res['security_status']}")
        
        # Insert/Update in PostgreSQL
        db = SessionLocal()
        try:
            page = db.query(PageMetadata).filter(PageMetadata.url == norm_url).first()
            if not page:
                page = PageMetadata(
                    url=norm_url,
                    normalized_url=norm_url,
                    domain=domain,
                    title=extracted.get("title", ""),
                    content_hash=content_hash,
                    source=source,
                    crawl_source=crawl_source
                )
                db.add(page)
            
            page.trust_score = trust_res["trust_score"]
            page.trust_level = trust_res["trust_level"]
            page.trust_signals = json.dumps(trust_res["trust_signals"])
            page.security_risk = sec_res["security_risk"]
            page.security_status = sec_res["security_status"]
            page.security_signals = json.dumps(sec_res["security_signals"])
            page.ingestion_status = "INDEXED"
            db.commit()
            db.refresh(page)
            
            # Using the primary key as the document_id for OpenSearch
            doc_id = page.id
        except Exception as e:
            logger.error(f"DB Error: {e}")
            db.rollback()
            return
        finally:
            db.close()
            
        logger.info("Indexing in OpenSearch...")
        self.opensearch.index_document(
            document_id=doc_id,
            url=norm_url,
            domain=domain,
            title=extracted.get("title", ""),
            content=cleaned_text,
            content_hash=content_hash,
            trust_score=trust_res["trust_score"],
            trust_level=trust_res["trust_level"],
            security_risk=sec_res["security_risk"],
            security_status=sec_res["security_status"]
        )
        
        logger.info(f"Chunking {norm_url}...")
        # Add metadata required for chunks
        metadata = {
            "page_id": str(doc_id),
            "url": norm_url,
            "domain": domain,
            "title": extracted.get("title", ""),
            "content_hash": content_hash,
            "trust_score": trust_res["trust_score"],
            "trust_level": trust_res["trust_level"],
            "security_risk": sec_res["security_risk"],
            "security_status": sec_res["security_status"]
        }
        chunks = self.chunker.chunk_text(cleaned_text, metadata)
        
        if not chunks:
            logger.warning("No chunks generated")
            return
            
        logger.info(f"Generated {len(chunks)} chunks. Embedding...")
        chunk_texts = [c["text"] for c in chunks]
        embeddings = self.embedding_service.embed_documents(chunk_texts, batch_size=16)
        
        logger.info(f"Upserting {len(chunks)} vectors to Qdrant...")
        # We optionally clean up old chunks by page_id to avoid stale vectors
        self.qdrant.delete_by_page_id(page_id)
        
        success = self.qdrant.upsert_chunks(chunks, embeddings)
        if success:
            logger.info(f"Successfully processed and indexed {norm_url}")
        else:
            logger.error(f"Failed to upsert vectors for {norm_url}")
        
    async def run(self, domain: str, limit: int = 5):
        """Runs the pipeline for a given domain using Common Crawl."""
        records = await self.cc_client.search_urls(domain, limit=limit)
        
        for record in records:
            url = record.get("url")
            crawl_source = record.get("filename") # The WARC file location in CC
            if url:
                await self.process_url(url, crawl_source=crawl_source)
