import logging
from typing import Dict, Any
from app.config import BLOCK_ON_PII, BLOCK_ON_CREDENTIALS, BLOCK_ON_SECRETS, BLOCK_ON_CONFIDENTIAL

logger = logging.getLogger(__name__)


class PolicyEngine:
    """
    Policy Enforcement Engine for Enterprise GenAI Security Gateway.
    Evaluates unified detection findings, assesses risk level, and determines security decision (ALLOW vs BLOCK).
    
    Policy Rules:
      1. LOW Risk (No sensitive data detected):
         -> Decision: ALLOW
         -> Action: ALLOWED_FORWARDED_TO_LLM
      2. CRITICAL Risk (Passwords, API Keys, DB URLs, Private Keys, Secret Configs):
         -> Decision: BLOCK (if BLOCK_ON_CREDENTIALS / BLOCK_ON_SECRETS is True)
         -> Action: BLOCKED_CREDENTIALS_DETECTED
      3. HIGH Risk (Emails, Phones, Confidential Markers, Internal Project Names, Internal Infrastructure):
         -> Decision: BLOCK (if BLOCK_ON_PII / BLOCK_ON_CONFIDENTIAL is True)
         -> Action: BLOCKED_CONFIDENTIAL_OR_PII_DETECTED
      4. MEDIUM Risk (General PII like Names, IP Addresses, Code snippets):
         -> Decision: BLOCK (if configured to enforce strict privacy policy)
         -> Action: BLOCKED_SENSITIVE_DATA_DETECTED
    """
    def __init__(self):
        self.block_pii = BLOCK_ON_PII
        self.block_credentials = BLOCK_ON_CREDENTIALS
        self.block_secrets = BLOCK_ON_SECRETS
        self.block_confidential = BLOCK_ON_CONFIDENTIAL

    def evaluate(self, detection_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate sensitive data detection results and enforce security policies.
        Returns policy evaluation dictionary with decision, risk_level, reason, and action.
        """
        is_sensitive = detection_result.get("is_sensitive", False)
        entities = detection_result.get("entities", [])
        categories = detection_result.get("categories", [])
        highest_severity = detection_result.get("highest_severity", "LOW")

        # 1. Default ALLOW state for safe prompts
        if not is_sensitive or len(entities) == 0:
            return {
                "decision": "ALLOW",
                "risk_level": "LOW",
                "reason": "Prompt passed security evaluation. No sensitive data detected.",
                "action": "ALLOWED_FORWARDED_TO_LLM"
            }

        cat_str = ", ".join(categories) if categories else "Sensitive Information"

        # Check entity categories against policy rules
        is_credential_or_secret = any(
            e["severity"] == "CRITICAL" or e["entity_type"] in [
                "API_KEY", "PASSWORD", "ACCESS_TOKEN", "PRIVATE_KEY", "DATABASE_CONNECTION", "DATABASE_CONNECTION_CONFIG"
            ] for e in entities
        )

        is_confidential = any(
            e["entity_type"] in [
                "CONFIDENTIAL_MARKER", "INTERNAL_PROJECT_NAME", "INTERNAL_INFRASTRUCTURE_URL",
                "INTERNAL_DOMAIN", "INTERNAL_REPOSITORY", "INTERNAL_SERVICE_NAME", "INTERNAL_EMPLOYEE_ID"
            ] for e in entities
        )

        is_pii = any(
            e["entity_type"] in [
                "EMAIL_ADDRESS", "PHONE_NUMBER", "US_SSN", "CREDIT_CARD", "IBAN_CODE", "PERSON", "IP_ADDRESS"
            ] for e in entities
        )

        # Enforce blocking decisions according to policy configuration
        should_block = False
        action = "BLOCKED_SENSITIVE_DATA_DETECTED"
        reason = f"Security Violation: Sensitive data detected ({cat_str}). Request blocked by enterprise policy."

        if is_credential_or_secret and (self.block_credentials or self.block_secrets):
            should_block = True
            action = "BLOCKED_CREDENTIALS_OR_SECRETS"
            reason = f"Critical Security Violation: Secrets or credentials detected ({cat_str}). External LLM blocked."

        elif is_confidential and self.block_confidential:
            should_block = True
            action = "BLOCKED_ENTERPRISE_CONFIDENTIAL_DATA"
            reason = f"Enterprise Policy Violation: Internal confidential information detected ({cat_str}). External LLM blocked."

        elif is_pii and self.block_pii:
            should_block = True
            action = "BLOCKED_PII_DATA"
            reason = f"Privacy Violation: Personally Identifiable Information (PII) detected ({cat_str}). Request blocked."

        elif highest_severity in ["HIGH", "CRITICAL", "MEDIUM"]:
            should_block = True
            action = "BLOCKED_SENSITIVE_DATA_DETECTED"
            reason = f"Security Policy Violation: Sensitive indicators detected ({cat_str}). Request blocked."

        if should_block:
            logger.warning(f"[POLICY_BLOCK] Decision=BLOCK RiskLevel={highest_severity} Categories={categories}")
            return {
                "decision": "BLOCK",
                "risk_level": highest_severity,
                "reason": reason,
                "action": action
            }
        else:
            logger.info(f"[POLICY_ALLOW] Prompt allowed under current policy settings.")
            return {
                "decision": "ALLOW",
                "risk_level": highest_severity,
                "reason": "Sensitive indicators noted but allowed by current risk policy configuration.",
                "action": "ALLOWED_UNDER_POLICY"
            }
