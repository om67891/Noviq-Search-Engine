import pytest
from app.graph.state import SearchState
from app.llm.mock import MockLLMProvider
from app.agents.planner import PlannerAgent
from app.agents.security import SecurityGateAgent
from app.agents.selection import SourceSelectionAgent
from app.agents.verification import VerificationAgent
from app.agents.evidence import EvidenceAggregationAgent
from app.agents.conflict import ConflictDetectionAgent
from app.agents.reasoning import ReasoningAgent
from app.agents.answer import AnswerGenerationAgent
from app.agents.citation_validation import CitationValidationAgent

@pytest.fixture
def llm():
    return MockLLMProvider()

@pytest.fixture
def base_state() -> SearchState:
    return {
        "original_query": "test query",
        "normalized_query": "test query",
        "sub_queries": [],
        "search_modes": [],
        "verification_required": True,
        "max_sources": 3,
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

def test_planner_agent(llm, base_state):
    planner = PlannerAgent(llm)
    base_state["original_query"] = "compare X and Y"
    
    new_state = planner.plan(base_state)
    assert new_state["reasoning_required"] is True
    assert new_state["max_sources"] == 3
    assert "planner" in new_state["execution_trace"]

def test_security_gate_agent(base_state):
    gate = SecurityGateAgent()
    base_state["retrieval_results"] = [
        {"url": "safe.com", "security_status": "SAFE"},
        {"url": "bad.com", "security_status": "HIGH_RISK"}
    ]
    
    new_state = gate.filter_results(base_state)
    assert len(new_state["security_filtered_results"]) == 1
    assert new_state["security_filtered_results"][0]["url"] == "safe.com"
    assert len(new_state["warnings"]) == 1

def test_source_selection_agent(base_state):
    selector = SourceSelectionAgent()
    base_state["security_filtered_results"] = [
        {"url": "a.com", "domain": "a.com"},
        {"url": "a.com/2", "domain": "a.com"},
        {"url": "a.com/3", "domain": "a.com"}, # Should be skipped due to diversity limit of 2
        {"url": "b.com", "domain": "b.com"}
    ]
    
    new_state = selector.select_sources(base_state)
    assert len(new_state["selected_sources"]) == 3
    
def test_conflict_detection(llm, base_state):
    detector = ConflictDetectionAgent(llm)
    base_state["evidence"] = [
        {"claim": "Cost is 100", "source_id": "1", "url": "a.com", "support_level": "strong", "evidence_text": "", "confidence": 90},
        {"claim": "Cost is 120", "source_id": "2", "url": "b.com", "support_level": "strong", "evidence_text": "", "confidence": 90}
    ]
    
    new_state = detector.detect(base_state)
    assert len(new_state["conflicts"]) == 1
    assert "100" in new_state["conflicts"][0]["details"]

def test_citation_validation(base_state):
    validator = CitationValidationAgent()
    base_state["selected_sources"] = [{"url": "a.com", "id": "1"}]
    base_state["citations"] = [
        {"citation_id": "S1", "source_id": "1", "url": "a.com", "title": "A"},
        {"citation_id": "S2", "source_id": "99", "url": "fake.com", "title": "Fake"}
    ]
    
    new_state = validator.validate(base_state)
    assert len(new_state["citations"]) == 1
    assert new_state["citations"][0]["url"] == "a.com"
    assert len(new_state["warnings"]) == 1
