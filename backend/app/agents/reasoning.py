import logging
from pydantic import BaseModel, Field
from app.graph.state import SearchState
from app.llm.base import LLMProvider

logger = logging.getLogger(__name__)

class ReasoningSummary(BaseModel):
    reasoning_summary: str = Field(description="Concise reasoning conclusion without exposing hidden chain of thought.")

class ReasoningAgent:
    def __init__(self, llm: LLMProvider):
        self.llm = llm
        
    def reason(self, state: SearchState) -> SearchState:
        """
        Processes evidence and conflicts to produce a logical summary.
        """
        state["execution_trace"].append("reasoning")
        
        if state.get("insufficient_evidence"):
            state["reasoning"] = "Insufficient evidence to perform reasoning."
            return state
            
        evidence = state.get("evidence", [])
        conflicts = state.get("conflicts", [])
        
        evidence_text = "\n".join([f"- [Source {e['source_id']}] {e['claim']} ({e['support_level']} support)" for e in evidence])
        conflict_text = "\n".join([c["details"] for c in conflicts]) if conflicts else "No conflicts detected."
        
        prompt = f"""
        Synthesize the following evidence and conflict information into a brief, logical reasoning summary.
        Do not expose your internal chain of thought.
        
        EVIDENCE:
        {evidence_text}
        
        CONFLICTS:
        {conflict_text}
        """
        
        try:
            res = self.llm.generate_structured(
                prompt=prompt,
                output_schema=ReasoningSummary,
                system_prompt="You are a Reasoning Agent. Provide a concise, evidence-based rationale."
            )
            state["reasoning"] = res.reasoning_summary
        except Exception as e:
            logger.error(f"Reasoning failed: {e}")
            state["warnings"].append("Reasoning phase failed.")
            state["reasoning"] = None
            
        return state
