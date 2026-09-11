import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class TrustScorer:
    def __init__(self):
        # Base weightings for different signals
        self.weights = {
            "https": 10,
            "tld_authority": 30, # .gov, .edu
            "citation": 20,
            "freshness": 10,
            "domain_authority_heuristic": 30
        }
        
        self.high_trust_tlds = {".gov", ".edu", ".gov.in", ".edu.in", ".gov.uk", ".ac.uk"}
        
    def assess_trust(self, url: str, domain: str, text: str, published_at: datetime = None) -> Dict[str, Any]:
        """
        Assesses trust based on deterministic heuristics.
        Returns a trust score (0-100), level, and signals.
        """
        score = 0
        signals = {
            "https": False,
            "tld_authority": False,
            "citation_quality": 0,
            "freshness": 0,
            "domain_authority": 0
        }
        
        # 1. HTTPS Signal
        if url.startswith("https://"):
            score += self.weights["https"]
            signals["https"] = True
            
        # 2. TLD Authority (Government/Education)
        is_high_trust_tld = any(domain.endswith(tld) for tld in self.high_trust_tlds)
        if is_high_trust_tld:
            score += self.weights["tld_authority"]
            signals["tld_authority"] = True
            
        # 3. Citation Quality (Heuristic: presence of "references", bracketed citations [1], etc)
        citation_score = 0
        text_lower = text.lower() if text else ""
        if "references" in text_lower[-1000:]: # Look near the end
            citation_score += 10
        if "bibliography" in text_lower[-1000:]:
            citation_score += 10
        # If it has standard citations [1] or (Author, Year)
        import re
        if re.search(r"\[\d+\]", text_lower):
            citation_score += 10
            
        citation_score = min(self.weights["citation"], citation_score)
        score += citation_score
        signals["citation_quality"] = citation_score
        
        # 4. Freshness Signal
        freshness_score = 0
        if published_at:
            age_days = (datetime.utcnow() - published_at).days
            if age_days < 30:
                freshness_score = self.weights["freshness"]
            elif age_days < 365:
                freshness_score = self.weights["freshness"] * 0.5
        score += freshness_score
        signals["freshness"] = freshness_score
        
        # 5. Domain Authority Heuristic (Local proxy for authority)
        domain_auth = 0
        if len(domain.split(".")) == 2: # Root domains generally slightly higher auth than random subdomains
            domain_auth += 10
        if "example.com" not in domain and "test" not in domain:
            domain_auth += 10
            
        domain_auth = min(self.weights["domain_authority_heuristic"], domain_auth)
        score += domain_auth
        signals["domain_authority"] = domain_auth
        
        # Normalization (Cap at 100)
        final_score = min(100, int(score))
        
        # Determine Trust Level
        if final_score >= 80:
            level = "High"
        elif final_score >= 50:
            level = "Medium"
        else:
            level = "Low"
            
        return {
            "trust_score": final_score,
            "trust_level": level,
            "trust_signals": signals
        }
