import pytest
from app.retrieval.fusion import ReciprocalRankFusion

def test_rrf_fusion():
    bm25 = [
        {"id": "doc1", "score": 20.0, "snippet": "hello"},
        {"id": "doc2", "score": 15.0, "snippet": "world"},
        {"id": "doc3", "score": 10.0, "snippet": "foo"}
    ]
    
    vector = [
        {"id": "doc2", "score": 0.8, "snippet": "world vector"}, # Should update snippet
        {"id": "doc4", "score": 0.7, "snippet": "bar"},
        {"id": "doc1", "score": 0.6, "snippet": "hello"}
    ]
    
    fusion = ReciprocalRankFusion(k=1)
    
    # rank bm25: doc1=1, doc2=2, doc3=3
    # rrf bm25: doc1=1/2, doc2=1/3, doc3=1/4
    
    # rank vector: doc2=1, doc4=2, doc1=3
    # rrf vector: doc2=1/2, doc4=1/3, doc1=1/4
    
    # final rrf:
    # doc1: 1/2 + 1/4 = 0.75
    # doc2: 1/3 + 1/2 = 0.833
    # doc3: 1/4 = 0.25
    # doc4: 1/3 = 0.333
    
    # ordering should be: doc2, doc1, doc4, doc3
    results = fusion.fuse(bm25, vector)
    
    assert len(results) == 4
    assert results[0]["id"] == "doc2"
    assert results[1]["id"] == "doc1"
    assert results[2]["id"] == "doc4"
    assert results[3]["id"] == "doc3"
    
    # Check if retrieval sources were merged properly
    assert "bm25" in results[0]["retrieval_sources"]
    assert "vector" in results[0]["retrieval_sources"]
    assert "bm25" not in results[2]["retrieval_sources"]
    assert "vector" in results[2]["retrieval_sources"]
    
    # Check snippet update logic (longer snippet preferred)
    assert results[0]["snippet"] == "world vector"
