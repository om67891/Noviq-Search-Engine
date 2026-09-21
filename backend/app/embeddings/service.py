"""
EmbeddingService — uses HuggingFace Inference API instead of local SentenceTransformer.

Why: The local SentenceTransformer + PyTorch stack requires ~700MB RAM which
crashes Render's 512MB free tier. HuggingFace hosts the same model for free;
we just make an HTTP call, using virtually zero local RAM.

Model: BAAI/bge-small-en-v1.5 (same as before, same quality)
"""
import logging
import os
import time
from typing import List, Optional

import httpx

logger = logging.getLogger(__name__)

# HuggingFace Inference API endpoint for embeddings
HF_API_URL = "https://api-inference.huggingface.co/models/BAAI/bge-small-en-v1.5"
HF_API_KEY = os.environ.get("HUGGINGFACE_API_KEY", "")

# Fallback: simple TF-IDF-style zero vector if HF is unavailable
VECTOR_DIM = 384  # bge-small-en-v1.5 output dimension


class EmbeddingService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
        return cls._instance

    def _call_hf_api(self, texts: List[str], retries: int = 3) -> Optional[List[List[float]]]:
        """
        Call HuggingFace Inference API to get embeddings.
        Handles model cold-start (503) with automatic retry.
        """
        if not HF_API_KEY:
            logger.warning("HUGGINGFACE_API_KEY not set — embeddings will be zero vectors.")
            return None

        headers = {"Authorization": f"Bearer {HF_API_KEY}"}
        payload = {"inputs": texts, "options": {"wait_for_model": True}}

        for attempt in range(retries):
            try:
                with httpx.Client(timeout=60.0) as client:
                    response = client.post(HF_API_URL, headers=headers, json=payload)

                if response.status_code == 200:
                    result = response.json()
                    # HF returns list of embeddings directly
                    if isinstance(result, list) and len(result) > 0:
                        return result
                    logger.error(f"Unexpected HF response format: {result}")
                    return None

                elif response.status_code == 503:
                    # Model is loading on HuggingFace side — wait and retry
                    wait = 20 * (attempt + 1)
                    logger.warning(f"HuggingFace model loading, retrying in {wait}s... (attempt {attempt+1}/{retries})")
                    time.sleep(wait)
                    continue

                else:
                    logger.error(f"HuggingFace API error {response.status_code}: {response.text}")
                    return None

            except Exception as e:
                logger.error(f"HuggingFace API call failed (attempt {attempt+1}): {e}")
                if attempt < retries - 1:
                    time.sleep(5)

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
