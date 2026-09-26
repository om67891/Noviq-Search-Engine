"""
Provider factory for Noviq web discovery.

Selects the appropriate SearchProvider based on environment configuration:

  SEARCH_PROVIDER=brave  → BraveSearchProvider (requires BRAVE_SEARCH_API_KEY)
  SEARCH_PROVIDER=ddg    → DDGSearchProvider (no key, rate-limited)
  (default)              → DDGSearchProvider if no Brave key, else Brave

Usage:
    from app.discovery.factory import get_provider
    provider = get_provider()
    results = await provider.search("ronaldo")
"""
import logging
from functools import lru_cache

from app.core.config import settings
from app.discovery.base import SearchProvider

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_provider() -> SearchProvider:
    """
    Returns a configured SearchProvider instance.
    Result is cached — provider is created once per process.
    """
    provider_name = getattr(settings, "SEARCH_PROVIDER", "").lower()
    brave_key = getattr(settings, "BRAVE_SEARCH_API_KEY", "") or ""

    # Brave is preferred when key is available
    if provider_name == "brave" or (brave_key and provider_name != "ddg"):
        if not brave_key:
            logger.warning(
                "SEARCH_PROVIDER=brave but BRAVE_SEARCH_API_KEY is not set. "
                "Falling back to DuckDuckGo."
            )
        else:
            from app.discovery.brave import BraveSearchProvider
            logger.info("Using Brave Search API provider.")
            return BraveSearchProvider(api_key=brave_key)

    # HackerNews Algolia — always works from cloud IPs, no API key
    if provider_name == "hn":
        from app.discovery.hn import HNSearchProvider
        logger.info("Using HackerNews Algolia provider.")
        return HNSearchProvider()

    # SearXNG — try first as it gives more general results
    if provider_name == "searx":
        from app.discovery.searx import SearxSearchProvider
        logger.info("Using SearXNG public instances provider.")
        return SearxSearchProvider()

    # Default: SearXNG with HN as documented fallback
    from app.discovery.searx import SearxSearchProvider
    logger.info("Using SearXNG public instances as default discovery provider.")
    return SearxSearchProvider()
