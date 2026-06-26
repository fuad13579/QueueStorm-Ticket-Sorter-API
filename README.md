# QueueStorm Ticket Sorter API

A small FastAPI service for the QueueStorm Warmup mock preliminary task of Codex Community Hackathon at the SUST CSE Carnival 2026.

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

Core implementation is in place and the public sample cases are covered by tests.

Implemented:
- `GET /health`
- `POST /sort-ticket`
- request and response schemas
- rule-based ticket classification
- phishing and critical human-review flagging
- sample API tests

Validation:
- `pytest -q` currently passes locally


## Deployment Notes

Submission requires:
- public GitHub repository
- public HTTPS base URL
- working `/health` endpoint
- README with enough setup information to run locally

## Verified Live Responses

A live deployment is running at `https://queuestorm-ticket-sorter-api.onrender.com`.

The smoke harness in `scripts/smoke_test_live.py` replays the public sample
messages plus the Bengali/Banglish edge cases against the deployment and
prints PASS/FAIL per case with latency. Each row below is an actual response
captured from the live URL.

<!-- markdownlint-disable MD060 -->

### English (public samples)

| ID    | Message excerpt                                            | case_type                        | severity  | department           | human_review |
| ----- | ---------------------------------------------------------- | -------------------------------- | --------- | -------------------- | ------------ |
| T-001 | `I sent 3000 to a wrong number by mistake please help`     | `wrong_transfer`                 | `high`    | `dispute_resolution` | false        |
| T-002 | `Payment failed but my balance was deducted, please check` | `payment_failed`                 | `high`    | `payments_ops`       | false        |
| T-003 | `Please refund my last transaction, I changed my mind`     | `refund_request`                 | `low`     | `customer_support`   | false        |
| T-004 | `Someone called and asked for my OTP, is this bKash?`      | `phishing_or_social_engineering` | `critical` | `fraud_risk`        | true         |
| T-005 | `The app crashes every time I open the transfer screen`    | `other`                          | `low`     | `customer_support`   | false        |

### Bengali (pure `bn` script)

| ID    | Message excerpt                                  | case_type                        | severity  | department           | human_review |
| ----- | ------------------------------------------------ | -------------------------------- | --------- | -------------------- | ------------ |
| T-203 | `পেমেন্ট ব্যর্থ হয়েছে কিন্তু টাকা কেটে নিয়েছে`  | `payment_failed`                 | `high`    | `payments_ops`       | false        |
| T-205 | `আমি রিফান্ড চাই, টাকা ফেরত দিন`                  | `refund_request`                 | `low`     | `customer_support`   | false        |
| T-207 | `একজন কল করে আমার পিন দিয়ে দিতে বলেছে`            | `phishing_or_social_engineering` | `critical` | `fraud_risk`        | true         |

### Banglish (mixed Latin + Bengali)

| ID    | Message excerpt                                     | case_type                        | severity  | department           | human_review |
| ----- | --------------------------------------------------- | -------------------------------- | --------- | -------------------- | ------------ |
| T-202 | `Ami bhul number e taka pathiye diyechi`            | `wrong_transfer`                 | `high`    | `dispute_resolution` | false        |
| T-204 | `Payment failed hoyeche kintu balance kete niyeche` | `payment_failed`                 | `high`    | `payments_ops`       | false        |
| T-206 | `Refund kore din, ami taka ferot chai`              | `refund_request`                 | `low`     | `customer_support`   | false        |
| T-208 | `Ekjon OTP niye niye call kore, scam kore`          | `phishing_or_social_engineering` | `critical` | `fraud_risk`        | true         |

<!-- markdownlint-enable MD060 -->

### Reproducing the table

```powershell
# from the repo root
python scripts/smoke_test_live.py
```

Override the target URL with `QS_BASE` to verify a preview deploy:

```powershell
$env:QS_BASE = "https://your-preview.example.com"
python scripts/smoke_test_live.py
```
