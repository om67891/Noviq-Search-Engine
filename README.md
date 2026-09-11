# Noviq — SecureAgent Search

> **Search. Verify. Discover.**

Noviq is a final-year engineering research project representing a state-of-the-art **Trust-Aware Multi-Agent AI Search Engine**. Built to tackle the critical challenges of "Black Box AI", Hallucinations, and Prompt Injections, Noviq provides a deterministic, highly transparent, and secure search pipeline that verifies evidence before generating answers.

## Key Features

- **Multi-Agent Orchestration**: LangGraph-powered dynamic workflow routing consisting of Planners, Retrieval Agents, Source Verification, Evidence Aggregators, and Conflict Detectors.
- **Explainability & Transparency**: Answers are returned alongside verifiable Trust metrics, Conflict detection logs, Confidence bounds, and a complete Execution Trace visible in the Next.js frontend. 
- **Security & Prompt Injection Defense**: Web context is strictly treated as UNTRUSTED DATA. Security gates analyze sources and strip adversarial injections before they can enter the LLM reasoning context.
- **Trust-Aware Ranking**: Domain authorities, `HTTPS` status, `gov/edu` TLDs, and recency heuristically boost results, ensuring higher-quality evidence wins out.
- **Hybrid Retrieval Fallback**: Queries evaluate via vector embeddings (`BAAI/bge-small-en-v1.5`) mapped to a **Qdrant** collection, fused via RRF with **OpenSearch** BM25 Keyword algorithms to guarantee fallback resilience.

## Architecture & Technology Stack

**Frontend**
- Next.js (React 19)
- Tailwind CSS v4
- Playwright E2E Testing
- `react-markdown` (Safe output rendering)

**Backend**
- Python 3.12 (FastAPI)
- LangGraph (Agentic Workflow orchestration)
- Qdrant (Vector Database)
- OpenSearch (BM25 Indexing)
- PostgreSQL (Source Metadata)
- Redis (Session Caching)

## Getting Started

### 1. Requirements
- Docker & Docker Compose
- Node.js (v20+)
- Python 3.12+ (uv or standard venv)

### 2. Infrastructure Setup
Boot up the critical local infrastructure components.
```bash
docker compose up -d
```
*(This starts PostgreSQL, Qdrant, OpenSearch, and Redis on your local machine)*

### 3. Backend Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --port 8000
```

### 4. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

Navigate to `http://localhost:3000` to begin interacting with the Noviq Engine.

## Search Modes
Noviq natively supports 4 distinct modes selectable in the UI:
1. **Keyword**: Raw BM25 algorithm execution against the OpenSearch index.
2. **Semantic**: Vector proximity search utilizing local embeddings.
3. **Hybrid**: RRF-fused list combining Semantic context meaning and Keyword strict matching.
4. **Agentic**: Kicks off the multi-agent asynchronous pipeline. This evaluates trust, maps contradictions, generates safe citations, and prevents hallucination.

## Evaluation & Testing Methodology
The Noviq project has been fully audited against a structured 30-phase End-to-End matrix (available in `/docs`).
- **Regression:** 24/24 `pytest` scenarios targeting LangGraph nodes and API boundaries.
- **Frontend E2E:** `Playwright` automated suite evaluating mode selections, loading states, and HTML injection prevention.
- **Quality Evaluation:** Precision/Recall evaluation against a diverse mock dataset simulating ambiguous, factual, and security-testing queries.

## Known Limitations & Future Work
- **Local Embedding Scaling:** Current execution utilizes CPU bounding for local vectors. Migrating to GPU-bound embeddings would drastically improve scale times.
- **Corpus Ingestion:** Real live ingestion using Common Crawl is constrained by disk and memory without cloud-scale deployment infrastructure.
- **Deterministic Evaluation:** Current speed tests simulate large LLM generation by utilizing MockLLMs; utilizing GPT-4 or Claude 3.5 in production will result in inherently slower agentic response loops.
