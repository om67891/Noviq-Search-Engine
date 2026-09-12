# Noviq Technical Walkthrough

## The Final Flow

When a user submits a query to Noviq, the following sequence perfectly outlines the technical lifecycle of the request:

1. **User Query**: The query string is submitted through the Next.js frontend to the FastAPI `/api/v1/agentic-search/` endpoint.
2. **Planner**: The LangGraph engine spins up the `planner_agent`, which assesses the query and decides if standard retrieval is sufficient or if multi-step verification is required.
3. **Query Decomposition**: Complex queries are split into discrete searchable sub-components.
4. **Hybrid Retrieval**: Queries are sent to the `HybridSearchEngine`. 
   - OpenSearch (BM25) looks for keyword exact matches.
   - Qdrant looks for dense vector semantic similarity using `bge-small-en-v1.5`.
   - The results are fused using **Reciprocal Rank Fusion (RRF)**.
5. **Relevance Gate**: Qdrant strictly enforces a `SEMANTIC_SCORE_THRESHOLD=0.65` to block distantly related neighbor vectors from polluting the response.
6. **Security Gate**: Retrieved candidates are scanned for prompt injection attacks or explicit blocklist terms (e.g. "ignore previous instructions").
7. **Trust / Source Selection**: The `TrustScorer` assesses the remaining clean candidates based on heuristics (like `.gov/.edu` TLDs and simulated HTTPS).
8. **Verification & Conflict Detection**: The agentic graph checks for conflicting facts between sources. 
9. **Evidence Aggregation**: Clean, relevant, safe, and trusted evidence is combined.
10. **Reasoning & Answer Generation**: The LLM Engine formulates a cohesive markdown answer grounded *strictly* in the provided evidence.
11. **Citation Validation**: If the LLM generates `[1]`, the graph verifies that source `[1]` was part of the retrieved candidate list.
12. **Final Safety Check**: Output formatting ensures markdown is safe to render on the client.
13. **Noviq UI**: The Next.js client renders the response, alongside provenance badges (Keyword/Semantic/Hybrid) and Conflict Warnings if present.

## Note on Implementation Capabilities
The current baseline uses a **local deterministic synthetic corpus** comprising 25 documents across 5 topics. It uses **MockLLM** to evaluate workflow correctness deterministically without invoking network latency or API costs. Live web scraping and real LLM integration are designed capabilities, but are disabled in this evaluation baseline.
