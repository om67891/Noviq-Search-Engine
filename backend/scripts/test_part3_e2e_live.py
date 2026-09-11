import asyncio
from typing import List, Dict
import random

from app.retrieval.chunker import TextChunker
from app.embeddings.service import EmbeddingService
from app.retrieval.qdrant_client import QdrantStore
from app.retrieval.hybrid_search import HybridSearchEngine
from app.services.search.opensearch_client import OpenSearchClient
import uuid

# Dummy corpus for testing
CORPUS = [
    {
        "url": "https://example.com/ai/intro",
        "title": "Introduction to Artificial Intelligence",
        "domain": "example.com",
        "text": "Artificial intelligence is a branch of computer science that aims to create intelligent machines. It encompasses subfields like machine learning, neural networks, and deep learning. AI systems learn patterns from examples." * 10
    },
    {
        "url": "https://example.com/ml/basics",
        "title": "Machine Learning Basics",
        "domain": "example.com",
        "text": "Machine learning is the study of computer algorithms that can improve automatically through experience and by the use of data. Training models requires data preparation and feature engineering." * 10
    },
    {
        "url": "https://example.com/security/rag",
        "title": "Security in RAG Systems",
        "domain": "example.com",
        "text": "Retrieval Augmented Generation (RAG) systems can be vulnerable to prompt injection and data poisoning. Security filtering is required before semantic search results are sent to the LLM." * 10
    },
    {
        "url": "https://example.com/search/hybrid",
        "title": "Hybrid Search Architectures",
        "domain": "example.com",
        "text": "Hybrid search combines lexical keyword search like BM25 with semantic vector search. RRF (Reciprocal Rank Fusion) is often used to merge the results and provide the best of both worlds." * 10
    },
    {
        "url": "https://example.com/test/page",
        "title": "A Test Page",
        "domain": "example.com",
        "text": "This is just a simple test page with very little content to see how the system handles short documents."
    }
]

async def ingest_corpus():
    print("Initializing services...")
    chunker = TextChunker(chunk_size=50, overlap=10)
    embedding_service = EmbeddingService()
    qdrant = QdrantStore()
    opensearch = OpenSearchClient()

    print("Cleaning old data...")
    # Attempt to clean opensearch and qdrant for a fresh start if possible
    # We will just insert them, Qdrant delete_by_page_id will clean stale chunks
    
    total_chunks = 0
    total_vectors = 0
    
    start_time = asyncio.get_event_loop().time()
    
    for i, page in enumerate(CORPUS):
        page_id = f"page-{i+1}"
        print(f"Processing page: {page['title']}")
        
        # 1. Clean stale vectors
        qdrant.delete_by_page_id(page_id)
        
        # 2. OpenSearch insertion
        # Mock index document method since opensearch_client might not have a public method yet
        # We will directly use opensearch client if it has one
        try:
            opensearch.client.index(
                index=opensearch.index_name,
                id=page_id,
                body={
                    "id": page_id,
                    "url": page["url"],
                    "domain": page["domain"],
                    "title": page["title"],
                    "text": page["text"]
                },
                refresh=True
            )
        except Exception as e:
            print(f"Failed to index in OpenSearch: {e}")

        # 3. Chunking
        metadata = {
            "page_id": page_id,
            "url": page["url"],
            "title": page["title"],
            "domain": page["domain"]
        }
        chunks = chunker.chunk_text(page["text"], metadata)
        total_chunks += len(chunks)
        
        # 4. Embeddings
        chunk_texts = [c["text"] for c in chunks]
        embeddings = embedding_service.embed_documents(chunk_texts)
        total_vectors += len(embeddings)
        
        # 5. Qdrant Upsert
        success = qdrant.upsert_chunks(chunks, embeddings)
        if not success:
            print(f"Failed to upsert chunks for {page_id}")
            
    end_time = asyncio.get_event_loop().time()
    print(f"\nIngestion Complete in {end_time - start_time:.2f}s")
    print(f"Total Pages: {len(CORPUS)}")
    print(f"Total Chunks: {total_chunks}")
    print(f"Total Vectors: {total_vectors}")
    print(f"Average Chunks/Page: {total_chunks / len(CORPUS):.1f}")
    
async def test_search():
    engine = HybridSearchEngine()
    
    queries = [
        "machine learning algorithms",
        "how does artificial intelligence learn from data?",
        "security risks in retrieval augmented generation",
        "hybrid search rrf",
        "simple test page"
    ]
    
    print("\n--- Search Testing ---")
    for q in queries:
        print(f"\nQuery: '{q}'")
        
        # Keyword
        t0 = asyncio.get_event_loop().time()
        bm25_res = engine.search_keyword(q, limit=3)
        t1 = asyncio.get_event_loop().time()
        print(f"  BM25 ({t1-t0:.3f}s): {bm25_res['total']} results")
        for r in bm25_res.get("results", []):
            print(f"    - {r.get('title')} (score: {r.get('score')})")
            
        # Semantic
        t0 = asyncio.get_event_loop().time()
        sem_res = engine.search_semantic(q, limit=3)
        t1 = asyncio.get_event_loop().time()
        print(f"  Semantic ({t1-t0:.3f}s): {sem_res['total']} results")
        for r in sem_res.get("results", []):
            print(f"    - {r.get('title')} (score: {r.get('score')})")
            
        # Hybrid
        t0 = asyncio.get_event_loop().time()
        hyb_res = engine.search_hybrid(q, limit=3)
        t1 = asyncio.get_event_loop().time()
        print(f"  Hybrid ({t1-t0:.3f}s): {hyb_res['total']} results")
        for r in hyb_res.get("results", []):
            print(f"    - {r.get('title')} (score: {r.get('score')}) [sources: {r.get('retrieval_sources')}]")

if __name__ == "__main__":
    asyncio.run(ingest_corpus())
    asyncio.run(test_search())
