import logging
from app.graph.state import SearchState
from app.core.config import settings

logger = logging.getLogger(__name__)

class SourceSelectionAgent:
    """
    Selects the most diverse, high-trust sources from the security-filtered results.
    """
    def select_sources(self, state: SearchState) -> SearchState:
        state["execution_trace"].append("source_selection")
        
        candidates = state.get("security_filtered_results", [])
        max_sources = state.get("max_sources", settings.MAX_VERIFICATION_SOURCES)
        
        selected = []
        seen_domains = set()
        
        # We prioritize highly trusted unique domains
        for doc in candidates:
            if len(selected) >= max_sources:
                break
                
            domain = doc.get("domain", "")
            
            # Simple diversity rule: allow max 2 from same domain if we need more, but prefer 1
            domain_count = sum(1 for s in selected if s.get("domain") == domain)
            
            if domain_count < 2:
                selected.append(doc)
                seen_domains.add(domain)
                
        state["selected_sources"] = selected
        
        if not selected:
            state["insufficient_evidence"] = True
            
        return state
