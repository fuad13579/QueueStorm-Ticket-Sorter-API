from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# Confirm the health endpoint returns the expected status payload.
def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


# Verify that a wrong-recipient transfer is classified as a high-severity dispute.
def test_wrong_transfer():
    response = client.post(
        "/sort-ticket",
        json={
            "ticket_id": "T-001",
            "message": "I sent 3000 to wrong number",
        },
    )
    data = response.json()
    assert response.status_code == 200
    assert data["case_type"] == "wrong_transfer"
    assert data["severity"] == "high"


# Verify that a failed payment with a deducted balance routes to payments ops.
def test_payment_failed():
    response = client.post(
        "/sort-ticket",
        json={
            "ticket_id": "T-002",
            "message": "Payment failed but balance deducted",
        },
    )
    data = response.json()
    assert data["case_type"] == "payment_failed"
    assert data["severity"] == "high"


# Verify that OTP requests are treated as phishing and escalated immediately.
def test_phishing():
    response = client.post(
        "/sort-ticket",
        json={
            "ticket_id": "T-003",
            "message": "Someone called asking my OTP, is that bKash?",
        },
    )
    data = response.json()
    assert data["case_type"] == "phishing_or_social_engineering"
    assert data["severity"] == "critical"
    assert data["human_review_required"] is True


# Verify that a plain refund request stays low severity by default.
def test_refund():
    response = client.post(
        "/sort-ticket",
        json={
            "ticket_id": "T-004",
            "message": "Please refund my last transaction, I changed my mind",
        },
    )
    data = response.json()
    assert data["case_type"] == "refund_request"
    assert data["severity"] == "low"


# Verify that unrelated app issues fall back to the other category.
def test_other():
    response = client.post(
        "/sort-ticket",
        json={
            "ticket_id": "T-005",
            "message": "App crashed when I opened it",
        },
    )
    data = response.json()
    assert data["case_type"] == "other"
    assert data["severity"] == "low"