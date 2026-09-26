"""
SearXNG public instance provider for Noviq.
Uses HTML scraping (NOT the JSON API) to bypass cloud IP restrictions.
No API key required!

Key insight from logs: public SearXNG instances block format=json from cloud IPs
(returning 429 or plain HTML). We now scrape the HTML output instead.
"""
import logging
import random
from datetime import datetime
from typing import List
from urllib.parse import urlparse, urlencode

import httpx
from bs4 import BeautifulSoup

from app.discovery.base import DiscoveredPage, SearchProvider

logger = logging.getLogger(__name__)

# Only include instances confirmed to be UP based on log analysis:
# - Removed: searx.roflcopter.fr (DNS dead), search.ononoki.org (DNS dead)
# - Removed: searx.work (SSL broken), search.mdosch.de (418 blocks bots)
# Added fresh instances from the official SearXNG public list
SEARX_INSTANCES = [
    "https://searx.be",
    "https://searx.tiekoetter.com",
    "https://paulgo.io",
    "https://searx.perennialte.ch",
    "https://search.bus-hit.me",
    "https://priv.au",
    "https://etsi.me",
    "https://search.inetol.net",
    "https://searx.juancord.xyz",
    "https://search.projectsegfau.lt",
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]


def _parse_searxng_html(html: str, instance: str) -> List[dict]:
    """
    Parse SearXNG HTML results page.
    SearXNG results are in <article class='result'> tags.
    """
    soup = BeautifulSoup(html, "html.parser")
    results = []

    # SearXNG HTML structure: <article class="result result-default"> 
    # containing <h3><a href="...">title</a></h3>
    # and <p class="content">snippet</p>
    for article in soup.select("article.result"):
        # Extract URL
        link_tag = article.select_one("h3 a")
        if not link_tag:
            continue
        url = link_tag.get("href", "")
        if not url or not url.startswith("http"):
            continue

        title = link_tag.get_text(strip=True)

        # Extract snippet
        snippet_tag = article.select_one("p.content")
        snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""

        results.append({"url": url, "title": title, "snippet": snippet})

    return results


class SearxSearchProvider(SearchProvider):
    """SearXNG HTML scraper — rotates through public instances, no API key required."""

    name = "searx"
    requires_api_key = False

    def __init__(self, timeout: int = 8):
        self.timeout = timeout

    async def search(self, query: str, limit: int = 15) -> List[DiscoveredPage]:
        instances = list(SEARX_INSTANCES)
        random.shuffle(instances)

        for instance in instances:
            logger.info(f"[SearXNG] Trying instance {instance} for query '{query}'")
            try:
                # Use HTML format (NOT json) — cloud IPs are blocked from JSON API
                params = urlencode({
                    "q": query,
                    "language": "en",
                    "time_range": "",
                    "safesearch": "0",
                    "theme": "simple",
                })
                url = f"{instance}/search?{params}"

                headers = {
                    "User-Agent": random.choice(USER_AGENTS),
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept-Encoding": "gzip, deflate, br",
                    "DNT": "1",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                }

                async with httpx.AsyncClient(
                    timeout=self.timeout,
                    follow_redirects=True,
                    verify=False,  # Skip SSL verification — some instances have bad certs
                ) as client:
                    response = await client.get(url, headers=headers)
                    response.raise_for_status()
                    html = response.text

                raw_results = _parse_searxng_html(html, instance)

                if not raw_results:
                    logger.warning(f"[SearXNG] {instance} returned 0 parsed results (HTML may be blocked)")
                    continue

                results = []
                for rank, item in enumerate(raw_results[:limit]):
                    link = item["url"]
                    try:
                        domain = urlparse(link).netloc
                    except Exception:
                        domain = ""

                    results.append(
                        DiscoveredPage(
                            url=link,
                            title=item.get("title", ""),
                            snippet=item.get("snippet", ""),
                            domain=domain,
                            source="searxng",
                            discovered_at=datetime.utcnow(),
                            rank=rank,
                        )
                    )

                logger.info(f"[SearXNG] Success! Got {len(results)} results from {instance}")
                return results

            except httpx.HTTPStatusError as e:
                logger.warning(f"[SearXNG] {instance} HTTP {e.response.status_code}: blocked")
                continue
            except Exception as e:
                logger.warning(f"[SearXNG] {instance} failed: {e}")
                continue

        logger.error(f"[SearXNG] All {len(instances)} instances failed for query '{query}'")
        return []
