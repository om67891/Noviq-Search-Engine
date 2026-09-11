from urllib.parse import urlparse, urlunparse

def normalize_url(url: str) -> str:
    """
    Normalizes a URL by:
    - Lowercasing the scheme and netloc.
    - Removing default ports (80 for http, 443 for https).
    - Removing the fragment (#).
    - Ensuring a consistent trailing slash behavior for root.
    """
    try:
        parsed = urlparse(url)
        scheme = parsed.scheme.lower()
        netloc = parsed.netloc.lower()
        
        # Remove default ports
        if scheme == "http" and netloc.endswith(":80"):
            netloc = netloc[:-3]
        elif scheme == "https" and netloc.endswith(":443"):
            netloc = netloc[:-4]
            
        path = parsed.path
        if not path:
            path = "/"
            
        # Reconstruct without fragment and params for basic normalization
        normalized = urlunparse((scheme, netloc, path, parsed.params, parsed.query, ""))
        return normalized
    except Exception:
        return url

def validate_url(url: str) -> bool:
    """
    Validates that a URL is http or https and has a valid hostname.
    """
    try:
        parsed = urlparse(url)
        return parsed.scheme in ["http", "https"] and bool(parsed.netloc)
    except Exception:
        return False
