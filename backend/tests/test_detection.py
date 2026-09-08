from app.detection.presidio_detector import PresidioDetector
from app.detection.regex_detector import RegexDetector
from app.detection.confidential_detector import ConfidentialDetector
from app.detection.unified_detector import UnifiedDetector


def test_safe_prompt_detection():
    detector = UnifiedDetector()
    res = detector.analyze("Explain the difference between REST and SOAP.")
    assert res["is_sensitive"] is False
    assert len(res["entities"]) == 0
    assert res["highest_severity"] == "LOW"


def test_email_pii_detection():
    detector = UnifiedDetector()
    res = detector.analyze("My email is test@example.com.")
    assert res["is_sensitive"] is True
    assert "EMAIL_ADDRESS" in res["categories"]


def test_phone_pii_detection():
    detector = UnifiedDetector()
    res = detector.analyze("Please call customer support at 555-019-2834 immediately.")
    assert res["is_sensitive"] is True
    assert "PHONE_NUMBER" in res["categories"]


def test_credential_regex_detection():
    detector = UnifiedDetector()
    res = detector.analyze("My AWS access key is AKIAIOSFODNN7EXAMPLE for cloud deployment.")
    assert res["is_sensitive"] is True
    assert "API_KEY" in res["categories"]
    assert res["highest_severity"] == "CRITICAL"


def test_confidential_project_detection():
    detector = UnifiedDetector()
    res = detector.analyze("This is a confidential internal architecture document for Project Phoenix.")
    assert res["is_sensitive"] is True
    assert any(cat in ["CONFIDENTIAL_MARKER", "INTERNAL_PROJECT_NAME"] for cat in res["categories"])
    assert res["highest_severity"] in ["HIGH", "CRITICAL"]


def test_internal_url_detection():
    detector = UnifiedDetector()
    res = detector.analyze("The internal API is available at https://api.internal.company.com/.")
    assert res["is_sensitive"] is True
    assert any(cat in ["INTERNAL_INFRASTRUCTURE_URL", "INTERNAL_DOMAIN"] for cat in res["categories"])
    assert res["highest_severity"] in ["HIGH", "CRITICAL"]
