#!/usr/bin/env python3
"""Fetch commodity weekly OHLC from Yahoo Finance via yfinance.

Default symbols: GC=F (Gold), SI=F (Silver), CL=F (WTI Oil).
Outputs a single JSON document on stdout.
"""

from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta
from typing import Any

from _common import (
    add_window_args,
    build_window_payload,
    emit,
    fail,
    resolve_window,
    safe_float,
    summarize_observations,
)

FRIENDLY_NAMES: dict[str, dict[str, str]] = {
    "GC=F": {"instrument": "Gold", "unit": "USD/oz"},
    "SI=F": {"instrument": "Silver", "unit": "USD/oz"},
    "CL=F": {"instrument": "WTI Oil", "unit": "USD/bbl"},
    "BZ=F": {"instrument": "Brent Oil", "unit": "USD/bbl"},
    "HG=F": {"instrument": "Copper", "unit": "USD/lb"},
    "NG=F": {"instrument": "Natural Gas", "unit": "USD/MMBtu"},
}


def fetch_symbol(yf, symbol: str, start: str, end: str) -> dict[str, Any]:
    meta = FRIENDLY_NAMES.get(symbol, {"instrument": symbol, "unit": ""})
    end_dt = date.fromisoformat(end) + timedelta(days=1)
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(
            start=start,
            end=end_dt.isoformat(),
            interval="1d",
            auto_adjust=False,
        )
    except Exception as exc:
        return {
            "instrument": meta["instrument"],
            "symbol": symbol,
            "unit": meta["unit"],
            "error": f"yfinance fetch failed: {exc}",
            "observations": [],
            "summary": summarize_observations([]),
        }

    observations: list[dict[str, Any]] = []
    if df is not None and not df.empty:
        for idx, row in df.iterrows():
            try:
                d = idx.date().isoformat() if hasattr(idx, "date") else str(idx)[:10]
            except Exception:
                d = str(idx)[:10]
            close_val = safe_float(row.get("Close"))
            if close_val is None:
                continue
            observations.append(
                {
                    "date": d,
                    "open": safe_float(row.get("Open")),
                    "high": safe_float(row.get("High")),
                    "low": safe_float(row.get("Low")),
                    "close": close_val,
                    "volume": safe_float(row.get("Volume")),
                    "value": close_val,
                }
            )

    summary = summarize_observations(observations, value_key="close")
    return {
        "instrument": meta["instrument"],
        "symbol": symbol,
        "unit": meta["unit"],
        "observations": observations,
        "summary": summary,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch commodity weekly OHLC via Yahoo Finance.")
    add_window_args(parser, default_days=7)
    parser.add_argument(
        "--symbols",
        default="GC=F,SI=F,CL=F",
        help="Comma-separated yfinance symbols (default: GC=F,SI=F,CL=F)",
    )
    args = parser.parse_args()

    try:
        import yfinance as yf
    except Exception as exc:
        fail("yfinance package is not installed", hint="pip install yfinance", detail=str(exc))

    start, end = resolve_window(args.start_date, args.end_date, days=args.days)
    symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]

    rows: list[dict[str, Any]] = []
    data_gaps: list[str] = []
    for sym in symbols:
        row = fetch_symbol(yf, sym, start, end)
        rows.append(row)
        if row.get("error") or row["summary"]["count"] == 0:
            data_gaps.append(
                f"{row['instrument']} ({sym}): {row.get('error') or 'no observations in window'}"
            )

    emit(
        {
            "section": "commodity",
            "source": "Yahoo Finance",
            "window": build_window_payload(start, end),
            "rows": rows,
            "data_gaps": data_gaps,
        }
    )


if __name__ == "__main__":
    main()
