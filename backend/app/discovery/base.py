"""
Base types for Noviq web discovery providers.

All providers implement the SearchProvider Protocol, returning DiscoveredPage objects.
This abstraction allows swapping Brave, DDG, Common Crawl, or any future provider.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Protocol, runtime_checkable


@dataclass
class DiscoveredPage:
    """A single candidate page returned by a discovery provider."""
    url: str
    title: str
    snippet: str
    domain: str
    source: str  # e.g. "brave", "ddg", "commoncrawl"
    discovered_at: datetime = field(default_factory=datetime.utcnow)
    rank: int = 0  # position in provider results


@runtime_checkable
class SearchProvider(Protocol):
    """
    Protocol that all search/discovery providers must implement.
    Returns a list of DiscoveredPage objects for a given query.
    """
    async def search(self, query: str, limit: int = 10) -> List[DiscoveredPage]:
        ...

    @property
    def name(self) -> str:
        ...

    @property
    def requires_api_key(self) -> bool:
        ...
