import asyncio
import httpx
import os
import time
import subprocess

async def test_fallback():
    print("==================================================")
    print("NOVIQ PART 7 — QDRANT FALLBACK TEST")
    print("==================================================\n")
    
    print("1. Ensuring Qdrant is running...")
    subprocess.run(["docker", "compose", "start", "qdrant"], check=True)
    time.sleep(3) # Wait for Qdrant to be ready
    
    query = "ronaldo"
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Test baseline
        print("2. Testing Hybrid mode with Qdrant ON")
        res = await client.get(f"http://localhost:8000/api/v1/search/?q={query}&mode=hybrid")
        if res.status_code == 200:
            sources = set()
            for r in res.json().get("results", []):
                sources.update(r.get("retrieval_sources", []))
            print(f"   -> Success. Retrieval sources: {list(sources)}")
        
        # Stop Qdrant
        print("\n3. Stopping Qdrant...")
        subprocess.run(["docker", "compose", "stop", "qdrant"], check=True)
        time.sleep(3)
        
        # Test fallback
        print("4. Testing Hybrid mode with Qdrant OFF")
        res = await client.get(f"http://localhost:8000/api/v1/search/?q={query}&mode=hybrid")
        if res.status_code == 200:
            sources = set()
            for r in res.json().get("results", []):
                sources.update(r.get("retrieval_sources", []))
            print(f"   -> Fallback Success! Retrieval sources: {list(sources)}")
        else:
            print(f"   -> Fallback Failed: HTTP {res.status_code}")
            
        print("\n5. Restarting Qdrant...")
        subprocess.run(["docker", "compose", "start", "qdrant"], check=True)
        time.sleep(3)
        print("Done.")

if __name__ == "__main__":
    asyncio.run(test_fallback())
