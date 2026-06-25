import re

from app.rules import CASE_KEYWORDS, DEFAULT_DEPARTMENT


def normalize_text(text: str) -> str:
    return " ".join(text.lower().strip().split())


def detect_case_type(message: str) -> tuple[str, float]:
    normalized = normalize_text(message)

    for keyword in CASE_KEYWORDS["phishing_or_social_engineering"]:
        if keyword in normalized:
            return "phishing_or_social_engineering", 0.95

    for keyword in CASE_KEYWORDS["wrong_transfer"]:
        if keyword in normalized:
            return "wrong_transfer", 0.90

    for keyword in CASE_KEYWORDS["payment_failed"]:
        if keyword in normalized:
            return "payment_failed", 0.90

    for keyword in CASE_KEYWORDS["refund_request"]:
        if keyword in normalized:
            return "refund_request", 0.85

    return "other", 0.50


def detect_severity(case_type: str, message: str) -> str:
    normalized = normalize_text(message)

    if case_type == "phishing_or_social_engineering":
        return "critical"

    if case_type in {"wrong_transfer", "payment_failed"}:
        return "high"

    if case_type == "refund_request":
        if "urgent" in normalized or "asap" in normalized:
            return "medium"
        return "low"

    return "low"


def detect_department(case_type: str, severity: str, message: str) -> str:
    if case_type == "refund_request":
        normalized = normalize_text(message)
        if "fraud" in normalized or "dispute" in normalized or "charged me" in normalized:
            return "dispute_resolution"

    return DEFAULT_DEPARTMENT[case_type]


def build_summary(case_type: str, message: str) -> str:
    amount_match = re.search(r"\b(\d+(?:[.,]\d+)?)\b", message)

    if case_type == "wrong_transfer":
        if amount_match:
            return f"Customer reports sending {amount_match.group(1)} to a wrong recipient and requests recovery."
        return "Customer reports a wrong transfer and requests help recovering the funds."

    if case_type == "payment_failed":
        return "Customer reports a failed payment and indicates the balance may have been deducted."

    if case_type == "refund_request":
        return "Customer is requesting a refund for a recent transaction."

    if case_type == "phishing_or_social_engineering":
        return "Customer reports a suspicious contact requesting sensitive account information."

    return "Customer reports an issue that does not match the main predefined categories."


def classify_ticket(ticket_id: str, message: str) -> dict:
    case_type, confidence = detect_case_type(message)
    severity = detect_severity(case_type, message)
    department = detect_department(case_type, severity, message)
    agent_summary = build_summary(case_type, message)
    human_review_required = case_type == "phishing_or_social_engineering" or severity == "critical"

    return {
        "ticket_id": ticket_id,
        "case_type": case_type,
        "severity": severity,
        "department": department,
        "agent_summary": agent_summary,
        "human_review_required": human_review_required,
        "confidence": confidence,
    }