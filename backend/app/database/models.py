from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, Text
from app.database.db import Base


class AuditLog(Base):
    """
    AuditLog table stores security gateway records for every prompt received.
    
    IMPORTANT SECURITY REQUIREMENT:
    Raw sensitive passwords, API keys, and secret tokens are NEVER stored in this database.
    Only redacted snippets, entity categories, risk levels, and decision outcomes are logged.
    """
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String(36), index=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    user_id = Column(String(100), default="employee_user", nullable=False)
    prompt_snippet = Column(Text, nullable=False)  # Redacted/truncated preview
    is_sensitive = Column(Boolean, default=False, nullable=False)
    detected_entities = Column(Text, nullable=False)  # JSON string array of detected entity types
    risk_level = Column(String(20), default="LOW", nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    policy_decision = Column(String(20), nullable=False)  # ALLOW, BLOCK
    action = Column(String(100), nullable=False)
    llm_called = Column(Boolean, default=False, nullable=False)  # Strictly MUST be False if BLOCKED
    response_status = Column(String(50), nullable=False)  # SUCCESS, BLOCKED, LLM_ERROR
    latency_ms = Column(Float, default=0.0, nullable=False)

    def to_dict(self):
        """Helper to convert AuditLog instance into a dict for API response."""
        return {
            "id": self.id,
            "request_id": self.request_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "user_id": self.user_id,
            "prompt_snippet": self.prompt_snippet,
            "is_sensitive": self.is_sensitive,
            "detected_entities": self.detected_entities,
            "risk_level": self.risk_level,
            "policy_decision": self.policy_decision,
            "action": self.action,
            "llm_called": self.llm_called,
            "response_status": self.response_status,
            "latency_ms": self.latency_ms
        }
