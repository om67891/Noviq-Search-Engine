import logging
from typing import Dict, Any, List, Optional
from opensearchpy import OpenSearch, helpers
from app.core.config import settings

logger = logging.getLogger(__name__)

class OpenSearchClient:
    def __init__(self):
        self.index_name = "noviq_pages"
        
        # We handle cases where OPENSEARCH_URL might not be fully configured yet
        host = settings.OPENSEARCH_URL or "http://localhost:9200"
        
        auth = None
        if settings.OPENSEARCH_USERNAME and settings.OPENSEARCH_PASSWORD:
            auth = (settings.OPENSEARCH_USERNAME, settings.OPENSEARCH_PASSWORD)
            
        self.client = OpenSearch(
            hosts=[host],
            http_auth=auth,
            use_ssl=host.startswith("https"),
            verify_certs=False,
            ssl_show_warn=False
        )
        
    def ensure_index(self):
        """Creates the index with BM25 mapping if it doesn't exist."""
        try:
            if not self.client.indices.exists(index=self.index_name):
                mapping = {
                    "mappings": {
                        "properties": {
                            "document_id": {"type": "keyword"},
                            "url": {"type": "keyword"},
                            "domain": {"type": "keyword"},
                            "title": {
                                "type": "text",
                                "analyzer": "standard"
                            },
                            "content": {
                                "type": "text",
                                "analyzer": "standard"
                            },
                            "content_hash": {"type": "keyword"},
                            "language": {"type": "keyword"},
                            "trust_score": {"type": "integer"},
                            "trust_level": {"type": "keyword"},
                            "security_risk": {"type": "integer"},
                            "security_status": {"type": "keyword"}
                        }
                    }
                }
                self.client.indices.create(index=self.index_name, body=mapping)
                logger.info(f"Created OpenSearch index: {self.index_name}")
        except Exception as e:
            logger.error(f"Failed to ensure OpenSearch index: {e}")

    def index_document(self, document_id: int, url: str, domain: str, title: Optional[str], content: str, content_hash: str, language: Optional[str] = None, trust_score: int = 0, trust_level: str = "Low", security_risk: int = 0, security_status: str = "SAFE"):
        """Indexes a document into OpenSearch."""
        doc = {
            "document_id": str(document_id),
            "url": url,
            "domain": domain,
            "title": title or "",
            "content": content,
            "content_hash": content_hash,
            "language": language or "en",
            "trust_score": trust_score,
            "trust_level": trust_level,
            "security_risk": security_risk,
            "security_status": security_status
        }
        
        try:
            self.client.index(
                index=self.index_name,
                body=doc,
                id=str(document_id),
                refresh=True
            )
            return True
        except Exception as e:
            logger.error(f"Error indexing document {document_id}: {e}")
            return False

    def search(self, query: str, limit: int = 10, offset: int = 0) -> Dict[str, Any]:
        """Performs a BM25 lexical search."""
        if not query.strip():
            return {"total": 0, "results": []}
            
        body = {
            "from": offset,
            "size": limit,
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["title^2", "content"],
                    "type": "best_fields"
                }
            },
            "highlight": {
                "fields": {
                    "content": {
                        "fragment_size": 150,
                        "number_of_fragments": 2
                    }
                }
            }
        }
        
        try:
            response = self.client.search(index=self.index_name, body=body)
            
            hits = response["hits"]["hits"]
            total = response["hits"]["total"]["value"]
            
            results = []
            for hit in hits:
                source = hit["_source"]
                highlight = hit.get("highlight", {})
                
                # Use highlighted snippet or fall back to start of content
                snippet = " ".join(highlight.get("content", []))
                if not snippet and source.get("content"):
                    snippet = source["content"][:150] + "..."
                    
                results.append({
                    "id": source.get("document_id"),
                    "url": source.get("url"),
                    "domain": source.get("domain"),
                    "title": source.get("title"),
                    "snippet": snippet,
                    "score": hit["_score"],
                    "trust_score": source.get("trust_score", 0),
                    "trust_level": source.get("trust_level", "Low"),
                    "security_risk": source.get("security_risk", 0),
                    "security_status": source.get("security_status", "SAFE")
                })
                
            return {
                "total": total,
                "results": results
            }
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return {"total": 0, "results": []}
