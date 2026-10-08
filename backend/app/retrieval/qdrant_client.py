import logging
from typing import List, Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

# Module-level flag — set once at startup, prevents repeated connection attempts
_qdrant_available: Optional[bool] = None


def _check_qdrant_once(host: str, api_key: str) -> bool:
    """One-shot connectivity check. If Qdrant is unreachable, disable for entire session."""
    global _qdrant_available
    if _qdrant_available is not None:
        return _qdrant_available

    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(
            url=host,
            api_key=api_key,
            prefer_grpc=False,
            timeout=5,
        )
        # Light check — just list collections
        client.get_collections()
        _qdrant_available = True
        logger.info("Qdrant Cloud is reachable — semantic search enabled.")
        return True
    except Exception as e:
        _qdrant_available = False
        logger.warning(f"Qdrant Cloud unreachable — semantic search disabled for this session. ({e})")
        return False


class QdrantStore:
    def __init__(self):
        self.collection_name = settings.QDRANT_COLLECTION

        host = settings.QDRANT_URL or "http://localhost:6333"
        api_key = settings.QDRANT_API_KEY

        # Check connectivity once — if it fails, self.client stays None permanently
        if not _check_qdrant_once(host, api_key):
            self.client = None
            return

        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams
            self.client = QdrantClient(
                url=host,
                api_key=api_key,
                prefer_grpc=False,
                check_compatibility=False,
                timeout=10,
            )
        except Exception as e:
            logger.error(f"Failed to initialize QdrantClient: {e}")
            self.client = None
            return

        self._ensure_collection()

    def _ensure_collection(self):
        if not self.client:
            return

        try:
            from qdrant_client.models import Distance, VectorParams
            if not self.client.collection_exists(self.collection_name):
                # BAAI/bge-small-en-v1.5 produces 384-dimensional vectors
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE),
                )
                logger.info(f"Created Qdrant collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error ensuring Qdrant collection: {e}")

    def upsert_chunks(self, chunks: List[Dict[str, Any]], embeddings: List[List[float]]):
        """Upserts a batch of chunks and their vectors into Qdrant."""
        if not self.client or not chunks or not embeddings:
            return False

        if len(chunks) != len(embeddings):
            logger.error("Chunks and embeddings length mismatch")
            return False

        from qdrant_client.models import PointStruct
        import uuid

        points = []
        for i, chunk in enumerate(chunks):
            chunk_id = chunk["chunk_id"]
            point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, chunk_id))

            points.append(
                PointStruct(
                    id=point_id,
                    vector=embeddings[i],
                    payload=chunk
                )
            )

        try:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            return True
        except Exception as e:
            logger.error(f"Failed to upsert vectors to Qdrant: {e}")
            return False

    def delete_by_page_id(self, page_id: str):
        """Deletes all chunks associated with a specific page_id."""
        if not self.client:
            return

        from qdrant_client.http.models import Filter, FieldCondition, MatchValue

        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="page_id",
                            match=MatchValue(value=page_id)
                        )
                    ]
                )
            )
        except Exception as e:
            logger.error(f"Failed to delete old vectors for page {page_id}: {e}")

    def search(self, query_vector: List[float], limit: int = 30) -> List[Dict[str, Any]]:
        """Performs vector similarity search."""
        if not self.client:
            return []

        try:
            results = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                limit=limit,
                score_threshold=settings.SEMANTIC_SCORE_THRESHOLD
            )

            # Extract points from QueryResponse
            results = results.points if hasattr(results, "points") else results

            formatted_results = []
            for hit in results:
                payload = hit.payload or {}
                formatted_results.append({
                    "id": payload.get("page_id"),
                    "chunk_id": payload.get("chunk_id"),
                    "url": payload.get("url"),
                    "domain": payload.get("domain"),
                    "title": payload.get("title"),
                    "snippet": payload.get("text"),
                    "score": hit.score,
                    "retrieval_sources": ["vector"],
                    "trust_score": payload.get("trust_score", 0),
                    "trust_level": payload.get("trust_level", "Low"),
                    "security_risk": payload.get("security_risk", 0),
                    "security_status": payload.get("security_status", "SAFE")
                })

            return formatted_results
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []
