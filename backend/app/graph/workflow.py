import logging
from typing import Dict, Any, Callable
from langgraph.graph import StateGraph, END
from app.graph.state import SearchState

from app.llm.base import LLMProvider
from app.llm.mock import MockLLMProvider
from app.agents.planner import PlannerAgent
from app.agents.retrieval import RetrievalAgent
from app.agents.security import SecurityGateAgent
from app.agents.selection import SourceSelectionAgent
from app.agents.verification import VerificationAgent
from app.agents.evidence import EvidenceAggregationAgent
from app.agents.conflict import ConflictDetectionAgent
from app.agents.reasoning import ReasoningAgent
from app.agents.answer import AnswerGenerationAgent
from app.agents.citation_validation import CitationValidationAgent
from app.core.config import settings

logger = logging.getLogger(__name__)

class AgenticSearchWorkflow:
    def __init__(self, llm_provider: LLMProvider = None):
        self.llm = llm_provider or self._initialize_llm()
        
        # Initialize Agents
        self.planner = PlannerAgent(self.llm)
        self.retrieval = RetrievalAgent()
        self.security_gate = SecurityGateAgent()
        self.source_selector = SourceSelectionAgent()
        self.verifier = VerificationAgent(self.llm)
        self.aggregator = EvidenceAggregationAgent(self.llm)
        self.conflict_detector = ConflictDetectionAgent(self.llm)
        self.reasoner = ReasoningAgent(self.llm)
        self.answer_generator = AnswerGenerationAgent(self.llm)
        self.citation_validator = CitationValidationAgent()
        
        self.graph = self._build_graph()
        
    def _initialize_llm(self) -> LLMProvider:
        # We use MockLLMProvider by default per requirements
        provider_name = getattr(settings, "LLM_PROVIDER", "mock").lower()
        if provider_name == "mock":
            logger.info("Using MockLLMProvider for offline execution.")
            return MockLLMProvider()
        else:
            # Here you would initialize OpenAI/Anthropic based on config.
            # But the requirement says keep it mocked unless a real provider is fully implemented.
            logger.warning(f"Provider '{provider_name}' not fully implemented, falling back to MockLLMProvider.")
            return MockLLMProvider()

    def _build_graph(self):
        workflow = StateGraph(SearchState)
        
        # Add Nodes
        workflow.add_node("planner", self.planner.plan)
        workflow.add_node("retrieval", self.retrieval.retrieve)
        workflow.add_node("security_gate", self.security_gate.filter_results)
        workflow.add_node("source_selection", self.source_selector.select_sources)
        workflow.add_node("verification", self.verifier.verify_sources)
        workflow.add_node("evidence_aggregation", self.aggregator.aggregate)
        workflow.add_node("conflict_detection", self.conflict_detector.detect)
        workflow.add_node("reasoning", self.reasoner.reason)
        workflow.add_node("answer_generation", self.answer_generator.generate_answer)
        workflow.add_node("citation_validation", self.citation_validator.validate)
        
        # Add Edges
        workflow.set_entry_point("planner")
        workflow.add_edge("planner", "retrieval")
        workflow.add_edge("retrieval", "security_gate")
        workflow.add_edge("security_gate", "source_selection")
        workflow.add_edge("source_selection", "verification")
        
        # Conditional branching after verification
        def check_evidence(state: SearchState) -> str:
            if state.get("insufficient_evidence", False):
                if state.get("iteration_count", 1) < getattr(settings, "MAX_RETRIEVAL_ROUNDS", 2):
                    return "planner"
                else:
                    return "answer_generation"
            return "evidence_aggregation"
            
        workflow.add_conditional_edges(
            "verification",
            check_evidence,
            {
                "planner": "planner",
                "answer_generation": "answer_generation",
                "evidence_aggregation": "evidence_aggregation"
            }
        )
        
        workflow.add_edge("evidence_aggregation", "conflict_detection")
        workflow.add_edge("conflict_detection", "reasoning")
        workflow.add_edge("reasoning", "answer_generation")
        workflow.add_edge("answer_generation", "citation_validation")
        workflow.add_edge("citation_validation", END)
        
        return workflow.compile()
        
    def run(self, query: str) -> Dict[str, Any]:
        """
        Executes the agentic search workflow for a given query.
        """
        initial_state = {
            "original_query": query,
            "normalized_query": query.lower().strip(),
            "sub_queries": [],
            "search_modes": [],
            "verification_required": True,
            "max_sources": settings.MAX_VERIFICATION_SOURCES,
            "reasoning_required": False,
            "freshness_required": False,
            "retrieval_results": [],
            "trusted_results": [],
            "security_filtered_results": [],
            "selected_sources": [],
            "verification_results": [],
            "evidence": [],
            "conflicts": [],
            "reasoning": None,
            "answer": "",
            "citations": [],
            "confidence": 0,
            "trust_summary": {},
            "warnings": [],
            "errors": [],
            "execution_trace": [],
            "insufficient_evidence": False,
            "iteration_count": 0
        }
        
        try:
            final_state = self.graph.invoke(initial_state)
            return final_state
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            initial_state["errors"].append(str(e))
            initial_state["answer"] = "An internal error occurred during agent execution."
            return initial_state
