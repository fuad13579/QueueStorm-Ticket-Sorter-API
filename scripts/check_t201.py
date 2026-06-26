"""Direct local check: classify T-201 with the current source classifier."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.classifier import classify_ticket

msg = "\u0986\u09ae\u09bf \u09ad\u09c1\u09b2 \u09a8\u09ae\u09cd\u09ac\u09b0\u09c7 \u09e7\u09eb\u09e6\u09e6 \u099f\u09be\u0995\u09be \u09aa\u09be\u09a0\u09bf\u09df\u09c7 \u09a6\u09bf\u09df\u09c7\u099b\u09bf"
result = classify_ticket(ticket_id="T-201", message=msg)
# Write to a UTF-8 file so the Bengali glyphs round-trip safely.
out = Path(__file__).resolve().parent.parent / "scripts" / "check_t201.out.txt"
out.write_text(f"message: {msg}\nresult: {result}\n", encoding="utf-8")