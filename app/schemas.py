from typing import Literal, Optional

from pydantic import BaseModel, Field


# Literal type aliases keep the API contract strict so invalid values are rejected before classification runs.
CaseType = Literal[
    "wrong_transfer",
    "payment_failed",
    "refund_request",
    "phishing_or_social_engineering",
    "other",
]

Severity = Literal["low", "medium", "high", "critical"]

Department = Literal[
    "customer_support",
    "dispute_resolution",
    "payments_ops",
    "fraud_risk",
]

Channel = Literal["app", "sms", "call_center", "merchant_portal"]
Locale = Literal["bn", "en", "mixed"]


# Incoming request payload for /sort-ticket.
# Example: ticket_id and message are required, while channel and locale are optional hints.
class TicketRequest(BaseModel):
    ticket_id: str = Field(..., min_length=1)
    channel: Optional[Channel] = None
    locale: Optional[Locale] = None
    message: str = Field(..., min_length=1)


# Outgoing response shape returned to the caller and used by the grader.
class TicketResponse(BaseModel):
    ticket_id: str
    case_type: CaseType
    severity: Severity
    department: Department
    agent_summary: str
    human_review_required: bool
    confidence: float = Field(..., ge=0.0, le=1.0)