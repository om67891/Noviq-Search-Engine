"""
HackerNews Algolia Search provider for Noviq.
Uses the HackerNews Algolia API — completely free, no API key, no IP blocks.
Returns real, high-quality web URLs from HN stories.

API docs: https://hn.algolia.com/api
"""
import logging
from datetime import datetime
from typing import List
from urllib.parse import urlparse

import httpx

from app.discovery.base import DiscoveredPage, SearchProvider

logger = logging.getLogger(__name__)

HN_API_URL = "https://hn.algolia.com/api/v1/search"


class HNSearchProvider(SearchProvider):
    """HackerNews Algolia search provider — no API key, no rate limits from cloud."""

    name = "hackernews"
    requires_api_key = False

    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    async def search(self, query: str, limit: int = 15) -> List[DiscoveredPage]:
        logger.info(f"[HackerNews] Searching for: '{query}' (limit={limit})")

        try:
            params = {
                "query": query,
                "tags": "story",
                "hitsPerPage": limit,
                "numericFilters": "points>10",  # Only quality stories
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(HN_API_URL, params=params)
                response.raise_for_status()
                data = response.json()

        except Exception as e:
            logger.error(f"[HackerNews] API call failed: {e}")
            return []

        results = []
        hits = data.get("hits", [])

        for rank, hit in enumerate(hits):
            url = hit.get("url", "")
            # Skip HN discussion pages — we want the actual linked article
            if not url or "news.ycombinator.com" in url:
                continue

            try:
                domain = urlparse(url).netloc
            except Exception:
                domain = ""

            results.append(
                DiscoveredPage(
                    url=url,
                    title=hit.get("title", ""),
                    snippet=f"[HN] {hit.get('points', 0)} points • {hit.get('num_comments', 0)} comments",
                    domain=domain,
                    source="hackernews",
                    discovered_at=datetime.utcnow(),
                    rank=rank,
                )
            )

        logger.info(f"[HackerNews] Found {len(results)} results for '{query}'")
        return results
