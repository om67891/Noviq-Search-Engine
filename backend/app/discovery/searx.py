"""
SearXNG public instance provider for Noviq.
Uses a rotating list of public SearXNG instances to avoid rate limits and IP bans.
No API key required!
"""
import logging
import random
from datetime import datetime
from typing import List
from urllib.parse import urlparse

import httpx

from app.discovery.base import DiscoveredPage, SearchProvider

logger = logging.getLogger(__name__)

# List of known reliable public SearXNG instances
SEARX_INSTANCES = [
    "https://searx.be",
    "https://searx.tiekoetter.com",
    "https://searx.work",
    "https://paulgo.io",
    "https://search.mdosch.de",
    "https://searx.roflcopter.fr",
    "https://search.ononoki.org",
    "https://searx.perennialte.ch"
]

class SearxSearchProvider(SearchProvider):
    """SearXNG API scraper — rotates through public instances, no API key required."""

    name = "searx"
    requires_api_key = False

    def __init__(self, timeout: int = 15):
        self.timeout = timeout

    async def search(self, query: str, limit: int = 15) -> List[DiscoveredPage]:
        # Shuffle instances to distribute load and avoid hitting a blocked server twice
        instances = list(SEARX_INSTANCES)
        random.shuffle(instances)

        for instance in instances:
            logger.info(f"[SearXNG] Trying instance {instance} for query '{query}'")
            try:
                url = f"{instance}/search"
                params = {
                    "q": query,
                    "format": "json",
                    "language": "en"
                }
                async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                    response = await client.get(url, params=params)
                    response.raise_for_status()
                    data = response.json()
                    
                    if "results" not in data:
                        continue
                        
                    results = []
                    for rank, item in enumerate(data["results"][:limit]):
                        link = item.get("url", "")
                        if not link:
                            continue
                        
                        try:
                            domain = urlparse(link).netloc
                        except Exception:
                            domain = ""
                            
                        results.append(
                            DiscoveredPage(
                                url=link,
                                title=item.get("title", ""),
                                snippet=item.get("content", ""),
                                domain=domain,
                                source="searxng",
                                discovered_at=datetime.utcnow(),
                                rank=rank
                            )
                        )
                    
                    if results:
                        logger.info(f"[SearXNG] Success! Found {len(results)} results from {instance}")
                        return results
                        
            except Exception as e:
                logger.warning(f"[SearXNG] Instance {instance} failed: {e}")
                continue
                
        logger.error(f"[SearXNG] All {len(instances)} instances failed for query '{query}'")
        return []
