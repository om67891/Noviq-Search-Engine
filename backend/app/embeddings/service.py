import logging
from typing import List, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

class EmbeddingService:
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
        return cls._instance

    def _get_device(self) -> str:
        if settings.EMBEDDING_DEVICE == "cpu":
            return "cpu"
        
        try:
            import torch
            if torch.cuda.is_available():
                return "cuda"
            if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                return "mps"
        except ImportError:
            pass
            
        return "cpu"

    def _load_model(self):
        if self._model is None:
            device = self._get_device()
            logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL} on device: {device}")
            try:
                import torch
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(settings.EMBEDDING_MODEL, device=device)
                logger.info("Embedding model loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
                raise e

    def embed_text(self, text: str) -> List[float]:
        """Embeds a single piece of text."""
        if not text.strip():
            return []
            
        self._load_model()
        
        # BGE models expect query instruction for retrieval, but for document embedding we just embed the text.
        # This basic method embeds the text directly (suitable for documents).
        embeddings = self._model.encode([text], normalize_embeddings=True)
        return embeddings[0].tolist()

    def embed_query(self, query: str) -> List[float]:
        """Embeds a query string, potentially adding the BGE instruction prefix if applicable."""
        if not query.strip():
            return []
            
        self._load_model()
        
        # For BGE, queries usually need an instruction prefix. 
        # BAAI/bge-small-en-v1.5 standard instruction:
        instruction = "Represent this sentence for searching relevant passages: "
        formatted_query = f"{instruction}{query}"
        
        embeddings = self._model.encode([formatted_query], normalize_embeddings=True)
        return embeddings[0].tolist()

    def embed_documents(self, texts: List[str], batch_size: int = 16) -> List[List[float]]:
        """Embeds a batch of documents."""
        if not texts:
            return []
            
        self._load_model()
        
        embeddings = self._model.encode(texts, batch_size=batch_size, normalize_embeddings=True)
        return [emb.tolist() for emb in embeddings]
