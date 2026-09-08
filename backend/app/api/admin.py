import json
import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database.db import get_db
from app.database.models import AuditLog

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["Admin Dashboard"])


@router.get("/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    Returns aggregated analytics and summary statistics for the Admin Dashboard.
    """
    try:
        total_requests = db.query(AuditLog).count()
        allowed_requests = db.query(AuditLog).filter(AuditLog.policy_decision == "ALLOW").count()
        blocked_requests = db.query(AuditLog).filter(AuditLog.policy_decision == "BLOCK").count()
        sensitive_requests = db.query(AuditLog).filter(AuditLog.is_sensitive == True).count()

        block_rate = round((blocked_requests / total_requests * 100), 1) if total_requests > 0 else 0.0

        # Aggregate category counts
        category_counts = {}
        all_logs = db.query(AuditLog.detected_entities, AuditLog.risk_level).all()

        risk_level_counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}

        for entities_json, risk in all_logs:
            if risk in risk_level_counts:
                risk_level_counts[risk] += 1

            if entities_json:
                try:
                    cats = json.loads(entities_json)
                    for cat in cats:
                        category_counts[cat] = category_counts.get(cat, 0) + 1
                except Exception:
                    pass

        return {
            "summary": {
                "total_requests": total_requests,
                "allowed_requests": allowed_requests,
                "blocked_requests": blocked_requests,
                "sensitive_requests": sensitive_requests,
                "block_rate_percent": block_rate
            },
            "category_counts": category_counts,
            "risk_level_counts": risk_level_counts
        }
    except Exception as e:
        logger.error(f"Error compiling admin stats: {e}")
        return {
            "summary": {
                "total_requests": 0,
                "allowed_requests": 0,
                "blocked_requests": 0,
                "sensitive_requests": 0,
                "block_rate_percent": 0.0
            },
            "category_counts": {},
            "risk_level_counts": {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
        }


@router.get("/logs")
def get_audit_logs(
    limit: int = Query(50, ge=1, le=500),
    decision: Optional[str] = None,
    risk_level: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Returns recent audit logs with optional filtering by decision (ALLOW/BLOCK) or risk level.
    """
    try:
        query = db.query(AuditLog)
        
        if decision:
            query = query.filter(AuditLog.policy_decision == decision.upper())
        if risk_level:
            query = query.filter(AuditLog.risk_level == risk_level.upper())

        logs = query.order_by(desc(AuditLog.timestamp)).limit(limit).all()
        return [log.to_dict() for log in logs]
    except Exception as e:
        logger.error(f"Error fetching audit logs: {e}")
        return []
