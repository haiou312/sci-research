#!/usr/bin/env python3
"""Weekly fixed-income blocks for US/UK/JP via FRED.

KR is intentionally excluded — it is fed by yfinance_kr_bond.py instead.
"""

from __future__ import annotations

import argparse
from typing import Any

from _common import add_window_args, build_window_payload, emit, fail, resolve_window
from _fred import fetch_first_available, get_client

US_MAP: dict[str, list[str]] = {
    "US 2Y": ["DGS2"],
    "US 5Y": ["DGS5"],
    "US 10Y": ["DGS10"],
    "US 30Y": ["DGS30"],
}
UK_MAP: dict[str, list[str]] = {
    "UK short rate proxy": ["IR3TIB01GBM156N", "IRSTCI01GBM156N"],
    "UK long yield proxy": ["IRLTLT01GBM156N"],
}
JP_MAP: dict[str, list[str]] = {
    "JP short rate proxy": ["IR3TIB01JPM156N", "IRSTCI01JPM156N"],
    "JP long yield proxy": ["IRLTLT01JPM156N"],
}


def fetch_block(fred: Any, name_to_ids: dict[str, list[str]], start: str, end: str, mp: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for name, ids in name_to_ids.items():
        rows.append({"instrument": name, **fetch_first_available(fred, ids, start, end, max_points=mp)})
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Weekly fixed-income blocks (FRED): US/UK/JP.")
    add_window_args(parser, default_days=7)
    parser.add_argument("--max-points", type=int, default=60)
    args = parser.parse_args()

    fred, error = get_client()
    if error:
        fail(error.get("error", "FRED client failure"), **{k: v for k, v in error.items() if k != "error"})

    start, end = resolve_window(args.start_date, args.end_date, days=args.days)

    us_rows = fetch_block(fred, US_MAP, start, end, args.max_points)
    uk_rows = fetch_block(fred, UK_MAP, start, end, args.max_points)
    jp_rows = fetch_block(fred, JP_MAP, start, end, args.max_points)

    data_gaps: list[str] = []
    for block_name, rows in (("US", us_rows), ("UK", uk_rows), ("JP", jp_rows)):
        for r in rows:
            if not r.get("selected_series_id"):
                data_gaps.append(f"{block_name} {r['instrument']}: no series available")

    emit(
        {
            "section": "fixed_income",
            "source": "FRED",
            "window": build_window_payload(start, end),
            "us_treasuries": us_rows,
            "uk_gilts": uk_rows,
            "jp_jgbs": jp_rows,
            "notes": "UK/JP rows are FRED proxies; prefer BOE/BOJ yield-curve scripts when available. KR is provided separately by yfinance_kr_bond.py.",
            "data_gaps": data_gaps,
        }
    )


if __name__ == "__main__":
    main()
