import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database.db import init_db
from app.llm.llm_client import LLMClient

# Initialize database tables for pytest context
init_db()

client = TestClient(app)


def test_api_safe_prompt_flow():
    """Test 1 — Safe prompt: Expect ALLOW."""
    response = client.post(
        "/api/chat",
        json={"prompt": "Explain the difference between REST and SOAP.", "user_id": "test_user_01"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "ALLOW"
    assert data["llm_called"] is True


def test_api_pii_prompt_flow():
    """Test 2 — PII prompt: Expect PII detected and blocked."""
    response = client.post(
        "/api/chat",
        json={"prompt": "My email is test@example.com.", "user_id": "test_user_02"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_sensitive"] is True
    assert "EMAIL_ADDRESS" in data["categories"]
    assert data["decision"] == "BLOCK"
    assert data["llm_called"] is False


def test_api_credential_blocked_flow():
    """Test 3 — Credential prompt: Expect BLOCK and llm_called = False."""
    response = client.post(
        "/api/chat",
        json={"prompt": "My AWS access key is AKIAIOSFODNN7EXAMPLE.", "user_id": "test_user_03"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "BLOCK"
    assert data["llm_called"] is False
    assert "BLOCKED BY SECURITY GATEWAY" in data["response"]


def test_api_confidential_project_blocked_flow():
    """Test 4 — Confidential project info: Expect BLOCK and llm_called = False."""
    prompt = "This is a confidential internal architecture document for Project Phoenix."
    response = client.post(
        "/api/chat",
        json={"prompt": prompt, "user_id": "test_user_04"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "BLOCK"
    assert data["llm_called"] is False
    assert any(cat in ["CONFIDENTIAL_MARKER", "INTERNAL_PROJECT_NAME"] for cat in data["categories"])


def test_api_internal_url_detection_flow():
    """Test 5 — Internal URL prompt: Expect internal info detected and blocked."""
    prompt = "The internal API is available at https://api.internal.company.com/."
    response = client.post(
        "/api/chat",
        json={"prompt": prompt, "user_id": "test_user_05"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "BLOCK"
    assert data["llm_called"] is False
    assert any(cat in ["INTERNAL_INFRASTRUCTURE_URL", "INTERNAL_DOMAIN"] for cat in data["categories"])


def test_missing_llm_api_key_error():
    """Test 6 — Missing LLM API key returns clear error without fallback to mock."""
    llm = LLMClient()
    llm.api_key = ""  # Simulate missing API key
    res = llm.generate_response("Explain REST API")
    assert res["success"] is False
    assert "LLM Configuration Error" in res["text"] or "missing" in res["text"]
    assert res.get("provider") != "Mock LLM Engine"


def test_audit_log_llm_called_false_for_blocked():
    """Test 7 — Audit log: Verify llm_called = False for blocked requests."""
    response = client.post(
        "/api/chat",
        json={"prompt": "password=SecretPassword123!", "user_id": "test_user_07"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] == "BLOCK"
    assert data["llm_called"] is False

    # Check recent audit logs API
    logs_res = client.get("/api/admin/logs?limit=5")
    assert logs_res.status_code == 200
    logs = logs_res.json()
    matching_log = next((l for l in logs if l["request_id"] == data["request_id"]), None)
    assert matching_log is not None
    assert matching_log["llm_called"] is False
    assert matching_log["policy_decision"] == "BLOCK"


def test_standalone_analyze_api():
    """Test 8 — Standalone /api/analyze endpoint."""
    response = client.post(
        "/api/analyze",
        json={"prompt": "Strictly Confidential internal roadmap for Project Atlas"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_sensitive"] is True
    assert data["policy_decision"] == "BLOCK"
    assert data["llm_called"] is False
    assert "redacted_snippet" in data
