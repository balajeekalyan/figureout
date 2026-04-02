"""
Postpone all past event dates in events.json to future dates.

Each past date is shifted forward by the same number of days needed
to land after today, preserving relative spacing between events.

Usage:
    python postpone_dates.py
    python postpone_dates.py --data-path path/to/events.json
    python postpone_dates.py --offset-days 7   # add extra buffer beyond today
"""

import argparse
import json
from datetime import date, timedelta
from pathlib import Path


DEFAULT_DATA_PATH = Path(__file__).parent.parent / "examples/event-sports-booking/mcp-server/data/events.json"


def postpone_dates(data_path: Path, offset_days: int = 0) -> int:
    today = date.today()
    cutoff = today + timedelta(days=offset_days)

    with data_path.open("r", encoding="utf-8") as f:
        events = json.load(f)

    # Collect all past dates to determine the minimum shift needed
    past_dates = []
    for event in events:
        for detail in event.get("details", []):
            d = date.fromisoformat(detail["date"])
            if d <= cutoff:
                past_dates.append(d)

    if not past_dates:
        print("All event dates are already in the future. Nothing to do.")
        return 0

    # Shift = days from the earliest past date to (cutoff + 1), so all events land in future
    earliest = min(past_dates)
    shift = (cutoff - earliest).days + 1

    changed = 0
    for event in events:
        for detail in event.get("details", []):
            d = date.fromisoformat(detail["date"])
            if d <= cutoff:
                new_date = d + timedelta(days=shift)
                print(f"  {detail['date']} -> {new_date}  ({event['name']})")
                detail["date"] = new_date.isoformat()
                changed += 1

    with data_path.open("w", encoding="utf-8") as f:
        json.dump(events, f, indent=4, ensure_ascii=False)

    print(f"\nDone. Shifted {changed} date(s) by +{shift} days (cutoff: {cutoff}).")
    return changed


def main():
    parser = argparse.ArgumentParser(description="Postpone past event dates to the future.")
    parser.add_argument(
        "--data-path",
        type=Path,
        default=DEFAULT_DATA_PATH,
        help="Path to events.json (default: %(default)s)",
    )
    parser.add_argument(
        "--offset-days",
        type=int,
        default=0,
        help="Extra days of buffer beyond today (default: 0)",
    )
    args = parser.parse_args()

    if not args.data_path.exists():
        raise FileNotFoundError(f"events.json not found at: {args.data_path}")

    postpone_dates(args.data_path, args.offset_days)


if __name__ == "__main__":
    main()
