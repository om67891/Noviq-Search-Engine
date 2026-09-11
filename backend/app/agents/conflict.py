import logging
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from app.graph.state import SearchState
from app.llm.base import LLMProvider

logger = logging.getLogger(__name__)

class ConflictResult(BaseModel):
    conflict_detected: bool
    conflict_details: Optional[str] = Field(description="Explanation of the conflict if detected.")

class ConflictDetectionAgent:
    def __init__(self, llm: LLMProvider):
        self.llm = llm
        
    def detect(self, state: SearchState) -> SearchState:
        """
        Analyzes evidence to detect contradictions between sources.
        """
        state["execution_trace"].append("conflict_detection")
        
        evidence = state.get("evidence", [])
        if len(evidence) < 2:
            # Cannot have conflicts if less than 2 pieces of evidence
            state["conflicts"] = []
            return state
            
        evidence_text = "\n".join([f"- [Source {e['source_id']}] Claim: {e['claim']}" for e in evidence])
        
        prompt = f"""
        Review the following evidence claims for any direct factual contradictions or conflicts.
        
        EVIDENCE:
        {evidence_text}
        
        Determine if there is a conflict.
        """
        
        try:
            res = self.llm.generate_structured(
                prompt=prompt,
                output_schema=ConflictResult,
                system_prompt="You are a Conflict Detection Agent. You look for contradictions."
            )
            
            if res.conflict_detected:
                state["conflicts"] = [{"details": res.conflict_details}]
            else:
                state["conflicts"] = []
                
        except Exception as e:
            logger.error(f"Conflict detection failed: {e}")
            state["warnings"].append("Conflict detection step failed.")
            state["conflicts"] = []
            
        return state
