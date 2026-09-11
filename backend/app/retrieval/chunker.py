import logging
from typing import List, Dict, Any
import re

logger = logging.getLogger(__name__)

class TextChunker:
    """
    Deterministic text chunker that splits text into chunks of approximately fixed size (in words).
    """
    
    def __init__(self, chunk_size: int = 400, overlap: int = 100):
        # We use words as a proxy for tokens to avoid heavy tokenization overhead,
        # assuming ~1.3 tokens per word on average.
        self.chunk_size = chunk_size
        self.overlap = overlap
        
    def chunk_text(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Chunks text and preserves identity and metadata for each chunk.
        """
        if not text:
            return []
            
        words = text.split()
        if not words:
            return []
            
        chunks = []
        page_id = metadata.get("page_id")
        
        if len(words) <= self.chunk_size:
            # Document is smaller than chunk size, return it as a single chunk
            chunks.append({
                "chunk_id": f"{page_id}-0",
                "page_id": page_id,
                "chunk_index": 0,
                "text": text,
                **metadata
            })
            return chunks

        i = 0
        chunk_idx = 0
        while i < len(words):
            end_idx = min(i + self.chunk_size, len(words))
            chunk_text = " ".join(words[i:end_idx])
            
            chunks.append({
                "chunk_id": f"{page_id}-{chunk_idx}",
                "page_id": page_id,
                "chunk_index": chunk_idx,
                "text": chunk_text,
                **metadata
            })
            
            if end_idx == len(words):
                break
                
            chunk_idx += 1
            i += (self.chunk_size - self.overlap)
            
        return chunks
