"""
DuckDuckGo HTML fallback provider for Noviq.

Does NOT require an API key. Scrapes DDG HTML search results.
Rate-limited by DDG — use only as fallback when no API key is configured.

This provider is NOT suitable for high-volume production use.
It is a development/demo fallback only.
"""
import logging
import re
import asyncio
from datetime import datetime
from typing import List
from urllib.parse import urlparse, unquote

import httpx
from bs4 import BeautifulSoup

from app.discovery.base import DiscoveredPage

logger = logging.getLogger(__name__)

DDG_URL = "https://html.duckduckgo.com/html/"

# Multiple user agents to rotate on retry — reduces rate limiting
USER_AGENTS = [
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
]


class DDGSearchProvider:
    """DuckDuckGo HTML scraper — no API key required."""

    name = "ddg"
    requires_api_key = False

    def __init__(self, timeout: int = 30):
        self.timeout = timeout  # Increased from 10s to 30s for Render server latency

    async def search(self, query: str, limit: int = 10) -> List[DiscoveredPage]:
        """
        Scrape DuckDuckGo HTML results and return DiscoveredPage objects.
        Retries with different user agents on failure.
        """
        for attempt, user_agent in enumerate(USER_AGENTS):
            results = await self._attempt_search(query, limit, user_agent)
            if results:
                return results

            if attempt < len(USER_AGENTS) - 1:
                logger.warning(f"[DDG] Attempt {attempt+1} returned no results, retrying...")
                await asyncio.sleep(2)  # Brief pause before retry

        logger.error(f"[DDG] All attempts failed for '{query}'")
        return []

    async def _attempt_search(self, query: str, limit: int, user_agent: str) -> List[DiscoveredPage]:
        """Single attempt to search DDG."""
        headers = {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        }
        data = {"q": query, "kl": "us-en"}

        logger.info(f"[DDG] Searching for: '{query}' (limit={limit})")

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                headers=headers,
            ) as client:
                response = await client.post(DDG_URL, data=data)
                response.raise_for_status()
                html = response.text

        except httpx.TimeoutException:
            logger.error(f"[DDG] Timeout ({self.timeout}s) searching for '{query}'")
            return []
        except Exception as e:
            logger.error(f"[DDG] Error searching for '{query}': {e}")
            return []

        results = self._parse_html(html, query, limit)
        logger.info(f"[DDG] Found {len(results)} results for '{query}'")
        return results

    def _parse_html(self, html: str, query: str, limit: int) -> List[DiscoveredPage]:
        """Parse DDG HTML response and extract result URLs."""
        results = []
        try:
            soup = BeautifulSoup(html, "html.parser")
            result_divs = soup.select(".result__body")

            if not result_divs:
                # Try alternative selectors for different DDG HTML structures
                result_divs = soup.select(".results_links") or soup.select(".result")

            for rank, div in enumerate(result_divs[:limit]):
                # Extract URL
                link_tag = div.select_one(".result__a") or div.select_one("a.result__a") or div.select_one("a[href]")
                if not link_tag:
                    continue

                raw_href = link_tag.get("href", "")
                url = _extract_ddg_url(raw_href)
                if not url:
                    continue

                title = link_tag.get_text(strip=True)

                # Extract snippet
                snippet_tag = div.select_one(".result__snippet") or div.select_one(".result__body")
                snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""

                try:
                    domain = urlparse(url).netloc
                except Exception:
                    domain = ""

                results.append(
                    DiscoveredPage(
                        url=url,
                        title=title,
                        snippet=snippet,
                        domain=domain,
                        source="ddg",
                        discovered_at=datetime.utcnow(),
                        rank=rank,
                    )
                )

        except Exception as e:
            logger.error(f"[DDG] Parse error for '{query}': {e}")

        return results


def _extract_ddg_url(href: str) -> str:
    """Extract the actual destination URL from DDG's redirect URL."""
    if not href:
        return ""

    # DDG wraps results in //duckduckgo.com/l/?uddg=ENCODED_URL&...
    if "uddg=" in href:
        match = re.search(r"uddg=([^&]+)", href)
        if match:
            return unquote(match.group(1))

    # Sometimes DDG returns direct URLs
    if href.startswith("http"):
        return href

    return ""
