import pytest
from app.graph.workflow import AgenticSearchWorkflow
from app.llm.mock import MockLLMProvider

def test_workflow_execution():
    """
    Tests the full LangGraph execution using MockLLMProvider
    to ensure state flows through without exceptions.
    """
    workflow = AgenticSearchWorkflow(llm_provider=MockLLMProvider())
    
    # Run a simple query (will trigger Hybrid retrieval inherently)
    # The Mock LLM won't actually hit external DBs unless the retrieval agent does.
    # To truly mock it, we let the retrieval agent try. If DB isn't up, it fails gracefully.
    
    res = workflow.run("compare RAG and fine-tuning")
    
    assert "answer" in res
    assert "citations" in res
    assert "planner" in res["execution_trace"]
    
    # We should have a fallback answer if the DB wasn't up, 
    # but the graph should still execute END-TO-END without unhandled exceptions.
    assert isinstance(res["confidence"], int)
