"""
Secure HTTP Fetcher for Noviq.

Adds SSRF protection: every URL is validated against private IP ranges
before any outbound request is made.
"""
import httpx
import logging
import asyncio
from typing import Optional

from app.discovery.ssrf_guard import SSRFError, guard as ssrf_guard

logger = logging.getLogger(__name__)


class Fetcher:
    """HTTP fetcher with SSRF protection, timeouts, size limits, and retry."""

    def __init__(self, timeout: int = 15, max_retries: int = 2, max_size: int = 5 * 1024 * 1024):
        self.timeout = timeout
        self.max_retries = max_retries
        self.max_size = max_size
        self.user_agent = "Noviq/1.0 (Research Search Engine)"

    async def fetch_page(self, url: str) -> tuple[Optional[str], int, Optional[str]]:
        """
        Fetches the HTML content of a URL.
        Returns (content, status_code, failure_reason).

        SSRF check is performed before any network request.
        """
        # ── SSRF Guard ────────────────────────────────────────────────────────
        try:
            ssrf_guard(url)
        except SSRFError as e:
            logger.warning(f"SSRF guard blocked: {url} — {e}")
            return None, 0, f"SSRF blocked: {e}"

        headers = {"User-Agent": self.user_agent}

        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(
                    timeout=self.timeout,
                    follow_redirects=True,
                    max_redirects=5,
                    headers=headers,
                ) as client:
                    response = await client.get(url)

                    # Check Content-Length before reading
                    content_length = response.headers.get("Content-Length")
                    if content_length and int(content_length) > self.max_size:
                        return None, response.status_code, "Response too large"

                    content = response.text
                    if len(content.encode("utf-8")) > self.max_size:
                        return None, response.status_code, "Response body too large"

                    response.raise_for_status()
                    return content, response.status_code, None

            except SSRFError as e:
                return None, 0, str(e)
            except httpx.TimeoutException:
                reason = f"HTTP timeout after {self.timeout}s"
                logger.warning(f"Attempt {attempt + 1}: {reason} for {url}")
                if attempt == self.max_retries:
                    return None, 0, reason
            except httpx.HTTPStatusError as e:
                reason = f"HTTP error {e.response.status_code}"
                logger.warning(f"Attempt {attempt + 1}: {reason} for {url}")
                if attempt == self.max_retries or e.response.status_code in [400, 401, 403, 404]:
                    return None, e.response.status_code, reason
            except Exception as e:
                reason = f"Network error: {e}"
                logger.warning(f"Attempt {attempt + 1}: {reason} for {url}")
                if attempt == self.max_retries:
                    return None, 0, reason

            await asyncio.sleep(2 ** attempt)

        return None, 0, "Max retries exceeded"
