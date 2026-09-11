import pytest
from app.retrieval.hybrid_search import HybridSearchEngine
from app.embeddings.service import EmbeddingService
from app.retrieval.qdrant_client import QdrantStore
import time

def test_embedding_service():
    """Verify BGE embedding model works."""
    service = EmbeddingService()
    
    # Test text embedding
    text_vec = service.embed_text("machine learning is a branch of artificial intelligence")
    assert len(text_vec) == 384, "Text embedding dimension should be 384"
    assert all(isinstance(x, float) for x in text_vec), "Embedding should be numeric"
    
    # Test query embedding
    query_vec = service.embed_query("what is machine learning")
    assert len(query_vec) == 384, "Query embedding dimension should be 384"

def test_qdrant_integration():
    """Verify Qdrant operations."""
    store = QdrantStore()
    assert store.client is not None, "Qdrant client should be initialized"
    assert store.client.collection_exists(store.collection_name), "Collection should exist"

def test_chunking():
    """Verify deterministic chunking."""
    from app.retrieval.chunker import TextChunker
    chunker = TextChunker(chunk_size=10, overlap=5)
    
    text = "one two three four five six seven eight nine ten eleven twelve thirteen"
    chunks = chunker.chunk_text(text, {"page_id": "test-1"})
    
    assert len(chunks) == 2, "Should produce exactly 2 chunks"
    assert chunks[0]["chunk_id"] == "test-1-0"
    assert chunks[1]["chunk_id"] == "test-1-1"

def test_hybrid_fallback(monkeypatch):
    """Verify hybrid search falls back to BM25 when Qdrant fails."""
    engine = HybridSearchEngine()
    
    # Mock Qdrant client search to raise Exception
    def mock_qdrant_search(*args, **kwargs):
        raise Exception("Simulated Qdrant failure")
        
    monkeypatch.setattr(engine.qdrant_client, "search", mock_qdrant_search)
    
    # This should not crash, it should return BM25 results only
    results = engine.search_hybrid("test query", limit=10)
    assert "results" in results, "Should return results dictionary even if Qdrant fails"

# Pytest configuration to allow running this file directly if needed
if __name__ == "__main__":
    pytest.main(["-v", __file__])
