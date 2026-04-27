"""Shared helpers for weekly-report scripts.

Every weekly-report data script emits a single JSON document on stdout and
exits 0 on success, non-zero with a JSON error envelope on failure.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import date, datetime, timedelta
from typing import Any


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value.strip())
    except Exception:
        return None


def resolve_window(
    start_date: str | None,
    end_date: str | None,
    days: int = 7,
) -> tuple[str, str]:
    """Resolve the [start, end] date window in ISO YYYY-MM-DD form."""
    end_dt = parse_date(end_date) or date.today()
    start_dt = parse_date(start_date) or (end_dt - timedelta(days=max(1, int(days)) - 1))
    if start_dt > end_dt:
        start_dt, end_dt = end_dt, start_dt
    return start_dt.isoformat(), end_dt.isoformat()


def safe_float(value: Any) -> float | None:
    try:
        num = float(value)
        if math.isnan(num) or math.isinf(num):
            return None
        return num
    except Exception:
        return None


def summarize_observations(points: list[dict[str, Any]], value_key: str = "value") -> dict[str, Any]:
    """Compute count / latest / start / change_abs / change_pct for an observations list."""
    if not points:
        return {
            "count": 0,
            "latest_date": None,
            "latest_value": None,
            "start_value": None,
            "change_abs": None,
            "change_pct": None,
        }
    start_val = safe_float(points[0].get(value_key))
    latest_val = safe_float(points[-1].get(value_key))
    change_abs = None
    change_pct = None
    if start_val is not None and latest_val is not None:
        change_abs = latest_val - start_val
        if start_val != 0:
            change_pct = (change_abs / start_val) * 100
    return {
        "count": len(points),
        "latest_date": points[-1].get("date"),
        "latest_value": latest_val,
        "start_value": start_val,
        "change_abs": change_abs,
        "change_pct": change_pct,
    }


def build_window_payload(start_date: str, end_date: str) -> dict[str, str]:
    return {"start_date": start_date, "end_date": end_date}


def emit(payload: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(payload, ensure_ascii=False))
    sys.stdout.write("\n")
    sys.stdout.flush()


def fail(message: str, exit_code: int = 1, **extra: Any) -> None:
    payload: dict[str, Any] = {"error": message}
    payload.update(extra)
    sys.stdout.write(json.dumps(payload, ensure_ascii=False))
    sys.stdout.write("\n")
    sys.stdout.flush()
    sys.exit(exit_code)


def add_window_args(parser: argparse.ArgumentParser, default_days: int = 7) -> None:
    parser.add_argument("--start-date", help="ISO YYYY-MM-DD; default end_date - (days-1)")
    parser.add_argument("--end-date", help="ISO YYYY-MM-DD; default today")
    parser.add_argument("--days", type=int, default=default_days, help=f"Fallback lookback window, default {default_days}")


def iso_today() -> str:
    return date.today().isoformat()


def date_range(start: str, end: str) -> list[str]:
    s = date.fromisoformat(start)
    e = date.fromisoformat(end)
    if s > e:
        s, e = e, s
    out = []
    cur = s
    while cur <= e:
        out.append(cur.isoformat())
        cur += timedelta(days=1)
    return out
