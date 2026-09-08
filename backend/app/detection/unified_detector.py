import logging
from typing import List, Dict, Any
from app.detection.presidio_detector import PresidioDetector
from app.detection.regex_detector import RegexDetector
from app.detection.confidential_detector import ConfidentialDetector

logger = logging.getLogger(__name__)


class UnifiedDetector:
    """
    Unified Sensitive Data Detection Engine.
    Combines:
      1. Microsoft Presidio NLP Analyzer (Standard PII: Email, Phone, SSN, Credit Card, Person, IP, Location)
      2. Custom Regex Rule Engine (Technical Secrets: AWS Keys, OpenAI Keys, Passwords, Access Tokens, DB URIs)
      3. Enterprise Confidentiality Detector (Org-specific: Confidential Markers, Project Names, Internal Infrastructure, Source Code)
      
    Provides structured findings, highest risk calculation, and safe privacy-preserving prompt redaction.
    """
    def __init__(self):
        self.presidio = PresidioDetector()
        self.regex = RegexDetector()
        self.confidential = ConfidentialDetector()

    def analyze(self, prompt: str) -> Dict[str, Any]:
        """
        Runs complete sensitivity analysis across all detection layers.
        
        Returns structured dictionary:
        {
            "is_sensitive": True/False,
            "detected_count": int,
            "entities": [...],
            "categories": [...],
            "highest_severity": "LOW" | "MEDIUM" | "HIGH" | "CRITICAL",
            "redacted_snippet": str
        }
        """
        if not prompt or not prompt.strip():
            return {
                "is_sensitive": False,
                "detected_count": 0,
                "entities": [],
                "categories": [],
                "highest_severity": "LOW",
                "redacted_snippet": ""
            }

        # 1. Run Microsoft Presidio NLP detection
        presidio_findings = self.presidio.detect(prompt)
        
        # 2. Run Custom Regex Secrets detection
        regex_findings = self.regex.detect(prompt)

        # 3. Run Enterprise Confidentiality & Internal Data detection
        confidential_findings = self.confidential.detect(prompt)

        # 4. Combine findings from all 3 detection layers
        raw_entities = presidio_findings + regex_findings + confidential_findings

        # Sort by start character index
        raw_entities.sort(key=lambda x: x["start"])

        # Filter overlapping matches, prioritizing higher risk severity
        deduplicated = self._deduplicate_findings(raw_entities)

        # 5. Extract unique entity categories & highest risk level
        categories = list(set([e["entity_type"] for e in deduplicated]))
        highest_severity = self._calculate_highest_severity(deduplicated)
        is_sensitive = len(deduplicated) > 0

        # 6. Generate safe redacted prompt snippet (masking sensitive text spans)
        redacted_snippet = self._redact_prompt(prompt, deduplicated)

        # Sanitize entity objects so raw secret text is NEVER logged or stored
        sanitized_entities = []
        for e in deduplicated:
            sanitized_entities.append({
                "entity_type": e["entity_type"],
                "severity": e["severity"],
                "source": e["source"],
                "score": e.get("score", 1.0),
                "description": e.get("description", e["entity_type"])
            })

        return {
            "is_sensitive": is_sensitive,
            "detected_count": len(sanitized_entities),
            "entities": sanitized_entities,
            "categories": categories,
            "highest_severity": highest_severity,
            "redacted_snippet": redacted_snippet
        }

    def _deduplicate_findings(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove overlapping detection spans, prioritizing higher severity levels."""
        if not findings:
            return []

        severity_rank = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
        
        result = []
        for current in findings:
            overlap = False
            for i, existing in enumerate(result):
                # Check for overlap in character indices [start, end]
                if max(current["start"], existing["start"]) < min(current["end"], existing["end"]):
                    overlap = True
                    # Replace if current has higher severity
                    if severity_rank.get(current["severity"], 1) > severity_rank.get(existing["severity"], 1):
                        result[i] = current
                    break
            if not overlap:
                result.append(current)
        return result

    def _calculate_highest_severity(self, entities: List[Dict[str, Any]]) -> str:
        """Determines the maximum risk severity level among all detected entities."""
        if not entities:
            return "LOW"
            
        severity_rank = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
        highest = "LOW"
        highest_val = 1

        for e in entities:
            sev = e.get("severity", "LOW")
            val = severity_rank.get(sev, 1)
            if val > highest_val:
                highest_val = val
                highest = sev

        return highest

    def _redact_prompt(self, prompt: str, entities: List[Dict[str, Any]]) -> str:
        """Replace sensitive string spans with placeholders like <EMAIL_ADDRESS> or <API_KEY>."""
        if not entities:
            return prompt[:200] + "..." if len(prompt) > 200 else prompt

        # Re-sort descending by start index to replace from right to left without shifting left indices
        sorted_entities = sorted(entities, key=lambda x: x["start"], reverse=True)
        redacted = prompt

        for e in sorted_entities:
            start = e["start"]
            end = e["end"]
            replacement = f"<{e['entity_type']}>"
            redacted = redacted[:start] + replacement + redacted[end:]

        if len(redacted) > 200:
            return redacted[:200] + "..."
        return redacted
