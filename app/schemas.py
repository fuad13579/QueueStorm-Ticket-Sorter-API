from typing import Literal, Optional

from pydantic import BaseModel, Field


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


class TicketRequest(BaseModel):
    ticket_id: str = Field(..., min_length=1)
    channel: Optional[Channel] = None
    locale: Optional[Locale] = None
    message: str = Field(..., min_length=1)


class TicketResponse(BaseModel):
    ticket_id: str
    case_type: CaseType
    severity: Severity
    department: Department
    agent_summary: str
    human_review_required: bool
    confidence: float = Field(..., ge=0.0, le=1.0)