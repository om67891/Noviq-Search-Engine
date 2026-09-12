# Noviq — SecureAgent Search

> **Search. Verify. Discover.**

Noviq is a Trust-Aware Multi-Agent AI Search Engine with Explainable Retrieval, RRF Hybrid Search, and Prompt Injection Defense.

## Overview
Noviq merges traditional Keyword BM25 retrieval with Semantic Dense Vector retrieval, governed by an Agentic safety graph. Rather than generating answers unconditionally, Noviq strictly audits the retrieval provenance, evaluates domain trust, and checks for conflicting evidence before yielding a response.

## Current Architecture
- **Frontend**: Next.js 14, TailwindCSS, React Markdown.
- **Backend API**: FastAPI.
- **Lexical Retrieval**: OpenSearch (BM25).
- **Semantic Retrieval**: Qdrant (BAAI/bge-small-en-v1.5 384-dimensional vectors).
- **Fusion**: Reciprocal Rank Fusion (RRF, k=60).
- **Database**: PostgreSQL (Metadata & Ingestion Tracking).
- **Agentic Layer**: LangGraph.
- **LLM Engine**: MockLLM (Deterministic for local evaluation/testing).

## Features
- **Semantic Relevance Gating**: Hard-enforced cosine similarity thresholds (0.65) to prevent noisy generation.
- **Hybrid RRF Fusion**: Merges keyword and vector scores gracefully with fallback mechanics.
- **Security Gate**: Analyzes retrieval text for Prompt Injection attacks and excludes malicious payload sources.
- **Trust-Aware Ranking**: Sources are scored via HTTPS, TLD, Citation signals, and Freshness.
- **Agentic Insufficient Evidence**: The Agent explicitly halts and explains when local corpora lack sufficient evidence, preventing hallucination.
- **Deterministic Evaluation**: Ships with a 25-document Golden Dataset for mathematically rigorous Precision, Recall, MRR, and NDCG calculations.

## Run Noviq Locally

### 1. Start Infrastructure
```bash
docker compose up -d
```
Starts PostgreSQL, OpenSearch, Qdrant, and Redis.

### 2. Configure Environment
Copy `.env.example` to `.env`. Noviq runs entirely locally by default without requiring external API keys.

### 3. Run Backend (Uvicorn)
```bash
cd backend
python -m uvicorn app.main:app --port 8000
```

### 4. Run Frontend (Next.js)
```bash
cd frontend
npm install
npm run dev
```

### 5. Run Evaluation
```bash
cd backend
python scripts/seed_golden_dataset.py
python scripts/evaluate_search.py
```

## Disclaimer / Known Limitations
- The current system is tuned for a local deterministic synthetic corpus. It does not perform active real-time internet scraping in this baseline mode.
- MockLLM is active to avoid token costs during local CI/CD testing. To use OpenAI/Anthropic, override `LLM_PROVIDER` in your `.env`.
- Semantic Thresholds (0.65) are optimized for `bge-small-en-v1.5` on English texts.
