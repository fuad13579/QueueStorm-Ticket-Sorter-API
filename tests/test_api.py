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


# --- Edge cases below this line ---


# Whitespace and casing should not affect classification of a wrong-number complaint.
def test_wrong_transfer_uppercase_and_whitespace():
    response = client.post(
        "/sort-ticket",
        json={
            "ticket_id": "T-101",
            "message": "   I MISTAKENLY SENT 2500 TAKA TO THE WRONG NUMBER   ",
        },
    )
    data = response.json()
    assert response.status_code == 200
    assert data["case_type"] == "wrong_transfer"
    assert data["severity"] == "high"
    assert data["department"] == "dispute_resolution"


# When the message lacks a numeric amount, the summary should still be well-formed.
def test_wrong_transfer_without_amount():
    response = client.post(
        "/sort-ticket",
        json={
            "ticket_id": "T-102",
            "message": "I sent money to the wrong recipient, please help.",
        },
    )
    data = response.json()
    assert data["case_type"] == "wrong_transfer"
    assert data["severity"] == "high"
    assert "wrong" in data["agent_summary"].lower()


# "money deducted" without the word "payment" must still trip the payment-failed rules.
def test_payment_failed_synonym():
    response = client.post(
        "/sort-ticket",
        json={
            "ticket_id": "T-103",
            "message": "My transaction failed and money was deducted from my account",
        },
    )
    data = response.json()
    assert data["case_type"] == "payment_failed"
    assert data["severity"] == "high"
    assert data["department"] == "payments_ops"


# Phishing signals must override other intents (e.g. "refund" + "OTP" -> phishing, critical).
def test_phishing_priority_over_refund():
    response = client.post(
        "/sort-ticket",
        json={
            "ticket_id": "T-104",
            "message": "I want a refund, the agent asked for my OTP and pin",
        },
    )
    data = response.json()
    assert data["case_type"] == "phishing_or_social_engineering"
    assert data["severity"] == "critical"
    assert data["department"] == "fraud_risk"
    assert data["human_review_required"] is True


# PIN-only mentions should still be flagged as phishing even if OTP is absent.
def test_phishing_pin_only():
    response = client.post(
        "/sort-ticket",
        json={
            "ticket_id": "T-105",
            "message": "Someone asked for my pin over a call, should I share it?",
        },
    )
    data = response.json()
    assert data["case_type"] == "phishing_or_social_engineering"
    assert data["severity"] == "critical"
    assert data["human_review_required"] is True


# Refunds described as a billing dispute should route to dispute_resolution.
def test_refund_dispute_escalation():
    response = client.post(
        "/sort-ticket",
        json={
            "ticket_id": "T-106",
            "message": "Refund this charge please, this is a dispute and feels fraudulent",
        },
    )
    data = response.json()
    assert data["case_type"] == "refund_request"
    assert data["department"] == "dispute_resolution"


# Urgent refund asks should bump severity from low to medium while keeping the same department.
def test_refund_urgent_severity_bump():
    response = client.post(
        "/sort-ticket",
        json={
            "ticket_id": "T-107",
            "message": "Please refund me ASAP, I need the money back urgently",
        },
    )
    data = response.json()
    assert data["case_type"] == "refund_request"
    assert data["severity"] == "medium"


# Bengali-language complaints with English keyword "wrong number" should still classify.
def test_bengali_wrong_transfer():
    response = client.post(
        "/sort-ticket",
        json={
            "ticket_id": "T-108",
            "locale": "bn",
            "message": "আমি ভুল নম্বরে টাকা পাঠিয়ে দিয়েছি, wrong number",
        },
    )
    data = response.json()
    assert data["case_type"] == "wrong_transfer"
    assert data["severity"] == "high"


# Mixed locale complaint about a failed transaction should still classify.
def test_mixed_locale_payment_failed():
    response = client.post(
        "/sort-ticket",
        json={
            "ticket_id": "T-109",
            "locale": "mixed",
            "message": "Payment failed হয়েছে কিন্তু balance deducted হয়েছে",
        },
    )
    data = response.json()
    assert data["case_type"] == "payment_failed"
    assert data["severity"] == "high"


# --- Bengali / Banglish edge cases (no English keywords in the message) ---


# Pure Bengali wrong-transfer complaint should classify via Bengali keyword.
def test_bengali_only_wrong_transfer():
    response = client.post(
        "/sort-ticket",
        json={
            "ticket_id": "T-201",
            "locale": "bn",
            "message": "আমি ভুল নম্বরে ১৫০০ টাকা পাঠিয়ে দিয়েছি",
        },
    )
    data = response.json()
    assert data["case_type"] == "wrong_transfer"
    assert data["severity"] == "high"
    assert data["department"] == "dispute_resolution"


# Banglish wrong-transfer complaint (Latin script but Bengali meaning).
def test_banglisht_wrong_transfer():
    response = client.post(
        "/sort-ticket",
        json={
            "ticket_id": "T-202",
            "locale": "bn",
            "message": "Ami bhul number e taka pathiye diyechi",
        },
    )
    data = response.json()
    assert data["case_type"] == "wrong_transfer"
    assert data["severity"] == "high"


# Pure Bengali payment-failed complaint with "টাকা কেটে নিয়েছে".
def test_bengali_only_payment_failed():
    response = client.post(
        "/sort-ticket",
        json={
            "ticket_id": "T-203",
            "locale": "bn",
            "message": "পেমেন্ট ব্যর্থ হয়েছে কিন্তু টাকা কেটে নিয়েছে",
        },
    )
    data = response.json()
    assert data["case_type"] == "payment_failed"
    assert data["severity"] == "high"
    assert data["department"] == "payments_ops"


# Banglish payment-failed complaint.
def test_banglish_payment_failed():
    response = client.post(
        "/sort-ticket",
        json={
            "ticket_id": "T-204",
            "locale": "mixed",
            "message": "Payment failed hoyeche kintu balance kete niyeche",
        },
    )
    data = response.json()
    assert data["case_type"] == "payment_failed"
    assert data["severity"] == "high"


# Pure Bengali refund request.
def test_bengali_only_refund():
    response = client.post(
        "/sort-ticket",
        json={
            "ticket_id": "T-205",
            "locale": "bn",
            "message": "আমি রিফান্ড চাই, টাকা ফেরত দিন",
        },
    )
    data = response.json()
    assert data["case_type"] == "refund_request"
    assert data["severity"] == "low"
    assert data["department"] == "customer_support"


# Banglish refund request.
def test_banglish_refund():
    response = client.post(
        "/sort-ticket",
        json={
            "ticket_id": "T-206",
            "locale": "mixed",
            "message": "Refund kore din, ami taka ferot chai",
        },
    )
    data = response.json()
    assert data["case_type"] == "refund_request"
    assert data["severity"] == "low"


# Pure Bengali phishing complaint with "পিন দিয়ে দিন".
def test_bengali_only_phishing():
    response = client.post(
        "/sort-ticket",
        json={
            "ticket_id": "T-207",
            "locale": "bn",
            "message": "একজন কল করে আমার পিন দিয়ে দিতে বলেছে",
        },
    )
    data = response.json()
    assert data["case_type"] == "phishing_or_social_engineering"
    assert data["severity"] == "critical"
    assert data["department"] == "fraud_risk"
    assert data["human_review_required"] is True


# Banglish phishing complaint asking for OTP.
def test_banglish_phishing():
    response = client.post(
        "/sort-ticket",
        json={
            "ticket_id": "T-208",
            "locale": "mixed",
            "message": "Ekjon OTP niye niye call kore, scam kore",
        },
    )
    data = response.json()
    assert data["case_type"] == "phishing_or_social_engineering"
    assert data["severity"] == "critical"
    assert data["human_review_required"] is True


# An empty message must be rejected with a 422 validation error.
def test_empty_message_rejected():
    response = client.post(
        "/sort-ticket",
        json={"ticket_id": "T-110", "message": ""},
    )
    assert response.status_code == 422


# Missing required fields should surface a 422 from Pydantic.
def test_missing_required_fields():
    response = client.post("/sort-ticket", json={"ticket_id": "T-111"})
    assert response.status_code == 422


# The response must echo the ticket_id, return a valid confidence, and never ask for secrets.
def test_safety_rule_no_secret_requests_in_summary():
    forbidden = ["pin", "otp", "password", "card number", "cvv"]
    messages = [
        "I sent 3000 to wrong number",
        "Payment failed but balance deducted",
        "Someone called asking my OTP, is that bKash?",
        "Please refund my last transaction, I changed my mind",
        "App crashed when I opened it",
        "Phishing call asking for my password",
        "Refund please, the merchant charged me twice",
    ]
    for i, msg in enumerate(messages):
        response = client.post(
            "/sort-ticket",
            json={"ticket_id": f"T-SAFETY-{i}", "message": msg},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["ticket_id"] == f"T-SAFETY-{i}"
        assert 0.0 <= payload["confidence"] <= 1.0
        summary_lower = payload["agent_summary"].lower()
        asks_for_secret = "share" in summary_lower and any(
            token in summary_lower for token in forbidden
        )
        assert not asks_for_secret


# Wrong-channel combinations should not affect the classification outcome.
def test_channel_value_does_not_affect_classification():
    for channel in ["app", "sms", "call_center", "merchant_portal"]:
        response = client.post(
            "/sort-ticket",
            json={
                "ticket_id": f"T-CH-{channel}",
                "channel": channel,
                "message": "I sent 3000 to wrong number",
            },
        )
        data = response.json()
        assert response.status_code == 200
        assert data["case_type"] == "wrong_transfer"
        assert data["severity"] == "high"


# Bare complaints with no matching keyword must fall back to the "other" bucket.
def test_fallback_other_for_unrelated_message():
    response = client.post(
        "/sort-ticket",
        json={
            "ticket_id": "T-150",
            "message": "I cannot login to the app since this morning",
        },
    )
    data = response.json()
    assert data["case_type"] == "other"
    assert data["severity"] == "low"
    assert data["department"] == "customer_support"