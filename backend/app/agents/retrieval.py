import logging
from app.graph.state import SearchState
from app.retrieval.hybrid_search import HybridSearchEngine

logger = logging.getLogger(__name__)

class RetrievalAgent:
    def __init__(self):
        self.search_engine = HybridSearchEngine()
        
    def retrieve(self, state: SearchState) -> SearchState:
        """
        Executes search for all subqueries and aggregates results.
        """
        state["execution_trace"].append("retrieval")
        queries = state.get("sub_queries", [state["original_query"]])
        search_mode = state.get("search_modes", ["hybrid"])[0] # take primary mode
        limit_per_query = max(5, state.get("max_sources", 5))
        
        all_results = []
        seen_urls = set()
        
        for q in queries:
            logger.info(f"Retrieval Agent searching for: '{q}' (mode: {search_mode})")
            try:
                if search_mode == "keyword":
                    res = self.search_engine.search_keyword(q, limit=limit_per_query)
                elif search_mode == "semantic":
                    res = self.search_engine.search_semantic(q, limit=limit_per_query)
                else:
                    res = self.search_engine.search_hybrid(q, limit=limit_per_query)
                    
                for r in res.get("results", []):
                    if r["url"] not in seen_urls:
                        seen_urls.add(r["url"])
                        all_results.append(r)
            except Exception as e:
                logger.error(f"Search failed for query '{q}': {e}")
                state["errors"].append(f"Retrieval failed for '{q}': {str(e)}")
                
        # Sort by final score descending
        all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        state["retrieval_results"] = all_results
        
        if not all_results:
            state["insufficient_evidence"] = True
            
        return state
