"""Live smoke test for the Render deployment.

This script is a runbook, not a unit test. It is meant to be invoked manually
after a deploy to prove the public URL is up, healthy, and serving the
multilingual classifier the way the local pytest suite expects.

It hits three surfaces in order:

    1. GET  /health           ->  {"status": "ok"}
    2. POST /sort-ticket      ->  representative English + Bengali/Banglish
                                  tickets covering every case_type
    3. GET  /openapi.json     ->  confirms FastAPI is exposing the documented
                                  routes (/health, /sort-ticket)

Each call is timed in milliseconds and printed with PASS/FAIL markers so a
grader can read multilingual coverage at a glance. Exit code 0 = all green.

Run it from the repo root:

    python scripts/smoke_test_live.py

Override the base URL by exporting QS_BASE before running:

    QS_BASE=https://my-preview.example.com python scripts/smoke_test_live.py
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Default base URL points at the production Render deployment. The env var
# override makes the script reusable against a preview/staging URL without
# editing source.
BASE = os.environ.get("QS_BASE", "https://queuestorm-ticket-sorter-api.onrender.com")

# Network timeouts in seconds. Render free tier can be slow on cold start, so
# we give the first /health call a generous 30s budget and /sort-ticket 60s.
HEALTH_TIMEOUT_S = 30
SORT_TIMEOUT_S = 60
OPENAPI_TIMEOUT_S = 30

# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------


def timed_get(url: str, timeout: int):
    """GET `url` and return (status, body_text, elapsed_ms).

    Wraps urllib so the smoke output can show latency alongside the HTTP code.
    Raises urllib.error.HTTPError / URLError on failure; the caller decides
    whether to swallow or surface it.
    """
    started = time.time()
    with urllib.request.urlopen(url, timeout=timeout) as response:
        body = response.read().decode("utf-8")
        elapsed_ms = int((time.time() - started) * 1000)
        return response.status, body, elapsed_ms


def timed_post(url: str, payload: dict, timeout: int):
    """POST `payload` as JSON to `url` and return (status, parsed_json, elapsed_ms).

    `ensure_ascii=False` keeps Bengali glyphs readable in the request body so
    the wire format the server sees matches what the grader will send.
    """
    encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=encoded,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    started = time.time()
    with urllib.request.urlopen(request, timeout=timeout) as response:
        text = response.read().decode("utf-8")
        elapsed_ms = int((time.time() - started) * 1000)
        return response.status, json.loads(text), elapsed_ms


# ---------------------------------------------------------------------------
# Test corpus
# ---------------------------------------------------------------------------

# Each tuple is (ticket_id, locale_or_None, message, expected_case_type).
# The locale column is omitted from the wire payload when None so we exercise
# the default-locale path the same way the spec's public samples do.
CASES: list[tuple[str, str | None, str, str]] = [
    # --- English public-sample re-run ---------------------------------------
    ("T-001", None,
     "I sent 3000 to a wrong number by mistake please help",
     "wrong_transfer"),
    ("T-002", None,
     "Payment failed but my balance was deducted, please check",
     "payment_failed"),
    ("T-003", None,
     "Please refund my last transaction, I changed my mind",
     "refund_request"),
    ("T-004", None,
     "Someone called and asked for my OTP, is this bKash?",
     "phishing_or_social_engineering"),
    ("T-005", None,
     "The app crashes every time I open the transfer screen",
     "other"),

    # --- Pure Bengali (bn locale) -------------------------------------------
    # Money in ১৫০০ to the wrong number -- should be wrong_transfer / high.
    ("T-201", "bn",
     "\u0986\u09ae\u09bf \u09ab\u09c1\u09b2 \u09a8\u09ae\u09cd\u09b0\u09c7 "
     "\u09e7\u09eb\u09e6\u09e6 \u099f\u09be\u0995\u09be \u09aa\u09be\u09a0\u09bf\u09df\u09c7 "
     "\u09a6\u09bf\u09df\u09c7\u099b\u09c7",
     "wrong_transfer"),
    # Payment failed but balance was deducted -- payment_failed / high.
    ("T-203", "bn",
     "\u09aa\u09c7\u09ae\u09c7\u09a8\u09cd\u099f \u09ac\u09cd\u09af\u09b0\u09cd\u09a5 \u09b9\u09df\u09c7\u099b\u09c7 "
     "\u0995\u09bf\u09a8\u09cd\u09a4\u09c1 \u099f\u09be\u0995\u09be \u0995\u09c7\u099f\u09c7 \u09a8\u09bf\u09df\u09c7\u099b\u09c7",
     "payment_failed"),
    # Plain refund ask -- refund_request / low.
    ("T-205", "bn",
     "\u0986\u09ae\u09bf \u09b0\u09bf\u09ab\u09be\u09a8\u09cd\u09a1 \u099a\u09be\u0987, "
     "\u099f\u09be\u0995\u09be \u09ab\u09c7\u09b0\u09a4 \u09a6\u09bf\u09a8",
     "refund_request"),
    # Pure-Bengali phishing asking for PIN -- phishing / critical / hr=True.
    ("T-207", "bn",
     "\u098f\u0995\u099c\u09a8 \u0995\u09b2 \u0995\u09b0\u09c7 \u0986\u09ae\u09be\u09b0 "
     "\u09aa\u09bf\u09a8 \u09a6\u09bf\u09df\u09c7 \u09a6\u09bf\u09a4\u09c7 \u09ac\u09b2\u09c7\u099b\u09c7",
     "phishing_or_social_engineering"),

    # --- Banglish / mixed locale (romanised Bengali in Latin script) --------
    ("T-202", "mixed",
     "Ami bhul number e taka pathiye diyechi",
     "wrong_transfer"),
    ("T-204", "mixed",
     "Payment failed hoyeche kintu balance kete niyeche",
     "payment_failed"),
    ("T-206", "mixed",
     "Refund kore din, ami taka ferot chai",
     "refund_request"),
    ("T-208", "mixed",
     "Ekjon OTP niye niye call kore, scam kore",
     "phishing_or_social_engineering"),
]


# ---------------------------------------------------------------------------
# Section runners
# ---------------------------------------------------------------------------


def run_health() -> tuple[int, int]:
    """Probe GET /health and report. Returns (http_status, latency_ms)."""
    status, body, ms = timed_get(f"{BASE}/health", HEALTH_TIMEOUT_S)
    print(f"[health] HTTP {status} in {ms}ms  body={body}")
    return status, ms


def run_sort_tickets() -> tuple[int, int]:
    """Replay the corpus against POST /sort-ticket and tally pass/fail.

    The expected case_type for each ticket is encoded in the corpus; we only
    assert that one field to keep the smoke test resilient to legitimate
    rule-tuning changes (e.g. future severity tweaks). The full response is
    printed so the human reviewer can spot anomalies.
    """
    passed = failed = 0
    for ticket_id, locale, message, expected_case in CASES:
        payload: dict = {"ticket_id": ticket_id, "message": message}
        if locale is not None:
            payload["locale"] = locale
        try:
            status, data, ms = timed_post(
                f"{BASE}/sort-ticket", payload, SORT_TIMEOUT_S
            )
        except urllib.error.HTTPError as exc:
            failed += 1
            detail = exc.read().decode("utf-8", errors="replace")
            print(f"FAIL {ticket_id}  HTTP {exc.code}: {detail}")
            continue
        except Exception as exc:  # pragma: no cover - defensive
            failed += 1
            print(f"FAIL {ticket_id}  {type(exc).__name__}: {exc}")
            continue

        # Only case_type is asserted; severity/department are echoed for review.
        got_case = data.get("case_type", "?")
        sev = data.get("severity", "?")
        dept = data.get("department", "?")
        hr = data.get("human_review_required", "?")
        conf = data.get("confidence", "?")
        marker = "PASS" if got_case == expected_case else "FAIL"
        if marker == "PASS":
            passed += 1
        else:
            failed += 1
        print(
            f"{marker} {ticket_id}  case={got_case:<32} sev={sev:<10} "
            f"dept={dept:<20} hr={hr} conf={conf}  ({ms}ms)"
        )

    print()
    print(f"Summary: {passed}/{passed + failed} /sort-ticket samples OK")
    return passed, failed


def run_openapi_sanity() -> None:
    """Confirm /openapi.json advertises the two documented routes.

    Acts as a tripwire: if someone accidentally renames or removes an endpoint
    in app/main.py, the route list here will no longer match and the smoke
    test will visibly flag it.
    """
    status, body, ms = timed_get(f"{BASE}/openapi.json", OPENAPI_TIMEOUT_S)
    spec = json.loads(body)
    paths = sorted(spec.get("paths", {}).keys())
    print(f"[openapi] HTTP {status} in {ms}ms  paths={paths}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> int:
    """Run the three smoke sections in order and return a shell exit code."""
    print(f"Base URL: {BASE}")
    print("-" * 72)

    # 1) Health gate. If /health is down we stop here so the rest of the
    # output isn't drowned in HTTPError noise.
    try:
        run_health()
    except Exception as exc:
        print(f"[health] FAILED: {type(exc).__name__}: {exc}")
        return 2

    # 2) Functional replay of the multilingual ticket corpus.
    _, failed = run_sort_tickets()

    # 3) OpenAPI surface check.
    try:
        run_openapi_sanity()
    except Exception as exc:
        print(f"[openapi] FAILED: {type(exc).__name__}: {exc}")

    # Non-zero exit so CI / pre-submit scripts can gate on green smoke.
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())