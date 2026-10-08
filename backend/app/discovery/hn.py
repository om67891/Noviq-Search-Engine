"""
HackerNews Algolia Search provider for Noviq.
Uses the HackerNews Algolia API — completely free, no API key, no IP blocks.
Returns real, high-quality web URLs from HN stories.

Uses search_by_date to prioritize recent/trending content.
API docs: https://hn.algolia.com/api
"""
import logging
from datetime import datetime
from typing import List
from urllib.parse import urlparse

import httpx

from app.discovery.base import DiscoveredPage, SearchProvider

logger = logging.getLogger(__name__)

# Use search_by_date to get recent content, not old popular content
HN_SEARCH_URL = "https://hn.algolia.com/api/v1/search_by_date"
HN_RELEVANCE_URL = "https://hn.algolia.com/api/v1/search"

# Domains that block scrapers — skip them at discovery time to avoid wasting fetch budget
BLOCKED_DOMAINS = {
    "youtube.com", "youtu.be", "medium.com", "twitter.com", "x.com",
    "instagram.com", "facebook.com", "linkedin.com", "reddit.com",
    "dropbox.com", "drive.google.com", "docs.google.com",
}


class HNSearchProvider(SearchProvider):
    """HackerNews Algolia search provider — no API key, no rate limits from cloud."""

    name = "hackernews"
    requires_api_key = False

    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    async def search(self, query: str, limit: int = 15) -> List[DiscoveredPage]:
        logger.info(f"[HackerNews] Searching for: '{query}' (limit={limit})")
        results = []

        # Strategy: Get recent articles first, then fill up with relevant ones
        results = await self._fetch_hn(
            url=HN_SEARCH_URL,
            query=query,
            limit=limit * 3,  # Fetch more to account for skipped blocked domains
        )

        # If recent search didn't give enough results, supplement with top relevance
        if len(results) < 5:
            logger.info(f"[HackerNews] Only {len(results)} recent results, supplementing with relevance search")
            extra = await self._fetch_hn(
                url=HN_RELEVANCE_URL,
                query=query,
                limit=limit * 2,
            )
            # Merge, deduplicate by URL
            existing_urls = {r.url for r in results}
            for r in extra:
                if r.url not in existing_urls:
                    results.append(r)
                    existing_urls.add(r.url)

        # Limit to requested amount
        results = results[:limit]
        logger.info(f"[HackerNews] Returning {len(results)} results for '{query}'")
        return results

    async def _fetch_hn(self, url: str, query: str, limit: int) -> List[DiscoveredPage]:
        try:
            params = {
                "query": query,
                "tags": "story",
                "hitsPerPage": min(limit, 50),
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

        except Exception as e:
            logger.error(f"[HackerNews] API call to {url} failed: {e}")
            return []

        results = []
        hits = data.get("hits", [])

        for rank, hit in enumerate(hits):
            article_url = hit.get("url", "")

            # Skip HN discussion pages (no url means it's a text post, only has comments)
            if not article_url or "news.ycombinator.com" in article_url:
                continue

            try:
                domain = urlparse(article_url).netloc.replace("www.", "")
            except Exception:
                domain = ""

            # Skip domains that reliably block scraping
            if any(blocked in domain for blocked in BLOCKED_DOMAINS):
                logger.debug(f"[HackerNews] Skipping blocked domain: {domain}")
                continue

            results.append(
                DiscoveredPage(
                    url=article_url,
                    title=hit.get("title", ""),
                    snippet=f"HackerNews • {hit.get('points', 0)} points • {hit.get('num_comments', 0)} comments",
                    domain=domain,
                    source="hackernews",
                    discovered_at=datetime.utcnow(),
                    rank=rank,
                )
            )

        return results
