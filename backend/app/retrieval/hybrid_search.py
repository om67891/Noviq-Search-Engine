import logging
from typing import Dict, Any, List
from app.services.search.opensearch_client import OpenSearchClient
from app.retrieval.qdrant_client import QdrantStore
from app.embeddings.service import EmbeddingService
from app.retrieval.fusion import ReciprocalRankFusion
from app.core.config import settings

logger = logging.getLogger(__name__)

class HybridSearchEngine:
    def __init__(self):
        self.opensearch_client = OpenSearchClient()
        self.qdrant_client = QdrantStore()
        self.embedding_service = EmbeddingService()
        self.fusion = ReciprocalRankFusion(k=60)
        
    def _apply_trust_ranking(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not results:
            return results
            
        # Get max score to normalize base scores for keyword/semantic modes if they aren't already RRF (0-1)
        # RRF scores are already small (e.g., < 0.05). BM25 can be > 10. Cosine is 0-1.
        # We'll do a simple local scaling if the max score > 1 to bring it to a 0-1 range for fair combination.
        max_score = max((r.get("score", 0) for r in results), default=1.0)
        scale_factor = 1.0 if max_score <= 1.0 else (1.0 / max_score)
            
        for item in results:
            trust = item.get("trust_score", 0)
            risk = item.get("security_risk", 0)
            
            base_score = item.get("score", 0) * scale_factor
            trust_comp = (trust / 100.0) * settings.TRUST_WEIGHT
            risk_comp = (risk / 100.0) * settings.SECURITY_RISK_WEIGHT
            
            # Strong penalty for HIGH_RISK
            if item.get("security_status") == "HIGH_RISK":
                risk_comp += 0.5 # Additional penalty
                
            item["score"] = base_score + trust_comp - risk_comp
            
        results.sort(key=lambda x: x["score"], reverse=True)
        return results
        
    def search_keyword(self, query: str, limit: int = 10, offset: int = 0) -> Dict[str, Any]:
        logger.info(f"Executing keyword search for: '{query}'")
        res = self.opensearch_client.search(query=query, limit=limit, offset=offset)
        res["results"] = self._apply_trust_ranking(res.get("results", []))
        return res
        
    def search_semantic(self, query: str, limit: int = 10) -> Dict[str, Any]:
        logger.info(f"Executing semantic search for: '{query}'")
        try:
            query_vector = self.embedding_service.embed_query(query)
            if not query_vector:
                return {"total": 0, "results": []}
                
            results = self.qdrant_client.search(query_vector=query_vector, limit=limit)
            results = self._apply_trust_ranking(results)
            return {"total": len(results), "results": results}
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return {"total": 0, "results": []}
            
    def search_hybrid(self, query: str, limit: int = 10, offset: int = 0, candidate_k: int = 30) -> Dict[str, Any]:
        logger.info(f"Executing hybrid search for: '{query}'")
        
        # BM25 Search
        bm25_res = self.opensearch_client.search(query=query, limit=candidate_k, offset=0)
        bm25_results = bm25_res.get("results", [])
        
        # Vector Search
        semantic_results = []
        try:
            query_vector = self.embedding_service.embed_query(query)
            if query_vector:
                semantic_results = self.qdrant_client.search(query_vector=query_vector, limit=candidate_k)
        except Exception as e:
            logger.error(f"Vector search failed during hybrid mode (fallback to BM25): {e}")
            
        # Fusion
        fused = self.fusion.fuse(bm25_results, semantic_results)
        
        # Trust-Aware Re-ranking (Part 4)
        fused = self._apply_trust_ranking(fused)
        
        # Pagination
        paginated_results = fused[offset : offset + limit]
        
        return {
            "total": len(fused), # Approximate total
            "results": paginated_results
        }
