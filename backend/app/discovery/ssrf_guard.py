"""
SSRF Guard for Noviq — blocks requests to private/internal network ranges.

Because Noviq fetches arbitrary URLs from web discovery results, every URL
must be validated before fetching to prevent Server-Side Request Forgery attacks.

Blocked ranges:
  - localhost / 127.x.x.x
  - Private: 10.x, 172.16-31.x, 192.168.x
  - Link-local: 169.254.x (AWS metadata, GCP metadata)
  - IPv6 loopback / link-local
  - Cloud metadata endpoints: 169.254.169.254
  - Internal Docker bridge: 172.17-172.31.x
"""
import ipaddress
import logging
import socket
from urllib.parse import urlparse
from typing import Tuple

logger = logging.getLogger(__name__)

# Only these schemes are allowed
ALLOWED_SCHEMES = {"http", "https"}

# Blocked hostnames (exact match)
BLOCKED_HOSTNAMES = {
    "localhost",
    "metadata.google.internal",
    "metadata",
}

# Blocked IP network ranges (CIDR notation)
BLOCKED_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),      # Loopback
    ipaddress.ip_network("10.0.0.0/8"),        # Private Class A
    ipaddress.ip_network("172.16.0.0/12"),     # Private Class B
    ipaddress.ip_network("192.168.0.0/16"),    # Private Class C
    ipaddress.ip_network("169.254.0.0/16"),    # Link-local / AWS/GCP metadata
    ipaddress.ip_network("0.0.0.0/8"),         # "This" network
    ipaddress.ip_network("100.64.0.0/10"),     # Carrier-grade NAT
    ipaddress.ip_network("198.51.100.0/24"),   # TEST-NET-2
    ipaddress.ip_network("203.0.113.0/24"),    # TEST-NET-3
    ipaddress.ip_network("::1/128"),           # IPv6 loopback
    ipaddress.ip_network("fe80::/10"),         # IPv6 link-local
    ipaddress.ip_network("fc00::/7"),          # IPv6 unique local
]


class SSRFError(Exception):
    """Raised when a URL is blocked by SSRF protection."""
    pass


def _is_private_ip(hostname: str) -> Tuple[bool, str]:
    """Resolve hostname and check if the IP is in a private/blocked range."""
    try:
        # Resolve the hostname to an IP address
        addr_infos = socket.getaddrinfo(hostname, None)
        for addr_info in addr_infos:
            ip_str = addr_info[4][0]
            try:
                ip = ipaddress.ip_address(ip_str)
                for network in BLOCKED_NETWORKS:
                    if ip in network:
                        return True, f"IP {ip_str} is in blocked network {network}"
            except ValueError:
                continue
        return False, ""
    except socket.gaierror as e:
        # DNS resolution failed — block it to be safe
        return True, f"DNS resolution failed: {e}"


def validate_url(url: str) -> Tuple[bool, str]:
    """
    Validate a URL for SSRF safety.
    Returns (is_safe: bool, reason: str).
    reason is empty string when safe.
    """
    if not url or not isinstance(url, str):
        return False, "URL is empty or not a string"

    try:
        parsed = urlparse(url)
    except Exception as e:
        return False, f"URL parse error: {e}"

    # Check scheme
    scheme = parsed.scheme.lower()
    if scheme not in ALLOWED_SCHEMES:
        return False, f"Scheme '{scheme}' not allowed. Only http/https permitted."

    hostname = parsed.hostname
    if not hostname:
        return False, "URL has no hostname"

    # Check blocked hostnames
    if hostname.lower() in BLOCKED_HOSTNAMES:
        return False, f"Hostname '{hostname}' is blocked"

    # Check if hostname looks like an IP address directly
    try:
        ip = ipaddress.ip_address(hostname)
        for network in BLOCKED_NETWORKS:
            if ip in network:
                return False, f"Direct IP {hostname} is in blocked network {network}"
    except ValueError:
        # Not a direct IP — resolve it
        pass

    # Resolve hostname and check resolved IP
    is_private, reason = _is_private_ip(hostname)
    if is_private:
        return False, f"SSRF blocked: {reason}"

    return True, ""


def guard(url: str) -> None:
    """
    Validate a URL and raise SSRFError if it is not safe.
    Use this before any outbound HTTP request in the fetcher.
    """
    is_safe, reason = validate_url(url)
    if not is_safe:
        logger.warning(f"SSRF guard blocked URL '{url}': {reason}")
        raise SSRFError(f"URL blocked by SSRF protection: {reason}")
    logger.debug(f"SSRF guard passed for URL: {url}")
