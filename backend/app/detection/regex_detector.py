import re
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Configurable list of custom secret patterns
# Format: (entity_type, regex_pattern, severity_level, description)
SENSITIVE_PATTERNS = [
    (
        "API_KEY",
        r'AKIA[0-9A-Z]{16}',
        "CRITICAL",
        "AWS Access Key ID"
    ),
    (
        "API_KEY",
        r'sk-(?:proj-)?[a-zA-Z0-9_\-]{20,}',
        "CRITICAL",
        "OpenAI API Key"
    ),
    (
        "API_KEY",
        r'(?i)(?:api[_-]?key|access[_-]?key|secret[_-]?key)\s*[:=]\s*["\']?([a-zA-Z0-9_\-]{16,})["\']?',
        "CRITICAL",
        "Generic API / Secret Key Assignment"
    ),
    (
        "PASSWORD",
        r'(?i)(?:password|passwd|pwd)\s*[:=]\s*["\']?(\S{4,})["\']?',
        "CRITICAL",
        "Hardcoded Password Assignment"
    ),
    (
        "ACCESS_TOKEN",
        r'Bearer\s+eyJ[a-zA-Z0-9_\-\.]+\.[a-zA-Z0-9_\-\.]+',
        "CRITICAL",
        "JWT Bearer Access Token"
    ),
    (
        "PRIVATE_KEY",
        r'-----BEGIN (?:[A-Z0-9\s]+)?KEY-----',
        "CRITICAL",
        "Cryptographic Private Key Header"
    ),
    (
        "DATABASE_CONNECTION",
        r'(?i)(?:mongodb(?:\+srv)?|postgres|postgresql|mysql|oracle):\/\/[a-zA-Z0-9_%:]+@[a-zA-Z0-9.-]+',
        "CRITICAL",
        "Database Connection String with Credentials"
    ),
    (
        "INTERNAL_EMPLOYEE_ID",
        r'(?i)\bEMP[-_]?\d{4,6}\b',
        "HIGH",
        "Internal Employee Identifier"
    ),
    (
        "CONFIDENTIAL_MARKER",
        r'(?i)\b(?:STRICTLY CONFIDENTIAL|INTERNAL ONLY|COMPANY PROPRIETARY|DO NOT DISTRIBUTE)\b',
        "HIGH",
        "Enterprise Confidentiality Classification Marker"
    ),
]


class RegexDetector:
    """
    Custom Rule/Regex-based Detector for high-risk technical secrets, credentials, API keys, 
    and enterprise internal markers that general NLP detectors may miss.
    """
    def __init__(self):
        self.compiled_patterns = []
        for entity_type, pattern, severity, desc in SENSITIVE_PATTERNS:
            try:
                compiled = re.compile(pattern, re.IGNORECASE)
                self.compiled_patterns.append((entity_type, compiled, severity, desc))
            except re.error as err:
                logger.error(f"Failed to compile regex pattern for {entity_type}: {err}")

    def detect(self, text: str) -> List[Dict[str, Any]]:
        """Scan input text against all sensitive regex rules."""
        if not text or not text.strip():
            return []

        results = []
        for entity_type, pattern, severity, desc in self.compiled_patterns:
            for match in pattern.finditer(text):
                results.append({
                    "entity_type": entity_type,
                    "start": match.start(),
                    "end": match.end(),
                    "score": 1.0,
                    "severity": severity,
                    "source": "Regex Rule Engine",
                    "description": desc
                })

        return results
