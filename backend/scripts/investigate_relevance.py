import asyncio
import httpx
import json

QUERIES = ["cancer", "ronaldo", "xyzrandom123456"]
MODES = ["keyword", "semantic", "hybrid"]

async def run():
    results = {}
    async with httpx.AsyncClient(timeout=30.0) as client:
        for mode in MODES:
            results[mode] = {}
            for q in QUERIES:
                res = await client.get(f"http://localhost:8000/api/v1/search/?q={q}&mode={mode}")
                try:
                    data = res.json().get("results", [])
                    results[mode][q] = [{"id": r["id"], "title": r["title"], "score": r["score"], "sources": r.get("retrieval_sources")} for r in data]
                except Exception as e:
                    results[mode][q] = f"Error: {e}"
                    
    with open("docs/relevance_investigation.json", "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    asyncio.run(run())
