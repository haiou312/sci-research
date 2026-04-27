#!/usr/bin/env python3
"""Fetch a Korean Treasury bond ETF as a yield-direction proxy.

Default symbol: 148070.KS (KOSEF KR 10Y Treasury Bond ETF). The script reports
ETF closing prices; bond price moves inversely to yield, so a falling close
implies a rising yield (and vice versa).

Outputs a single JSON document on stdout.
"""

from __future__ import annotations

import argparse
from datetime import date, timedelta
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

DEFAULT_SYMBOL = "148070.KS"
FRIENDLY = {
    "148070.KS": {"label": "KR 10Y Treasury (KODEX 148070.KS ETF proxy)", "unit": "KRW"},
    "114820.KS": {"label": "KR 3Y Treasury (KODEX 114820.KS ETF proxy)", "unit": "KRW"},
    "302190.KS": {"label": "KR 10Y Treasury (TIGER 302190.KS ETF proxy)", "unit": "KRW"},
}


def fetch(yf, symbol: str, start: str, end: str) -> dict[str, Any]:
    meta = FRIENDLY.get(symbol, {"label": symbol, "unit": ""})
    end_dt = date.fromisoformat(end) + timedelta(days=1)
    try:
        df = yf.Ticker(symbol).history(
            start=start,
            end=end_dt.isoformat(),
            interval="1d",
            auto_adjust=False,
        )
    except Exception as exc:
        return {
            "instrument": meta["label"],
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
                    "close": close_val,
                    "value": close_val,
                }
            )

    return {
        "instrument": meta["label"],
        "symbol": symbol,
        "unit": meta["unit"],
        "observations": observations,
        "summary": summarize_observations(observations, value_key="close"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch KR Treasury bond ETF proxy from Yahoo Finance.")
    add_window_args(parser, default_days=7)
    parser.add_argument(
        "--symbol",
        default=DEFAULT_SYMBOL,
        help=f"yfinance symbol (default: {DEFAULT_SYMBOL})",
    )
    args = parser.parse_args()

    try:
        import yfinance as yf
    except Exception as exc:
        fail("yfinance package is not installed", hint="pip install yfinance", detail=str(exc))

    start, end = resolve_window(args.start_date, args.end_date, days=args.days)
    row = fetch(yf, args.symbol, start, end)

    data_gaps: list[str] = []
    if row.get("error") or row["summary"]["count"] == 0:
        data_gaps.append(
            f"{row['instrument']}: {row.get('error') or 'no observations in window'}"
        )

    emit(
        {
            "section": "fixed_income_kr",
            "source": "Yahoo Finance ETF proxy",
            "window": build_window_payload(start, end),
            "row": row,
            "notes": "ETF close price; bond price moves inversely to yield (close ↓ → yield ↑).",
            "data_gaps": data_gaps,
        }
    )


if __name__ == "__main__":
    main()
