import asyncio
import httpx
import time
import statistics
import json

# Golden queries and their expected relevant URLs (from our seed dataset)
EVAL_QUERIES = {
    "ronaldo": ["https://sports.example.com/ronaldo-career", "https://blog.football-fans.net/best-strikers", "https://sports.example.com/champions-league-history"],
    "machine learning": ["https://tech.example.edu/machine-learning-basics", "https://security.example.gov/data-poisoning"],
    "prompt injection": ["https://security.example.gov/prompt-injection"],
    "quantum computing": ["https://science.example.edu/quantum-computing", "https://science.example.edu/shors-algorithm"],
    "xyzrandom123456": [],
    "the history of the universe": ["https://science.example.edu/dark-matter", "https://space.example.gov/james-webb"],
    "docker kubernetes cloud": ["https://tech-news.example.com/cloud-native", "https://tech-news.example.com/docker-containers"]
}

MODES = ["keyword", "semantic", "hybrid"]

def calculate_precision_at_k(retrieved_urls, expected_urls, k):
    if not expected_urls:
        return 1.0 if not retrieved_urls else 0.0
    retrieved_k = retrieved_urls[:k]
    if not retrieved_k:
        return 0.0
    relevant = sum(1 for url in retrieved_k if url in expected_urls)
    return relevant / len(retrieved_k)

def calculate_recall_at_k(retrieved_urls, expected_urls, k):
    if not expected_urls:
        return 1.0 if not retrieved_urls else 0.0
    retrieved_k = retrieved_urls[:k]
    relevant = sum(1 for url in retrieved_k if url in expected_urls)
    return relevant / len(expected_urls)
    
def calculate_mrr_at_k(retrieved_urls, expected_urls, k):
    if not expected_urls:
        return 1.0 if not retrieved_urls else 0.0
    retrieved_k = retrieved_urls[:k]
    for i, url in enumerate(retrieved_k):
        if url in expected_urls:
            return 1.0 / (i + 1)
    return 0.0

import math
def calculate_ndcg_at_k(retrieved_urls, expected_urls, k):
    if not expected_urls:
        return 1.0 if not retrieved_urls else 0.0
    dcg = 0.0
    idcg = sum(1.0 / math.log2(i + 2) for i in range(min(k, len(expected_urls))))
    for i, url in enumerate(retrieved_urls[:k]):
        if url in expected_urls:
            dcg += 1.0 / math.log2(i + 2)
    return dcg / idcg if idcg > 0 else 0.0

async def run_evaluation():
    output = "==================================================\nNOVIQ PART 7 — SEARCH EVALUATION & PERFORMANCE\n==================================================\n\n"
    
    metrics = {mode: {"latency": [], "p@5": [], "r@10": [], "mrr@10": [], "ndcg@10": []} for mode in MODES}
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for mode in MODES:
            output += f"--- Evaluating {mode.upper()} Mode ---\n"
            for q, expected in EVAL_QUERIES.items():
                start = time.time()
                try:
                    res = await client.get(f"http://localhost:8000/api/v1/search/?q={q}&mode={mode}")
                    latency = time.time() - start
                    
                    if res.status_code == 200:
                        data = res.json().get("results", [])
                        urls = [r["url"] for r in data]
                        
                        metrics[mode]["latency"].append(latency)
                        metrics[mode]["p@5"].append(calculate_precision_at_k(urls, expected, 5))
                        metrics[mode]["r@10"].append(calculate_recall_at_k(urls, expected, 10))
                        metrics[mode]["mrr@10"].append(calculate_mrr_at_k(urls, expected, 10))
                        metrics[mode]["ndcg@10"].append(calculate_ndcg_at_k(urls, expected, 10))
                except Exception as e:
                    output += f"Query '{q}' failed: {e}\n"
                    
            if metrics[mode]["latency"]:
                lats = metrics[mode]["latency"]
                output += f"Median Latency: {statistics.median(lats):.3f}s\n"
                output += f"p95 Latency: {sorted(lats)[int(len(lats)*0.95)]:.3f}s\n"
                output += f"Mean Precision@5: {statistics.mean(metrics[mode]['p@5']):.3f}\n"
                output += f"Mean Recall@10: {statistics.mean(metrics[mode]['r@10']):.3f}\n"
                output += f"Mean MRR@10: {statistics.mean(metrics[mode]['mrr@10']):.3f}\n"
                output += f"Mean NDCG@10: {statistics.mean(metrics[mode]['ndcg@10']):.3f}\n\n"
                
    import os
    os.makedirs("../docs", exist_ok=True)
    with open("../docs/search-evaluation-results.md", "w", encoding="utf-8") as f:
        f.write(output)
    print(output)
        
if __name__ == "__main__":
    asyncio.run(run_evaluation())
