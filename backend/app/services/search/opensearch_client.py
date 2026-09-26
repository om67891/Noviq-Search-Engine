"""
PostgreSQL Full-Text Search client — replaces OpenSearch/Elasticsearch.

Why: OpenSearch requires a separate running service (port 9200) which does not
exist on Render's free tier. PostgreSQL (which is already deployed) has a
built-in tsvector/tsquery full-text search engine that is production-ready
and sufficient for keyword search on a live-web search engine.

The same interface as the old OpenSearchClient is preserved so no other
files need to change.
"""
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import text

from app.database.session import SessionLocal

logger = logging.getLogger(__name__)


class OpenSearchClient:
    """
    Drop-in replacement for the OpenSearch client.
    Uses PostgreSQL tsvector full-text search for BM25-style keyword retrieval.
    All public method signatures are identical to the original OpenSearchClient.
    """

    def __init__(self):
        # No external connection needed — uses the existing PostgreSQL session
        self._ensure_fts_columns()

    def _ensure_fts_columns(self):
        """
        Ensures the page_metadata table has a tsvector column for full-text search.
        Creates a GIN index for fast search if it doesn't already exist.
        Runs once on startup — safe to call multiple times.
        """
        db = SessionLocal()
        try:
            # Step 1: Ensure the snippet column exists first! (Silent failure fix)
            db.execute(text("""
                ALTER TABLE page_metadata
                ADD COLUMN IF NOT EXISTS content_snippet TEXT;
            """))
            db.commit()

            # Step 2: Now we can safely create the search_vector that depends on it
            db.execute(text("""
                ALTER TABLE page_metadata
                ADD COLUMN IF NOT EXISTS search_vector tsvector
                    GENERATED ALWAYS AS (
                        setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
                        setweight(to_tsvector('english', coalesce(content_snippet, '')), 'B')
                    ) STORED;
            """))

            # Add GIN index for fast full-text search
            db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_page_metadata_fts
                ON page_metadata USING GIN (search_vector);
            """))

            db.commit()
            logger.info("PostgreSQL FTS column and index verified.")
        except Exception as e:
            # Column might already exist or table might not be set up yet — safe to ignore
            db.rollback()
            logger.warning(f"FTS setup note (may be safe to ignore): {e}")
        finally:
            db.close()

    def ensure_index(self):
        """Compatibility stub — no-op for PostgreSQL backend."""
        pass

    def index_document(
        self,
        document_id: int,
        url: str,
        domain: str,
        title: Optional[str],
        content: str,
        content_hash: str,
        language: Optional[str] = None,
        trust_score: int = 0,
        trust_level: str = "Low",
        security_risk: int = 0,
        security_status: str = "SAFE",
    ) -> bool:
        """
        Stores a content snippet in PostgreSQL for full-text search.
        Updates the content_snippet column on the existing page_metadata row.
        """
        # Store first 2000 chars as snippet for FTS
        snippet = content[:2000] if content else ""

        db = SessionLocal()
        try:
            db.execute(
                text("""
                    UPDATE page_metadata
                    SET content_snippet = :snippet
                    WHERE id = :doc_id
                """),
                {"snippet": snippet, "doc_id": document_id},
            )
            db.commit()
            return True
        except Exception as e:
            logger.error(f"FTS index_document error for id={document_id}: {e}")
            db.rollback()
            return False
        finally:
            db.close()

    def search(self, query: str, limit: int = 10, offset: int = 0) -> Dict[str, Any]:
        """
        Performs full-text keyword search using PostgreSQL tsvector.
        Returns results in the same format as the original OpenSearch client.
        """
        if not query or not query.strip():
            return {"total": 0, "results": []}

        db = SessionLocal()
        try:
            # Use plainto_tsquery for natural language queries (handles multi-word gracefully)
            rows = db.execute(
                text("""
                    SELECT
                        id,
                        url,
                        domain,
                        title,
                        content_snippet,
                        trust_score,
                        trust_level,
                        security_risk,
                        security_status,
                        ts_rank(search_vector, plainto_tsquery('english', :query)) AS rank
                    FROM page_metadata
                    WHERE
                        search_vector @@ plainto_tsquery('english', :query)
                        AND ingestion_status = 'INDEXED'
                    ORDER BY rank DESC
                    LIMIT :limit OFFSET :offset
                """),
                {"query": query, "limit": limit, "offset": offset},
            ).fetchall()

            # Count total matches
            total_row = db.execute(
                text("""
                    SELECT COUNT(*)
                    FROM page_metadata
                    WHERE
                        search_vector @@ plainto_tsquery('english', :query)
                        AND ingestion_status = 'INDEXED'
                """),
                {"query": query},
            ).fetchone()

            total = total_row[0] if total_row else 0

            results = []
            for row in rows:
                snippet = row.content_snippet or ""
                results.append(
                    {
                        "id": str(row.id),
                        "url": row.url,
                        "domain": row.domain,
                        "title": row.title,
                        "snippet": snippet[:300] + "..." if len(snippet) > 300 else snippet,
                        "score": float(row.rank),
                        "trust_score": row.trust_score or 0,
                        "trust_level": row.trust_level or "Low",
                        "security_risk": row.security_risk or 0,
                        "security_status": row.security_status or "SAFE",
                        "retrieval_sources": ["bm25"],
                    }
                )

            return {"total": total, "results": results}

        except Exception as e:
            logger.error(f"PostgreSQL FTS search error: {e}")
            return {"total": 0, "results": []}
        finally:
            db.close()
