# QueueStorm Ticket Sorter API

A small FastAPI service for the QueueStorm Warmup mock preliminary task of Codex Community Hackathon in SUST CSE Carnival 2026.

The API accepts one customer support ticket and returns a structured classification with:
- case type
- severity
- department
- agent summary
- human review flag
- confidence score

## Task Requirements

Required endpoints:
- `GET /health`
- `POST /sort-ticket`

Expected classification targets:
- `wrong_transfer`
- `payment_failed`
- `refund_request`
- `phishing_or_social_engineering`
- `other`

## Tech Stack

- Python 3.11+
- FastAPI
- Uvicorn
- Pytest
- Rule-based classification

## Project Structure

```text
app/
  __init__.py
  main.py
  schemas.py
  rules.py
  classifier.py
tests/
  __init__.py
requirements.txt
README.md
```

## Local Setup

Create and activate a virtual environment, then install dependencies.

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run The API

```powershell
uvicorn app.main:app --reload
```

Default local URL:
- `http://127.0.0.1:8000`

Useful docs pages:
- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/redoc`

## API Contract

### `GET /health`

Response example:

```json
{
  "status": "ok"
}
```

### `POST /sort-ticket`

Request example:

```json
{
  "ticket_id": "T-001",
  "channel": "app",
  "locale": "en",
  "message": "I sent 5000 taka to a wrong number this morning, please help me get it back"
}
```

Response example:

```json
{
  "ticket_id": "T-001",
  "case_type": "wrong_transfer",
  "severity": "high",
  "department": "dispute_resolution",
  "agent_summary": "Customer reports sending 5000 BDT to a wrong recipient and requests recovery.",
  "human_review_required": true,
  "confidence": 0.85
}
```

## Test Cases To Support

Public sample cases from the brief:

1. `I sent 3000 to wrong number` -> `wrong_transfer`, `high`
2. `Payment failed but balance deducted` -> `payment_failed`, `high`
3. `Someone called asking my OTP, is that bKash?` -> `phishing_or_social_engineering`, `critical`
4. `Please refund my last transaction, I changed my mind` -> `refund_request`, `low`
5. `App crashed when I opened it` -> `other`, `low`

## Safety Rule

The `agent_summary` must never ask the customer to share:
- PIN
- OTP
- password
- full card number

## Current Status

Repository scaffold is in place.

Files still need implementation:
- `app/main.py`
- `app/schemas.py`
- `app/rules.py`
- `app/classifier.py`
- `tests/test_api.py`

## Recommended Next Steps

1. Implement request and response schemas in `app/schemas.py`.
2. Add keyword rules in `app/rules.py`.
3. Build classification logic in `app/classifier.py`.
4. Expose `/health` and `/sort-ticket` in `app/main.py`.
5. Add tests in `tests/test_api.py`.
6. Run tests locally.
7. Deploy to Render or Railway.

## Deployment Notes

Submission requires:
- public GitHub repository
- public HTTPS base URL
- working `/health` endpoint
- README with enough setup information to run locally
