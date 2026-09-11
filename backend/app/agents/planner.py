import logging
from typing import List
from pydantic import BaseModel, Field
from app.graph.state import SearchState
from app.llm.base import LLMProvider
from app.core.config import settings

logger = logging.getLogger(__name__)

class SearchPlan(BaseModel):
    intent: str = Field(description="The primary intent of the query (e.g., factual, comparison, freshness).")
    sub_queries: List[str] = Field(description="Sub-queries to execute, preserving original intent.")
    search_modes: List[str] = Field(description="Search modes to use (e.g., ['hybrid']).")
    verification_required: bool = Field(description="Whether multi-source verification is needed.")
    max_sources: int = Field(description="Maximum number of sources to retrieve and verify.")
    reasoning_required: bool = Field(description="Whether a multi-step reasoning phase is needed.")
    freshness_required: bool = Field(description="Whether the answer requires recent information.")

class PlannerAgent:
    def __init__(self, llm: LLMProvider):
        self.llm = llm
        
    def plan(self, state: SearchState) -> SearchState:
        """
        Takes the user query and generates a structured search plan.
        """
        logger.info(f"Planner processing query: '{state['original_query']}'")
        state["execution_trace"].append("planner")
        
        prompt = f"""
        Analyze the following query and output a structured search plan.
        Query: {state['original_query']}
        
        Consider whether this requires comparison, factual lookup, or time-sensitive data.
        Limit sub_queries to {settings.MAX_SUBQUERIES}.
        """
        
        try:
            plan = self.llm.generate_structured(
                prompt=prompt,
                output_schema=SearchPlan,
                system_prompt="You are a Search Planner Agent. Output valid JSON adhering to the SearchPlan schema."
            )
            
            state["sub_queries"] = plan.sub_queries[:settings.MAX_SUBQUERIES]
            state["search_modes"] = plan.search_modes
            state["verification_required"] = plan.verification_required
            state["max_sources"] = plan.max_sources
            state["reasoning_required"] = plan.reasoning_required
            state["freshness_required"] = plan.freshness_required
            
        except Exception as e:
            logger.error(f"LLM Planner failed, falling back to deterministic planning: {e}")
            state["warnings"].append("Planner LLM failed, using fallback deterministic planner.")
            self._fallback_plan(state)
            
        # Initialize or increment loop counters
        if "iteration_count" not in state or state["iteration_count"] == 0:
            state["iteration_count"] = 1
        else:
            state["iteration_count"] += 1
            
        # Reset insufficient evidence for new round
        state["insufficient_evidence"] = False
            
        return state

    def _fallback_plan(self, state: SearchState):
        """Deterministic fallback planner to keep system operational."""
        query_lower = state['original_query'].lower()
        
        if any(w in query_lower for w in ["compare", "difference", "vs", "versus"]):
            state["reasoning_required"] = True
            state["verification_required"] = True
            state["max_sources"] = settings.MAX_VERIFICATION_SOURCES
        elif any(w in query_lower for w in ["latest", "today", "current", "recent"]):
            state["freshness_required"] = True
            state["verification_required"] = True
            state["max_sources"] = settings.MAX_VERIFICATION_SOURCES
        elif any(w in query_lower for w in ["why", "how", "explain"]):
            state["reasoning_required"] = True
            state["verification_required"] = True
            state["max_sources"] = settings.MAX_VERIFICATION_SOURCES
        else:
            state["reasoning_required"] = False
            state["verification_required"] = True
            state["max_sources"] = 3
            
        state["sub_queries"] = [state['original_query']]
        state["search_modes"] = ["hybrid"]
        state["freshness_required"] = state.get("freshness_required", False)
