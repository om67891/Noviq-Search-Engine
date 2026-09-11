from typing import TypedDict, List, Dict, Any, Optional
import operator
from typing_extensions import Annotated

class SearchState(TypedDict):
    """
    Shared state for the Multi-Agent AI Search Engine graph.
    """
    # Core query inputs
    original_query: str
    normalized_query: str
    sub_queries: List[str]
    
    # Planner outputs
    search_modes: List[str]
    verification_required: bool
    max_sources: int
    reasoning_required: bool
    freshness_required: bool
    
    # Retrieval & Trust
    retrieval_results: List[Dict[str, Any]]
    trusted_results: List[Dict[str, Any]]
    security_filtered_results: List[Dict[str, Any]]
    selected_sources: List[Dict[str, Any]]
    
    # Verification & Evidence
    verification_results: List[Dict[str, Any]]
    # Using Annotated to easily append evidence across parallel verification nodes if needed
    evidence: Annotated[List[Dict[str, Any]], operator.add]
    
    # Conflict & Reasoning
    conflicts: List[Dict[str, Any]]
    reasoning: Optional[str]
    
    # Output Generation
    answer: str
    citations: List[Dict[str, Any]]
    confidence: int
    trust_summary: Dict[str, Any]
    
    # Execution & Auditing
    warnings: Annotated[List[str], operator.add]
    errors: Annotated[List[str], operator.add]
    execution_trace: Annotated[List[str], operator.add]
    
    # Control flow
    insufficient_evidence: bool
    iteration_count: int
