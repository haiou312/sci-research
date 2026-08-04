#!/usr/bin/env python3
"""Calculate the fixed CRD VI reporting week in Europe/London."""

from __future__ import annotations

import argparse
from datetime import date, datetime, time, timedelta
import json
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def parse_run_at(value: str | None, timezone: ZoneInfo) -> datetime:
    if value is None:
        return datetime.now(timezone)
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone)
    return parsed.astimezone(timezone)


def latest_completed_sunday(run_at: datetime) -> date:
    days_since_sunday = (run_at.weekday() + 1) % 7
    if days_since_sunday == 0:
        days_since_sunday = 7
    return run_at.date() - timedelta(days=days_since_sunday)


def build_period(
    run_at: datetime,
    timezone: ZoneInfo,
    week_ending: date | None = None,
    output_root: Path = Path("~/.sci-research/reports/crd-vi"),
) -> dict[str, object]:
    period_end = week_ending or latest_completed_sunday(run_at)
    if period_end.weekday() != 6:
        raise ValueError("week_ending must be a Sunday")
    period_start = period_end - timedelta(days=6)
    iso_year, iso_week, _ = period_end.isocalendar()
    previous_end = period_start - timedelta(days=1)
    previous_year, previous_week, _ = previous_end.isocalendar()
    report_week = f"{iso_year}-W{iso_week:02d}"
    start_at = datetime.combine(period_start, time.min, timezone)
    end_at = datetime.combine(period_end, time(23, 59, 59), timezone)
    report_dir = output_root.expanduser() / report_week
    return {
        "schema_version": 1,
        "report_week": report_week,
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
        "period_start_at": start_at.isoformat(),
        "period_end_at": end_at.isoformat(),
        "status_cutoff": period_end.isoformat(),
        "checked_at": run_at.isoformat(),
        "timezone": str(timezone),
        "discovery_start": (period_start - timedelta(days=2)).isoformat(),
        "previous_week": f"{previous_year}-W{previous_week:02d}",
        "full_refresh_due": iso_week % 4 == 0,
        "report_dir": str(report_dir),
        "report_path": str(report_dir / f"crd-vi-transposition-{report_week}.md"),
        "report_docx_path": str(
            report_dir / f"crd-vi-transposition-{report_week}.docx"
        ),
        "audit_dir": str(report_dir / "audit"),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-at", help="ISO timestamp; defaults to now")
    parser.add_argument("--week-ending", type=date.fromisoformat)
    parser.add_argument("--timezone", default="Europe/London")
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("~/.sci-research/reports/crd-vi"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        timezone = ZoneInfo(args.timezone)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"unknown timezone: {args.timezone}") from exc
    run_at = parse_run_at(args.run_at, timezone)
    period = build_period(run_at, timezone, args.week_ending, args.output_root)
    print(json.dumps(period, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValueError as exc:
        raise SystemExit(f"CRD_VI_WEEK_ERROR: {exc}") from exc
