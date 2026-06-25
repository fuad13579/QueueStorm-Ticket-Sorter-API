# Keyword groups drive the rule engine: each phrase can trigger a category without any model call.
# Example: "OTP" or "asked for pin" should immediately flag phishing or social engineering.
CASE_KEYWORDS = {
    "wrong_transfer": [
        "wrong number",
        "wrong recipient",
        "sent to wrong",
        "mistakenly sent",
        "wrong transfer",
        "sent money to the wrong",
    ],
    "payment_failed": [
        "payment failed",
        "transaction failed",
        "balance deducted",
        "money deducted",
        "didn't go through",
        "did not go through",
        "failed transaction",
    ],
    "refund_request": [
        "refund",
        "return my money",
        "money back",
        "changed my mind",
        "cancel transaction",
    ],
    "phishing_or_social_engineering": [
        "otp",
        "pin",
        "password",
        "verification code",
        "scam",
        "fraud call",
        "asked for my otp",
        "asked for otp",
        "asked for pin",
    ],
}

# Default routing maps each detected case type to the team that should handle it first.
DEFAULT_DEPARTMENT = {
    "wrong_transfer": "dispute_resolution",
    "payment_failed": "payments_ops",
    "refund_request": "customer_support",
    "phishing_or_social_engineering": "fraud_risk",
    "other": "customer_support",
}