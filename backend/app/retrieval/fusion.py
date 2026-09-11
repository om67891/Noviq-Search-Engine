from typing import List, Dict, Any

class ReciprocalRankFusion:
    def __init__(self, k: int = 60):
        self.k = k

    def fuse(self, bm25_results: List[Dict[str, Any]], vector_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Fuses BM25 and Vector search results using Reciprocal Rank Fusion.
        Deduplicates by URL or ID.
        """
        fused_scores = {}
        items_map = {}
        
        # Process BM25 results
        for rank, item in enumerate(bm25_results):
            # Try to deduplicate by URL first, fallback to id
            key = item.get("url") or item.get("id")
            if not key:
                continue
                
            items_map[key] = items_map.get(key) or {
                **item,
                "retrieval_sources": []
            }
            if "bm25" not in items_map[key]["retrieval_sources"]:
                items_map[key]["retrieval_sources"].append("bm25")
            
            fused_scores[key] = fused_scores.get(key, 0.0) + (1.0 / (self.k + rank + 1))
            items_map[key]["bm25_rank"] = rank + 1

        # Process Vector results
        for rank, item in enumerate(vector_results):
            key = item.get("url") or item.get("id")
            if not key:
                continue
                
            if key not in items_map:
                items_map[key] = {
                    **item,
                    "retrieval_sources": []
                }
            elif "snippet" in item and len(item["snippet"]) > len(items_map[key].get("snippet", "")):
                # If vector result has a better/longer snippet (chunk), we might want to prefer it
                items_map[key]["snippet"] = item["snippet"]
                items_map[key]["chunk_id"] = item.get("chunk_id")
                
            if "vector" not in items_map[key]["retrieval_sources"]:
                items_map[key]["retrieval_sources"].append("vector")
                
            fused_scores[key] = fused_scores.get(key, 0.0) + (1.0 / (self.k + rank + 1))
            items_map[key]["vector_rank"] = rank + 1

        # Combine and sort by final RRF score
        fused_results = []
        for key, score in fused_scores.items():
            result = items_map[key].copy()
            result["score"] = score
            fused_results.append(result)
            
        fused_results.sort(key=lambda x: x["score"], reverse=True)
        return fused_results
