#!/usr/bin/env python3
"""Weekly money market proxies for USD/EUR/GBP via FRED."""

from __future__ import annotations

import argparse
from typing import Any

from _common import add_window_args, build_window_payload, emit, fail, resolve_window
from _fred import fetch_first_available, get_client

INSTRUMENTS: list[tuple[str, list[str]]] = [
    ("USD O/N", ["SOFR", "DFF", "FEDFUNDS"]),
    ("EUR O/N", ["ECBDFR", "IR3TIB01EZM156N", "IRSTCI01EZM156N"]),
    ("GBP O/N", ["IUDSOIA", "IRSTCI01GBM156N", "IR3TIB01GBM156N"]),
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Weekly money market proxies (FRED).")
    add_window_args(parser, default_days=7)
    parser.add_argument("--max-points", type=int, default=60)
    args = parser.parse_args()

    fred, error = get_client()
    if error:
        fail(error.get("error", "FRED client failure"), **{k: v for k, v in error.items() if k != "error"})

    start, end = resolve_window(args.start_date, args.end_date, days=args.days)

    rows: list[dict[str, Any]] = []
    for name, candidates in INSTRUMENTS:
        fetched = fetch_first_available(fred, candidates, start, end, max_points=args.max_points)
        rows.append({"instrument": name, **fetched})

    data_gaps = [r["instrument"] for r in rows if not r.get("selected_series_id")]
    emit(
        {
            "section": "money_market",
            "source": "FRED",
            "window": build_window_payload(start, end),
            "rows": rows,
            "notes": "EUR/GBP fall back to policy/interbank proxies when daily series unavailable.",
            "data_gaps": [f"{name}: no series available" for name in data_gaps],
        }
    )


if __name__ == "__main__":
    main()
