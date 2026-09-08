import re
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).resolve().parent / "confidential_patterns.json"


class ConfidentialDetector:
    """
    Enterprise Confidentiality & Internal Data Detector.
    Detects organization-specific sensitive information including:
      - Confidentiality classification markers (CONFIDENTIAL, INTERNAL USE ONLY, etc.)
      - Internal project code names (Project Phoenix, Project Atlas, etc.)
      - Internal infrastructure indicators (internal URLs, domains, repos, services)
      - Source code leaks & internal configuration snippets
    """
    def __init__(self, config_path: Path = CONFIG_PATH):
        self.compiled_rules = []
        self._load_patterns(config_path)

    def _load_patterns(self, config_path: Path):
        """Loads and compiles regex patterns from JSON configuration file."""
        try:
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # Parse all sections in JSON configuration
                sections = ["confidentiality_markers", "internal_projects", "internal_infrastructure", "source_code_indicators"]
                for section in sections:
                    for item in data.get(section, []):
                        pattern_str = item.get("pattern")
                        entity_type = item.get("entity_type", "CONFIDENTIAL_DATA")
                        severity = item.get("severity", "HIGH")
                        description = item.get("description", "Enterprise Internal Data")
                        
                        if pattern_str:
                            compiled = re.compile(pattern_str, re.IGNORECASE)
                            self.compiled_rules.append((entity_type, compiled, severity, description))

                logger.info(f"ConfidentialDetector loaded {len(self.compiled_rules)} custom enterprise rules from {config_path.name}")
            else:
                logger.warning(f"Confidential patterns file not found at {config_path}. Loading fallback default rules.")
                self._load_default_fallback_rules()
        except Exception as e:
            logger.error(f"Error loading confidential patterns JSON: {e}. Falling back to default rules.")
            self._load_default_fallback_rules()

    def _load_default_fallback_rules(self):
        """Fallback default rules if JSON configuration file fails to load."""
        defaults = [
            ("CONFIDENTIAL_MARKER", r'\b(?:STRICTLY CONFIDENTIAL|INTERNAL USE ONLY|COMPANY PROPRIETARY|RESTRICTED DATA|NOT FOR DISTRIBUTION)\b', "HIGH", "Enterprise Confidentiality Marker"),
            ("INTERNAL_PROJECT_NAME", r'\bProject\s+(?:Phoenix|Atlas|Titan|Apex)\b', "HIGH", "Internal Project Code Name"),
            ("INTERNAL_INFRASTRUCTURE_URL", r'https?://[a-zA-Z0-9.-]*internal[a-zA-Z0-9.-]*\.[a-zA-Z]{2,}(?:/[^\s]*)?', "HIGH", "Internal Network URL"),
            ("INTERNAL_DOMAIN", r'\b[a-zA-Z0-9._%+-]+\.(?:internal|corp|local)\b', "HIGH", "Internal Domain Name"),
            ("DATABASE_CONNECTION_CONFIG", r'(?:DB_PASSWORD|DATABASE_URL)\s*=\s*[\'"]?\S+[\'"]?', "CRITICAL", "Database Connection String Snippet")
        ]
        for entity_type, pattern, severity, desc in defaults:
            self.compiled_rules.append((entity_type, re.compile(pattern, re.IGNORECASE), severity, desc))

    def detect(self, text: str) -> List[Dict[str, Any]]:
        """
        Scans prompt text against all enterprise confidential data rules.
        Returns a list of structured findings.
        """
        if not text or not text.strip():
            return []

        results = []
        for entity_type, pattern, severity, desc in self.compiled_rules:
            for match in pattern.finditer(text):
                results.append({
                    "entity_type": entity_type,
                    "start": match.start(),
                    "end": match.end(),
                    "score": 1.0,
                    "severity": severity,
                    "source": "Enterprise Confidentiality Detector",
                    "description": desc
                })

        return results
