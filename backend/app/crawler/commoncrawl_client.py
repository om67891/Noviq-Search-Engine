import httpx
import json
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class CommonCrawlClient:
    """Client for discovering URLs from Common Crawl."""
    
    CDX_API_URL = "https://index.commoncrawl.org/CC-MAIN-2024-38-index" # Using a recent index
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        
    async def search_urls(self, domain: str, limit: int = 100) -> List[Dict]:
        """
        Search for URLs in the Common Crawl index by domain.
        Returns a list of CDX records.
        """
        params = {
            "url": f"*.{domain}/*",
            "output": "json",
            "limit": limit
        }
        
        logger.info(f"Searching Common Crawl for {domain} with limit {limit}")
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.CDX_API_URL, params=params)
                response.raise_for_status()
                
                # CDX API returns JSON lines
                records = []
                for line in response.text.strip().split('\n'):
                    if line:
                        records.append(json.loads(line))
                return records
        except httpx.TimeoutException:
            logger.error("Timeout connecting to Common Crawl index.")
            return []
        except Exception as e:
            logger.error(f"Error fetching from Common Crawl index: {str(e)}")
            return []
