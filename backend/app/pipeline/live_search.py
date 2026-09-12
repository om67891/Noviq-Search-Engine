"""
LiveSearchPipeline — Noviq's query-time web discovery and indexing pipeline.

This is the component that makes Noviq a real search engine rather than a
static index retrieval system.

Flow:
  1. Call discovery provider (Brave/DDG) with the user query
  2. For each discovered URL:
     a. SSRF guard check
     b. Fetch page content (SecureFetcher)
     c. Extract text via Trafilatura
     d. Prompt injection security scan
     e. Trust scoring
     f. Chunk text
     g. Embed chunks (BGE)
     h. Upsert to Qdrant
     i. Index in OpenSearch (BM25)
     j. Store metadata in PostgreSQL
  3. Return retrieval_source metadata

After this pipeline runs, HybridSearchEngine will search over the NEWLY
discovered and indexed content rather than a stale synthetic corpus.

This pipeline is called on EVERY search request (with Redis caching for
recently-seen URLs to avoid redundant fetching within a TTL window).
"""
import asyncio
import hashlib
import json
import logging
from datetime import datetime
from typing import List, Optional
from urllib.parse import urlparse

import httpx
import trafilatura

from app.core.config import settings
from app.database.session import SessionLocal
from app.discovery.base import DiscoveredPage
from app.discovery.factory import get_provider
from app.discovery.ssrf_guard import SSRFError, guard as ssrf_guard
from app.embeddings.service import EmbeddingService
from app.models.page import PageMetadata
from app.retrieval.chunker import TextChunker
from app.retrieval.qdrant_client import QdrantStore
from app.security.analyzer import SecurityAnalyzer
from app.services.normalization.url_normalizer import normalize_url
from app.services.search.opensearch_client import OpenSearchClient
from app.trust.scorer import TrustScorer

logger = logging.getLogger(__name__)


class LiveSearchPipeline:
    """
    Orchestrates query-time web discovery, fetching, extraction, and indexing.
    """

    def __init__(self):
        self.provider = get_provider()
        self.chunker = TextChunker(chunk_size=400, overlap=100)
        self.embedding_service = EmbeddingService()
        self.qdrant = QdrantStore()
        self.opensearch = OpenSearchClient()
        self.trust_scorer = TrustScorer()
        self.security_analyzer = SecurityAnalyzer()
        self._redis = None  # Lazy init

    def _get_redis(self):
        """Lazy Redis connection for URL deduplication/caching."""
        if self._redis is None:
            try:
                import redis as redis_lib
                redis_url = getattr(settings, "REDIS_URL", None)
                if redis_url:
                    self._redis = redis_lib.from_url(redis_url, decode_responses=True)
            except Exception as e:
                logger.warning(f"Redis unavailable, skip caching: {e}")
        return self._redis

    def _is_recently_indexed(self, url: str) -> bool:
        """Check Redis cache — True if URL was indexed within the last 1 hour."""
        r = self._get_redis()
        if not r:
            return False
        try:
            return r.exists(f"noviq:indexed:{url}") == 1
        except Exception:
            return False

    def _mark_indexed(self, url: str, ttl_seconds: int = 3600) -> None:
        """Mark URL as recently indexed in Redis."""
        r = self._get_redis()
        if not r:
            return
        try:
            r.setex(f"noviq:indexed:{url}", ttl_seconds, "1")
        except Exception:
            pass

    async def _fetch_page(self, url: str, timeout: int = 10) -> Optional[str]:
        """
        Fetch a URL with SSRF protection and size limits.
        Returns raw HTML or None on failure.
        """
        try:
            ssrf_guard(url)
        except SSRFError as e:
            logger.warning(f"SSRF blocked: {url} — {e}")
            return None

        headers = {
            "User-Agent": "Noviq/1.0 (Research Search Engine; +https://github.com/noviq)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        max_bytes = getattr(settings, "MAX_RESPONSE_BYTES", 5_000_000)

        try:
            async with httpx.AsyncClient(
                timeout=timeout,
                follow_redirects=True,
                max_redirects=5,
                headers=headers,
            ) as client:
                response = await client.get(url)
                response.raise_for_status()

                # Enforce size limit
                content = response.text
                if len(content.encode("utf-8")) > max_bytes:
                    logger.warning(f"Response too large for {url}, truncating")
                    content = content[:max_bytes]

                return content
        except SSRFError:
            return None
        except httpx.TimeoutException:
            logger.warning(f"Fetch timeout: {url}")
            return None
        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP {e.response.status_code}: {url}")
            return None
        except Exception as e:
            logger.warning(f"Fetch error for {url}: {e}")
            return None

    def _extract_text(self, html: str, url: str) -> Optional[str]:
        """Extract main text content using Trafilatura."""
        try:
            text = trafilatura.extract(
                html,
                url=url,
                include_comments=False,
                include_tables=True,
                no_fallback=False,
                favor_precision=False,
            )
            return text if text and len(text.strip()) > 50 else None
        except Exception as e:
            logger.warning(f"Extraction failed for {url}: {e}")
            return None

    def _content_hash(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    async def _process_discovered_page(
        self, page: DiscoveredPage, query: str
    ) -> bool:
        """
        Full processing pipeline for a single discovered page.
        Returns True if successfully indexed.
        """
        url = normalize_url(page.url)
        domain = urlparse(url).netloc

        # Skip if recently indexed (cache hit)
        if self._is_recently_indexed(url):
            logger.info(f"Cache hit, skipping re-index: {url}")
            return True

        # Fetch
        html = await self._fetch_page(url)
        if not html:
            return False

        # Extract
        text = self._extract_text(html, url)
        if not text:
            logger.warning(f"No usable text extracted from: {url}")
            return False

        content_hash = self._content_hash(text)

        # Security scan
        sec = self.security_analyzer.assess_security(text, domain)
        security_risk = sec.get("security_risk", 0)
        security_status = sec.get("security_status", "UNKNOWN")

        # Trust scoring (TrustScorer uses naive UTC datetimes internally)
        trust = self.trust_scorer.assess_trust(
            url, domain, text, published_at=datetime.utcnow()
        )
        trust_score = trust.get("trust_score", 0)
        trust_level = trust.get("trust_level", "Unknown")

        # Store in PostgreSQL
        db = SessionLocal()
        doc_id = None
        try:
            existing = db.query(PageMetadata).filter(PageMetadata.url == url).first()
            if existing:
                # Update existing record
                existing.content_hash = content_hash
                existing.trust_score = trust_score
                existing.trust_level = trust_level
                existing.security_risk = security_risk
                existing.security_status = security_status
                existing.ingestion_status = "INDEXED"
                existing.source = "live_web"
                db.commit()
                db.refresh(existing)
                doc_id = existing.id
            else:
                new_page = PageMetadata(
                    url=url,
                    normalized_url=url,
                    domain=domain,
                    title=page.title or "",
                    content_hash=content_hash,
                    source="live_web",
                    trust_score=trust_score,
                    trust_level=trust_level,
                    security_risk=security_risk,
                    security_status=security_status,
                    ingestion_status="INDEXED",
                )
                db.add(new_page)
                db.commit()
                db.refresh(new_page)
                doc_id = new_page.id
        except Exception as e:
            logger.error(f"DB error for {url}: {e}")
            db.rollback()
            return False
        finally:
            db.close()

        if doc_id is None:
            return False

        # Index in OpenSearch (BM25)
        try:
            self.opensearch.index_document(
                document_id=doc_id,
                url=url,
                domain=domain,
                title=page.title or "",
                content=text,
                content_hash=content_hash,
                trust_score=trust_score,
                trust_level=trust_level,
                security_risk=security_risk,
                security_status=security_status,
            )
        except Exception as e:
            logger.error(f"OpenSearch index error for {url}: {e}")

        # Chunk, embed, and upsert to Qdrant
        try:
            metadata = {
                "page_id": str(doc_id),
                "url": url,
                "domain": domain,
                "title": page.title or "",
                "content_hash": content_hash,
                "trust_score": trust_score,
                "trust_level": trust_level,
                "security_risk": security_risk,
                "security_status": security_status,
                "source": "live_web",
            }
            chunks = self.chunker.chunk_text(text, metadata)
            if chunks:
                chunk_texts = [c["text"] for c in chunks]
                embeddings = self.embedding_service.embed_documents(
                    chunk_texts, batch_size=16
                )
                self.qdrant.upsert_chunks(chunks, embeddings)
        except Exception as e:
            logger.error(f"Qdrant upsert error for {url}: {e}")

        # Mark as indexed in Redis cache
        self._mark_indexed(url)

        logger.info(
            f"Indexed live web page: {url} "
            f"[trust={trust_score}, security={security_status}]"
        )
        return True

    async def run(self, query: str, limit: int = 10) -> dict:
        """
        Run the full live search pipeline for a query.

        Returns a metadata dict describing what was discovered and indexed:
          {
            "discovered": int,
            "indexed": int,
            "failed": int,
            "retrieval_source": "live_web" | "unavailable",
            "provider": str,
            "warnings": list[str]
          }
        """
        logger.info(f"[LiveSearch] Starting pipeline for query: '{query}'")
        warnings = []

        max_results = getattr(settings, "MAX_DISCOVERY_RESULTS", 10)
        max_concurrency = getattr(settings, "MAX_FETCH_CONCURRENCY", 5)

        # Discover URLs
        try:
            discovered: List[DiscoveredPage] = await self.provider.search(
                query, limit=max_results
            )
        except Exception as e:
            logger.error(f"[LiveSearch] Discovery provider error: {e}")
            warnings.append(f"Web discovery unavailable: {e}")
            return {
                "discovered": 0,
                "indexed": 0,
                "failed": 0,
                "retrieval_source": "unavailable",
                "provider": self.provider.name,
                "warnings": warnings,
            }

        if not discovered:
            logger.warning(f"[LiveSearch] No URLs discovered for '{query}'")
            warnings.append("No web pages were discovered for this query.")
            return {
                "discovered": 0,
                "indexed": 0,
                "failed": 0,
                "retrieval_source": "unavailable",
                "provider": self.provider.name,
                "warnings": warnings,
            }

        logger.info(
            f"[LiveSearch] Discovered {len(discovered)} pages for '{query}', "
            f"processing up to {max_concurrency} concurrently."
        )

        # Process pages concurrently with bounded semaphore
        semaphore = asyncio.Semaphore(max_concurrency)
        indexed = 0
        failed = 0

        async def process_with_semaphore(page: DiscoveredPage) -> bool:
            async with semaphore:
                return await self._process_discovered_page(page, query)

        tasks = [process_with_semaphore(p) for p in discovered]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for r in results:
            if isinstance(r, Exception):
                failed += 1
                logger.error(f"[LiveSearch] Pipeline task error: {r}")
            elif r:
                indexed += 1
            else:
                failed += 1

        logger.info(
            f"[LiveSearch] Done. discovered={len(discovered)}, "
            f"indexed={indexed}, failed={failed}"
        )

        return {
            "discovered": len(discovered),
            "indexed": indexed,
            "failed": failed,
            "retrieval_source": "live_web",
            "provider": self.provider.name,
            "warnings": warnings,
        }
