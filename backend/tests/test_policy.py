from app.policy.policy_engine import PolicyEngine


def test_policy_allow_safe():
    policy = PolicyEngine()
    detection_result = {
        "is_sensitive": False,
        "entities": [],
        "categories": [],
        "highest_severity": "LOW"
    }
    decision = policy.evaluate(detection_result)
    assert decision["decision"] == "ALLOW"
    assert decision["risk_level"] == "LOW"


def test_policy_block_credential():
    policy = PolicyEngine()
    detection_result = {
        "is_sensitive": True,
        "entities": [{"entity_type": "API_KEY", "severity": "CRITICAL", "source": "Regex"}],
        "categories": ["API_KEY"],
        "highest_severity": "CRITICAL"
    }
    decision = policy.evaluate(detection_result)
    assert decision["decision"] == "BLOCK"
    assert decision["risk_level"] == "CRITICAL"


def test_policy_block_confidential_project():
    policy = PolicyEngine()
    detection_result = {
        "is_sensitive": True,
        "entities": [{"entity_type": "INTERNAL_PROJECT_NAME", "severity": "HIGH", "source": "Confidential"}],
        "categories": ["INTERNAL_PROJECT_NAME"],
        "highest_severity": "HIGH"
    }
    decision = policy.evaluate(detection_result)
    assert decision["decision"] == "BLOCK"
    assert decision["risk_level"] == "HIGH"
