import time
import uuid
import json
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.database.models import AuditLog
from app.detection.unified_detector import UnifiedDetector
from app.policy.policy_engine import PolicyEngine
from app.llm.llm_client import LLMClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Security Gateway"])

# Global singleton instances of gateway modules for optimal performance
detector = UnifiedDetector()
policy_engine = PolicyEngine()
llm_client = LLMClient()


class ChatRequest(BaseModel):
    prompt: str = Field(..., description="The user input prompt to analyze and forward.")
    user_id: Optional[str] = Field("employee_user", description="Optional employee ID or username.")


class AnalyzeRequest(BaseModel):
    prompt: str = Field(..., description="The text prompt to inspect for sensitive information.")


@router.post("/chat")
def process_chat_prompt(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Main Security Gateway Chat Endpoint.
    
    Security Flow Pipeline:
    Employee / API Client
    → Security Gateway
    → Sensitive Data Detection (Presidio + Custom Regex + Enterprise Confidentiality)
    → Policy Engine (Risk Assessment)
    → ALLOW or BLOCK
        ALLOW -> Real External LLM -> Response
        BLOCK -> External LLM is NOT called
    Both → SQLite Audit Log -> Admin Dashboard
    """
    start_time = time.time()
    request_id = str(uuid.uuid4())
    user_prompt = request.prompt.strip()

    if not user_prompt:
        raise HTTPException(status_code=400, detail="Prompt cannot be empty.")

    logger.info(f"[GATEWAY_REQUEST] ID={request_id} User={request.user_id} Length={len(user_prompt)}")

    # Step 1: Multi-layer Sensitive Data Detection
    detection_res = detector.analyze(user_prompt)

    # Step 2: Policy Engine Evaluation
    policy_res = policy_engine.evaluate(detection_res)

    decision = policy_res["decision"]  # ALLOW or BLOCK
    risk_level = policy_res["risk_level"]
    
    llm_called = False
    llm_response_text = ""
    response_status = "BLOCKED"

    # Step 3: Conditional Real LLM Execution
    if decision == "ALLOW":
        # STRICT SECURITY GUARANTEE: External LLM is ONLY called when decision is ALLOW
        logger.info(f"[GATEWAY_DECISION] ALLOW -> Forwarding prompt ID={request_id} to Real External LLM.")
        llm_result = llm_client.generate_response(user_prompt)
        llm_called = bool(llm_result.get("success", False))
        llm_response_text = llm_result.get("text", "")
        response_status = "SUCCESS" if llm_called else "LLM_ERROR"
        if not llm_called:
            logger.warning(f"[GATEWAY_DECISION] ALLOW -> Real Groq call failed for prompt ID={request_id}. No local fallback was used.")
    else:
        # STRICT SECURITY GUARANTEE: External LLM is NEVER called when decision is BLOCK
        llm_called = False
        llm_response_text = f"BLOCKED BY SECURITY GATEWAY — {policy_res['reason']}"
        response_status = "BLOCKED"
        logger.warning(f"[GATEWAY_DECISION] BLOCK -> Prompt ID={request_id} rejected. External LLM was NOT called.")

    # Calculate total gateway latency
    latency_ms = round((time.time() - start_time) * 1000, 2)

    # Step 4: Audit Logging in SQLite (Store NO raw passwords, keys, or secrets)
    try:
        audit_entry = AuditLog(
            request_id=request_id,
            user_id=request.user_id,
            prompt_snippet=detection_res["redacted_snippet"],
            is_sensitive=detection_res["is_sensitive"],
            detected_entities=json.dumps(detection_res["categories"]),
            risk_level=risk_level,
            policy_decision=decision,
            action=policy_res["action"],
            llm_called=llm_called,
            response_status=response_status,
            latency_ms=latency_ms
        )
        db.add(audit_entry)
        db.commit()
        logger.info(f"[AUDIT_LOG_SAVED] Record created for request_id={request_id} llm_called={llm_called}")
    except Exception as db_err:
        db.rollback()
        logger.error(f"Failed to record audit log: {db_err}")

    # Return clean API response
    return {
        "request_id": request_id,
        "decision": decision,
        "risk_level": risk_level,
        "is_sensitive": detection_res["is_sensitive"],
        "categories": detection_res["categories"],
        "detected_entities": detection_res["entities"],
        "reason": policy_res["reason"],
        "llm_called": llm_called,
        "response": llm_response_text,
        "latency_ms": latency_ms
    }


@router.post("/analyze")
def analyze_text_prompt(request: AnalyzeRequest):
    """
    Standalone API Analysis Endpoint.
    Allows external applications to inspect text sensitivity, risk level, and policy decision
    WITHOUT invoking the external LLM.
    """
    start_time = time.time()
    user_prompt = request.prompt.strip()

    if not user_prompt:
        raise HTTPException(status_code=400, detail="Prompt cannot be empty.")

    # Run detection & policy evaluation without LLM invocation
    detection_res = detector.analyze(user_prompt)
    policy_res = policy_engine.evaluate(detection_res)
    latency_ms = round((time.time() - start_time) * 1000, 2)

    return {
        "is_sensitive": detection_res["is_sensitive"],
        "risk_level": policy_res["risk_level"],
        "policy_decision": policy_res["decision"],
        "reason": policy_res["reason"],
        "categories": detection_res["categories"],
        "detected_entities": detection_res["entities"],
        "redacted_snippet": detection_res["redacted_snippet"],
        "llm_called": False,
        "analysis_latency_ms": latency_ms
    }
