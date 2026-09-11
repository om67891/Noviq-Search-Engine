import logging
from typing import Dict, Any, Optional

try:
    import trafilatura
except ImportError:
    trafilatura = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

logger = logging.getLogger(__name__)

class Extractor:
    """Extracts structured content from HTML pages."""
    
    def extract(self, html_content: str) -> Dict[str, Any]:
        """
        Attempts to extract title, main text, and metadata using Trafilatura.
        Falls back to BeautifulSoup if Trafilatura fails.
        """
        result = {
            "title": None,
            "text": None,
            "description": None,
            "author": None,
            "published_date": None,
            "language": None,
            "success": False
        }
        
        if not html_content:
            return result
            
        # Try Trafilatura first
        if trafilatura:
            try:
                extracted = trafilatura.extract(
                    html_content,
                    include_comments=False,
                    include_tables=False,
                    no_fallback=False,
                    output_format="json"
                )
                
                if extracted:
                    import json
                    data = json.loads(extracted)
                    result["title"] = data.get("title")
                    result["text"] = data.get("text")
                    result["author"] = data.get("author")
                    result["published_date"] = data.get("date")
                    result["description"] = data.get("description")
                    result["success"] = True
                    return result
            except Exception as e:
                logger.warning(f"Trafilatura extraction failed: {e}")
                
        # Fallback to BeautifulSoup
        if BeautifulSoup and not result["success"]:
            try:
                soup = BeautifulSoup(html_content, "html.parser")
                
                # Remove unwanted tags
                for element in soup(["script", "style", "nav", "footer", "iframe", "noscript"]):
                    element.decompose()
                
                result["title"] = soup.title.string if soup.title else None
                
                # Basic text extraction
                text = soup.get_text(separator=" ", strip=True)
                if text:
                    result["text"] = text
                    result["success"] = True
                    
                # Description meta tag
                desc_tag = soup.find("meta", attrs={"name": "description"})
                if desc_tag:
                    result["description"] = desc_tag.get("content")
                    
            except Exception as e:
                logger.error(f"BeautifulSoup fallback extraction failed: {e}")
                
        return result
