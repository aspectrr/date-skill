# /// script
# requires-python = ">=3.10"
# dependencies = ["python-dotenv", "requests"]
# ///
"""Find free days by reading upcoming TimeTree events.

Shows the next N days, marking each as free or busy, so the skill knows
when to suggest booking a date.

Usage:
    python3 free_days.py              # next 21 days
    python3 free_days.py --days 45
"""

import os
import sys
import argparse
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from timetree import TimeTreeClient


def main():
    parser = argparse.ArgumentParser(description="Show free/busy days from TimeTree.")
    parser.add_argument("--days", type=int, default=21, help="Days to look ahead")
    args = parser.parse_args()

    email = os.environ.get("TIMETREE_EMAIL")
    password = os.environ.get("TIMETREE_PASSWORD")
    cal_id = os.environ.get("CALENDAR_ID")

    if not all([email, password, cal_id]):
        sys.stderr.write("Missing TIMETREE_EMAIL, TIMETREE_PASSWORD, or CALENDAR_ID.\n")
        sys.exit(2)

    client = TimeTreeClient()
    client.signin(email, password)
    events, _ = client.get_events(int(cal_id))

    # Bucket events by date
    now = datetime.now(timezone.utc)
    by_day = {}
    for e in events:
        if not e.start_at or e.start_at < now:
            continue
        key = e.start_at.strftime("%Y-%m-%d")
        by_day.setdefault(key, []).append(e)

    print(f"=== Next {args.days} Days ===\n")
    for i in range(args.days):
        day = now + timedelta(days=i)
        key = day.strftime("%Y-%m-%d")
        label = day.strftime("%a %b %d")
        busy = by_day.get(key, [])

        if busy:
            print(f"📌 {label} — BUSY:")
            for e in sorted(busy, key=lambda x: x.start_at):
                t = e.start_at.strftime("%I:%M %p").strip()
                print(f"   {t}  {e.title}")
        else:
            print(f"✅ {label} — FREE")

    free = sum(1 for i in range(args.days)
               if not by_day.get((now + timedelta(days=i)).strftime("%Y-%m-%d")))
    print(f"\n{free} free days out of {args.days}")


if __name__ == "__main__":
    main()
