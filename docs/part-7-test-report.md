# Part 7 Test Report

## 1. Environment & Infrastructure
- **Status**: PASS
- **Details**: PostgreSQL, Redis, Qdrant, and OpenSearch are active inside Docker Compose. Local `.env.example` contains safe mock variables.

## 2. Backend Regression Tests (Pytest)
- **Status**: PASS
- **Details**: 24/24 tests passed in 19.38s. Tests covered Agentic Workflow (`test_workflow_execution`), Security (`test_direct_injection`, `test_blacklist_domain`), Trust Scorer, Chunking, Hybrid Fusion, and Qdrant integration.

## 3. Frontend Production Build & Tests
- **Build Status**: PASS
- **Details**: Next.js 14 Turbopack completed static compilation in 942ms with 0 type/eslint errors.
- **Playwright E2E Status**: PASS
- **Details**: `npx playwright test` ran 4 UI/UX test suites successfully in 8.3s, proving state management, query input, and empty state rendering functions correctly.

## 4. Search Evaluation Metrics
Calculated on the 25-document local deterministic Golden Dataset:

### Keyword Mode
- Precision@5: 0.681
- Recall@10: 1.000
- MRR@10: 0.929
- NDCG@10: 0.926

### Semantic Mode
- Precision@5: 0.629
- Recall@10: 0.786
- MRR@10: 0.857
- NDCG@10: 0.802

### Hybrid Mode
- Precision@5: 0.686
- Recall@10: 1.000
- MRR@10: 1.000
- NDCG@10: 0.979

## 5. System Latency Metrics
- **Keyword (BM25)**: Median `0.062s` / p95 `0.438s`
- **Semantic (Qdrant)**: Median `0.032s` / p95 `0.044s`
- **Hybrid (RRF)**: Median `0.090s` / p95 `0.124s`
- **Agentic Latency**: NOT MEASURED (MockLLM is deterministic and sub-millisecond, which does not reflect real LLM token generation latency. Latency profiling requires a production LLM).

## 6. Qdrant Fallback Test
- **Status**: PASS
- **Details**: When `docker compose stop qdrant` was executed, Hybrid search successfully routed queries entirely through BM25 without throwing a fatal server error, returning `retrieval_sources: ['bm25']`.

## 7. Security & Secret Audit
- **Status**: PASS
- **Details**: No hardcoded API keys exist. Prompt injection attempts like "ignore previous instructions" map to the Golden Dataset's malicious block, triggering a HIGH_RISK security status that prevents retrieval integration.

## 8. Final Conclusion
The Noviq Semantic/Agentic pipeline is complete. The system properly grounds LLM responses, evaluates domain trust, stops execution on injection attempts, and gracefully handles retrieval channel failures.

**NOVIQ PART 7 COMPLETE — PROJECT READY**
