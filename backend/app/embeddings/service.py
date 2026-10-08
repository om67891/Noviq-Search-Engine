"""
EmbeddingService — uses HuggingFace Inference API instead of local SentenceTransformer.

Why: The local SentenceTransformer + PyTorch stack requires ~700MB RAM which
crashes Render's 512MB free tier. HuggingFace hosts the same model for free;
we just make an HTTP call, using virtually zero local RAM.

Model: BAAI/bge-small-en-v1.5 (same as before, same quality)

If HuggingFace is unreachable (e.g. Render free tier DNS issues), the service
gracefully disables itself and returns zero vectors. BM25 keyword search
continues to work perfectly without embeddings.
"""
import logging
import os
from typing import List, Optional

import httpx

logger = logging.getLogger(__name__)

# HuggingFace Inference API endpoint for embeddings
HF_API_URL = "https://api-inference.huggingface.co/models/BAAI/bge-small-en-v1.5"

# Fallback: zero vector when HF is unavailable
VECTOR_DIM = 384  # bge-small-en-v1.5 output dimension

# Module-level flag — checked once, prevents repeated DNS failures
_hf_available: Optional[bool] = None


def _check_hf_once() -> bool:
    """One-shot reachability check for HuggingFace API."""
    global _hf_available
    if _hf_available is not None:
        return _hf_available

    api_key = os.environ.get("HUGGINGFACE_API_KEY", "")
    if not api_key:
        _hf_available = False
        logger.warning("HUGGINGFACE_API_KEY not set — embeddings disabled.")
        return False

    try:
        # Quick HEAD request to check DNS + connectivity (5 second timeout)
        with httpx.Client(timeout=5.0) as client:
            response = client.head(
                "https://api-inference.huggingface.co",
                headers={"Authorization": f"Bearer {api_key}"},
            )
        _hf_available = True
        logger.info("HuggingFace API is reachable — semantic embeddings enabled.")
        return True
    except Exception as e:
        _hf_available = False
        logger.warning(f"HuggingFace API unreachable — embeddings disabled for this session. ({e})")
        return False


class EmbeddingService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
        return cls._instance

    def _call_hf_api(self, texts: List[str], retries: int = 2) -> Optional[List[List[float]]]:
        """Call HuggingFace Inference API to get embeddings."""
        # Fast exit if HF was already found unreachable
        if not _check_hf_once():
            return None

        api_key = os.environ.get("HUGGINGFACE_API_KEY", "")
        headers = {"Authorization": f"Bearer {api_key}"}
        payload = {"inputs": texts, "options": {"wait_for_model": True}}

        for attempt in range(retries):
            try:
                with httpx.Client(timeout=30.0) as client:
                    response = client.post(HF_API_URL, headers=headers, json=payload)

                if response.status_code == 200:
                    result = response.json()
                    if isinstance(result, list) and len(result) > 0:
                        return result
                    logger.error(f"Unexpected HF response format: {result}")
                    return None

                elif response.status_code == 503:
                    import time
                    wait = 15 * (attempt + 1)
                    logger.warning(f"HuggingFace model loading, retrying in {wait}s... (attempt {attempt+1}/{retries})")
                    time.sleep(wait)
                    continue

                else:
                    logger.error(f"HuggingFace API error {response.status_code}: {response.text[:200]}")
                    return None

            except (httpx.ConnectError, httpx.TimeoutException):
                # Network failure — mark as unavailable, stop trying
                global _hf_available
                _hf_available = False
                logger.warning("HuggingFace became unreachable mid-session — disabling embeddings.")
                return None
            except Exception as e:
                logger.error(f"HuggingFace API call failed (attempt {attempt+1}): {e}")
                if attempt < retries - 1:
                    import time
                    time.sleep(3)

        return None

    def _zero_vector(self) -> List[float]:
        """Returns a zero vector as fallback when API is unavailable."""
        return [0.0] * VECTOR_DIM

    def embed_text(self, text: str) -> List[float]:
        """Embeds a single piece of text."""
        if not text or not text.strip():
            return self._zero_vector()

        result = self._call_hf_api([text[:512]])  # Limit to 512 chars
        if result and len(result) > 0:
            return result[0]
        return self._zero_vector()

    def embed_query(self, query: str) -> List[float]:
        """
        Embeds a query string with BGE instruction prefix for better retrieval.
        """
        if not query or not query.strip():
            return self._zero_vector()

        # BGE models perform better with instruction prefix for queries
        instruction = "Represent this sentence for searching relevant passages: "
        formatted = f"{instruction}{query}"

        result = self._call_hf_api([formatted[:512]])
        if result and len(result) > 0:
            return result[0]
        return self._zero_vector()

    def embed_documents(self, texts: List[str], batch_size: int = 16) -> List[List[float]]:
        """Embeds a batch of documents."""
        if not texts:
            return []

        all_embeddings = []

        # Process in batches to stay within API limits
        for i in range(0, len(texts), batch_size):
            batch = [t[:512] for t in texts[i:i + batch_size]]
            result = self._call_hf_api(batch)
            if result:
                all_embeddings.extend(result)
            else:
                # Fallback: zero vectors for failed batch
                all_embeddings.extend([self._zero_vector() for _ in batch])

        return all_embeddings
