import re
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class SecurityAnalyzer:
    def __init__(self):
        # Known malicious/suspicious domains (local blacklist as required by Part 4)
        self.blacklist = {
            "malware.example.com",
            "phishing.example.com",
            "suspicious.example.net"
        }
        
        # Heuristic prompt injection patterns
        # Normalized before matching
        self.injection_patterns = [
            r"ignore\s+(all\s+)?previous\s+instructions",
            r"ignore\s+all\s+instructions",
            r"disregard\s+(the\s+)?previous\s+instructions",
            r"disregard\s+(the\s+)?system\s+message",
            r"disregard\s+all\s+safety",
            r"disregard\s+(all\s+)?guidelines",
            r"reveal\s+(your\s+)?(system\s+)?prompt",
            r"reveal\s+hidden\s+instructions",
            r"act\s+as\s+(an\s+)?administrator",
            r"override\s+(previous\s+)?instructions",
            r"follow\s+these\s+instructions\s+instead",
            r"execute\s+(the\s+)?following\s+command",
            r"send\s+(your\s+)?credentials",
            r"you\s+are\s+now\s+\w+",           # "you are now DAN"
            r"do\s+anything\s+now",             # DAN: Do Anything Now
            r"jailbreak",
            r"system\s+message\s*:",
            r"developer\s+message\s*:",
        ]
        self._compiled_patterns = [re.compile(p) for p in self.injection_patterns]
        
    def _normalize_text(self, text: str) -> str:
        """Normalizes text for basic obfuscation handling (lowercase, squashing whitespace)."""
        if not text:
            return ""
        # Lowercase and replace all types of whitespace with single space
        return re.sub(r"\s+", " ", text.lower()).strip()
        
    def assess_security(self, text: str, domain: str) -> Dict[str, Any]:
        """
        Assesses the security of the content and domain.
        Returns risk score (0-100), status, and signals.
        """
        risk_score = 0
        signals = {
            "blacklist": False,
            "injection_patterns": []
        }
        
        # 1. Blacklist Check
        if domain in self.blacklist:
            risk_score += 80
            signals["blacklist"] = True
            
        # 2. Prompt Injection Check
        normalized_text = self._normalize_text(text)
        
        for pattern in self._compiled_patterns:
            matches = pattern.findall(normalized_text)
            if matches:
                risk_score += 50
                signals["injection_patterns"].append(pattern.pattern)
                
        # 3. Contextual false positive reduction
        # If the page discusses prompt injection (e.g., "this article explains how prompt injection attacks work")
        # we lightly reduce the score to distinguish discussion from direct instruction.
        if "explains how" in normalized_text or "researchers studied" in normalized_text or "article" in normalized_text:
            if risk_score > 0 and not signals["blacklist"]:
                risk_score = max(0, risk_score - 20)
                
        # Cap at 100
        risk_score = min(100, risk_score)
        
        # Determine Status
        if risk_score >= 70:
            status = "HIGH_RISK"
        elif risk_score >= 30:
            status = "SUSPICIOUS"
        else:
            status = "SAFE"
            
        return {
            "security_risk": risk_score,
            "security_status": status,
            "security_signals": signals
        }
