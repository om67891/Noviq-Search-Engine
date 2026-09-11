import asyncio
import httpx

async def run_live_test():
    print("--- STARTING PART 5 AGENTIC SEARCH E2E TEST ---")
    
    query = "Compare the machine learning research at Stanford with the latest malware exploits."
    payload = {
        "query": query,
        "mode": "agentic"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            res = await client.post("http://localhost:8000/api/v1/agentic-search/", json=payload, timeout=60.0)
            if res.status_code != 200:
                print(f"FAILED: HTTP {res.status_code}")
                print(res.text)
                return
                
            data = res.json()
            
            print(f"\nQUERY: {data['query']}")
            print(f"\nANSWER:\n{data['answer']}")
            print(f"\nCONFIDENCE: {data['confidence_score']}%")
            print(f"\nCITATIONS: {len(data['citations'])}")
            for c in data['citations']:
                print(f"  - [{c['citation_id']}] {c['url']}")
                
            print(f"\nSOURCES USED: {len(data['sources'])}")
            print(f"\nTRUST SUMMARY: {data['trust_summary']}")
            print(f"\nWARNINGS: {data['warnings']}")
            print(f"\nEXECUTION TRACE: {' -> '.join(data['execution_trace'])}")
            
            print("\n--- TEST PASSED ---")
            
        except Exception as e:
            print(f"Request failed: {e}")

if __name__ == "__main__":
    asyncio.run(run_live_test())
