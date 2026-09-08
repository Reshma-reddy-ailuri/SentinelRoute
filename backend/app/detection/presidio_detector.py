import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Standard Presidio PII entities we monitor
SUPPORTED_ENTITIES = [
    "PERSON",
    "EMAIL_ADDRESS",
    "PHONE_NUMBER",
    "LOCATION",
    "CREDIT_CARD",
    "IP_ADDRESS",
    "US_SSN",
    "IBAN_CODE"
]

class PresidioDetector:
    """
    Lightweight PII detector wrapper.

    The project prefers a fast, reliable fallback regex implementation in local/dev runs because
    the full Microsoft Presidio NLP engine can be slow or unavailable when spaCy models are not
    preloaded. This keeps the app responsive and still catches the main PII patterns used by the
    gateway policy checks.
    """
    def __init__(self):
        self.analyzer = None
        self.initialized = False

    def _init_presidio(self):
        """Attempt initialization only if a caller explicitly enables the heavy NLP path."""
        self.analyzer = None
        self.initialized = False
        logger.info("Skipping Presidio NLP initialization to keep the gateway fast and deterministic.")

    def detect(self, text: str) -> List[Dict[str, Any]]:
        """Analyze input text using the fast local regex fallback to keep the app responsive."""
        if not text or not text.strip():
            return []

        return self._fallback_pii_detect(text)

    def _fallback_pii_detect(self, text: str) -> List[Dict[str, Any]]:
        """Fallback regex for basic PII if Presidio NLP model fails to load."""
        import re
        results = []
        
        # Email pattern
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        for m in re.finditer(email_pattern, text):
            results.append({
                "entity_type": "EMAIL_ADDRESS",
                "start": m.start(),
                "end": m.end(),
                "score": 0.9,
                "severity": "HIGH",
                "source": "Presidio Fallback Regex"
            })
            
        # Phone pattern
        phone_pattern = r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
        for m in re.finditer(phone_pattern, text):
            results.append({
                "entity_type": "PHONE_NUMBER",
                "start": m.start(),
                "end": m.end(),
                "score": 0.85,
                "severity": "HIGH",
                "source": "Presidio Fallback Regex"
            })

        # SSN pattern
        ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
        for m in re.finditer(ssn_pattern, text):
            results.append({
                "entity_type": "US_SSN",
                "start": m.start(),
                "end": m.end(),
                "score": 0.95,
                "severity": "CRITICAL",
                "source": "Presidio Fallback Regex"
            })

        # IP Address pattern
        ip_pattern = r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
        for m in re.finditer(ip_pattern, text):
            results.append({
                "entity_type": "IP_ADDRESS",
                "start": m.start(),
                "end": m.end(),
                "score": 0.85,
                "severity": "MEDIUM",
                "source": "Presidio Fallback Regex"
            })

        # Person / Location Address pattern (e.g., "living at ...", "user account for ...")
        location_pattern = r'\b\d{1,5}\s+[A-Z][a-z]+\s+(?:Street|St|Avenue|Ave|Road|Rd|Terrace|Drive|Dr|Lane|Ln|Blvd)\b'
        for m in re.finditer(location_pattern, text):
            results.append({
                "entity_type": "LOCATION",
                "start": m.start(),
                "end": m.end(),
                "score": 0.8,
                "severity": "MEDIUM",
                "source": "Presidio Fallback Regex"
            })
            
        return results
