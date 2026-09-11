import logging
from app.graph.state import SearchState

logger = logging.getLogger(__name__)

class SecurityGateAgent:
    """
    Security Gate: Filters out HIGH_RISK content based on Part 4 metadata
    before it reaches the LLM reasoning or verification pipeline.
    """
    def filter_results(self, state: SearchState) -> SearchState:
        state["execution_trace"].append("security_gate")
        
        raw_results = state.get("retrieval_results", [])
        safe_results = []
        excluded_count = 0
        
        for res in raw_results:
            status = res.get("security_status", "SAFE")
            if status == "HIGH_RISK":
                excluded_count += 1
                logger.warning(f"Security Gate excluded HIGH_RISK source: {res.get('url')}")
            else:
                safe_results.append(res)
                
        state["security_filtered_results"] = safe_results
        
        if excluded_count > 0:
            state["warnings"].append(f"{excluded_count} source(s) were excluded because high prompt-injection risk was detected.")
            
        return state
