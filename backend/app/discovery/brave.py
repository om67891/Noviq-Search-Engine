"""
Brave Search API provider for Noviq.

Uses the Brave Web Search API (https://api.search.brave.com/res/v1/web/search).
Free tier: 2,000 requests/month. No account required beyond API key sign-up.

Set in .env:
  SEARCH_PROVIDER=brave
  BRAVE_SEARCH_API_KEY=your_key_here
"""
import logging
from datetime import datetime
from typing import List
from urllib.parse import urlparse

import httpx

from app.discovery.base import DiscoveredPage

logger = logging.getLogger(__name__)

BRAVE_API_URL = "https://api.search.brave.com/res/v1/web/search"


class BraveSearchProvider:
    """Brave Web Search API provider."""

    name = "brave"
    requires_api_key = True

    def __init__(self, api_key: str, timeout: int = 10):
        if not api_key:
            raise ValueError("BRAVE_SEARCH_API_KEY is required for BraveSearchProvider")
        self.api_key = api_key
        self.timeout = timeout

    async def search(self, query: str, limit: int = 10) -> List[DiscoveredPage]:
        """
        Search Brave Web Search API and return DiscoveredPage objects.
        """
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.api_key,
        }
        params = {
            "q": query,
            "count": min(limit, 20),  # Brave max is 20 per request
            "safesearch": "moderate",
            "freshness": "pw",  # past week — prefer fresh results
        }

        logger.info(f"[Brave] Searching for: '{query}' (limit={limit})")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    BRAVE_API_URL,
                    headers=headers,
                    params=params,
                )
                response.raise_for_status()
                data = response.json()

        except httpx.TimeoutException:
            logger.error(f"[Brave] Timeout searching for '{query}'")
            return []
        except httpx.HTTPStatusError as e:
            logger.error(f"[Brave] HTTP error {e.response.status_code} for '{query}': {e.response.text[:200]}")
            return []
        except Exception as e:
            logger.error(f"[Brave] Unexpected error for '{query}': {e}")
            return []

        results = []
        web_results = data.get("web", {}).get("results", [])

        for rank, item in enumerate(web_results):
            url = item.get("url", "")
            if not url:
                continue

            try:
                domain = urlparse(url).netloc
            except Exception:
                domain = ""

            results.append(
                DiscoveredPage(
                    url=url,
                    title=item.get("title", ""),
                    snippet=item.get("description", ""),
                    domain=domain,
                    source="brave",
                    discovered_at=datetime.utcnow(),
                    rank=rank,
                )
            )

        logger.info(f"[Brave] Found {len(results)} results for '{query}'")
        return results
