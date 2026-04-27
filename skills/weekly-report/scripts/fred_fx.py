#!/usr/bin/env python3
"""Weekly FX series via FRED (no Alpha Vantage)."""

from __future__ import annotations

import argparse
from typing import Any

from _common import add_window_args, build_window_payload, emit, fail, resolve_window
from _fred import fetch_first_available, get_client

FX_MAP: dict[str, list[str]] = {
    "USD broad index": ["DTWEXBGS"],
    "EURUSD": ["DEXUSEU"],
    "GBPUSD": ["DEXUSUK"],
    "USDJPY": ["DEXJPUS"],
    "USDKRW": ["DEXKOUS"],
    "USDCNY (CNY proxy for CNY/CNH block)": ["DEXCHUS"],
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Weekly FX series (FRED).")
    add_window_args(parser, default_days=7)
    parser.add_argument("--max-points", type=int, default=60)
    args = parser.parse_args()

    fred, error = get_client()
    if error:
        fail(error.get("error", "FRED client failure"), **{k: v for k, v in error.items() if k != "error"})

    start, end = resolve_window(args.start_date, args.end_date, days=args.days)

    rows: list[dict[str, Any]] = []
    for name, ids in FX_MAP.items():
        rows.append({"instrument": name, **fetch_first_available(fred, ids, start, end, max_points=args.max_points)})

    data_gaps = [f"{r['instrument']}: no series available" for r in rows if not r.get("selected_series_id")]

    emit(
        {
            "section": "foreign_exchange",
            "source": "FRED",
            "window": build_window_payload(start, end),
            "rows": rows,
            "notes": "All FX series sourced from FRED (DEX* dailies / DTWEXBGS broad index). Watch series direction: e.g. DEXJPUS = JPY per USD, DEXUSEU = USD per EUR.",
            "data_gaps": data_gaps,
        }
    )


if __name__ == "__main__":
    main()
