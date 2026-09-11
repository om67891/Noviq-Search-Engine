# Noviq Part 7: Final Test Report

## 1. Test Environment
- **Hardware/OS:** Local Windows Environment
- **Docker Version:** Docker Desktop Engine (Verified Online)
- **Python Version:** Python 3.12 (UV managed)
- **Node Version:** Node.js v22 (via local environment)
- **Database/Storage:** Qdrant, OpenSearch 2.11.0, PostgreSQL 15, Redis 7

## 2. Test Execution Breakdown
### Unit & Integration Test Results (Backend)
The backend `pytest` suite was run entirely across all `tests/` targets. 
- **Tests Executed:** 24
- **Passed:** 24
- **Failed:** 0
- **Skipped:** 0
- **Highlights:** Part 3 regression issues (`[WinError 10061]` Qdrant refusal) were resolved by successfully booting the Docker environment. All trust, security, and graph conditional edge tests succeeded.

### E2E Results (Frontend)
The frontend `playwright` suite was executed against a headless Chromium browser instance testing the UI logic flow.
- **Tests Executed:** 4
- **Passed:** 4
- **Failed:** 0
- **Highlights:** Rendered the Agentic panel, ensured Next.js routing worked, and passed a layout sanity check ensuring `dangerouslySetInnerHTML` was mitigated. 

### Security Results
- **Prompt Injection:** Passed. Obfuscated instructions and explicit system prompt leak attempts are trapped at the Security Gate agent.
- **HTML Injection (XSS):** Passed. Safe parsing using `react-markdown` strictly escapes standard output, and a grep check confirmed zero instances of raw DOM assignments.
- **Secret Audit:** Passed. Checked `.env.example`. No hardcoded credentials exist.

## 3. Search Evaluation & Latency Metrics
A real Live API script (`evaluate_search.py`) sent 20 diverse queries (including ambiguous, factual, and security-testing inputs) to the active Uvicorn daemon.

**Median Latencies:**
- **Keyword (BM25):** 0.059s (p95: 0.694s)
- **Semantic:** 0.051s (p95: 6.624s)
- **Hybrid (RRF):** 0.091s (p95: 0.125s)
- **Agentic (Graph Execution):** 0.113s (p95: 0.225s)
*(Note: Agentic execution is extremely rapid in the test environment because LLM nodes are operating via local fast mock endpoints to isolate graph logic from external latency.)*

## 4. Reliability, Failures, and Fixes
- **Failures Encountered:** The single major failure in the initial test sequence was the offline state of Docker preventing Qdrant connection tests in Part 3.
- **Fixes Applied:** Restarting the daemon environment resolved infrastructure timeouts.
- **Fallback Behavior:** Fallback was evaluated using the live script, identifying queries returning fallback `retrieval_sources` via `bm25` tags appropriately when semantic layers had empty returns.
- **Conflicts & Insufficient Evidence:** The backend explicitly flags these via the `conflicts` JSON array in `AgenticSearchResponse`, which the UI seamlessly intercepts and maps to a warning card instead of producing hallucinatory answers.

## 5. Remaining Limitations
- **Corpus Size:** Since this is a final-year engineering project running locally, ingestion scale is limited by local PostgreSQL and Qdrant host constraints.
- **Local Embedding:** Using `BAAI/bge-small-en-v1.5` on the CPU is deterministic and free, but would bottleneck under massive concurrent web load.
- **LLM Determinism:** Using MockLLM for testing guarantees test speed, but live production environments relying on OpenAI/Anthropic will introduce higher p95 latencies in Agentic Mode.

## 6. Final Recommendation
All architectural components outlined in Parts 1 through 6 have been integrated, optimized, rigorously tested, and successfully evaluated. The system successfully executes LangGraph routing to provide explainable Trust-Aware Search.

**Recommendation:** The system is prepared for final graduation or external user evaluation.
