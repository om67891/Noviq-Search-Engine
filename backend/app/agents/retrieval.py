"""
Retrieval Agent — discovers and retrieves content for the Agentic Search workflow.

This agent now:
  1. Calls LiveSearchPipeline to discover and index real web content for the query
  2. Then runs HybridSearchEngine over the freshly indexed content

This ensures the agentic pipeline operates on actual web evidence rather
than a static synthetic corpus.
"""
import asyncio
import logging

from app.graph.state import SearchState
from app.pipeline.live_search import LiveSearchPipeline
from app.retrieval.hybrid_search import HybridSearchEngine

logger = logging.getLogger(__name__)

# Module-level singletons
_pipeline: LiveSearchPipeline | None = None
_engine: HybridSearchEngine | None = None


def _get_pipeline() -> LiveSearchPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = LiveSearchPipeline()
    return _pipeline


def _get_engine() -> HybridSearchEngine:
    global _engine
    if _engine is None:
        _engine = HybridSearchEngine()
    return _engine


class RetrievalAgent:
    def retrieve(self, state: SearchState) -> SearchState:
        """
        Discovers real web content for each sub-query then retrieves results.
        """
        state["execution_trace"].append("retrieval")
        queries = state.get("sub_queries") or [state["original_query"]]
        search_mode = (state.get("search_modes") or ["hybrid"])[0]
        limit_per_query = max(5, state.get("max_sources", 5))

        all_results = []
        seen_urls: set = set()
        pipeline = _get_pipeline()
        engine = _get_engine()

        for q in queries:
            logger.info(f"[RetrievalAgent] Discovering + retrieving for: '{q}'")

            # Run live discovery synchronously (we're inside a sync LangGraph node)
            try:
                loop = asyncio.new_event_loop()
                meta = loop.run_until_complete(pipeline.run(query=q, limit=10))
                loop.close()
                logger.info(
                    f"[RetrievalAgent] Discovery: discovered={meta.get('discovered',0)}, "
                    f"indexed={meta.get('indexed',0)}"
                )
                if meta.get("retrieval_source") == "unavailable":
                    state["warnings"].append(
                        f"Live web discovery unavailable for '{q}'. "
                        "Results may be limited to cached pages."
                    )
            except Exception as e:
                logger.error(f"[RetrievalAgent] Discovery failed for '{q}': {e}")
                state["warnings"].append(f"Web discovery failed for '{q}': {e}")

            # Retrieve from now-updated index
            try:
                if search_mode == "keyword":
                    res = engine.search_keyword(q, limit=limit_per_query)
                elif search_mode == "semantic":
                    res = engine.search_semantic(q, limit=limit_per_query)
                else:
                    res = engine.search_hybrid(q, limit=limit_per_query)

                for r in res.get("results", []):
                    url = r.get("url", "")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        all_results.append(r)

            except Exception as e:
                logger.error(f"[RetrievalAgent] Search failed for '{q}': {e}")
                state["errors"].append(f"Retrieval failed for '{q}': {e}")

        # Sort by final score
        all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
        state["retrieval_results"] = all_results

        if not all_results:
            state["insufficient_evidence"] = True

        return state
