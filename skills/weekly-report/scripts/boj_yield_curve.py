#!/usr/bin/env python3
"""Japan MOF JGB yield-curve (sync port).

Pulls jgbcme.csv (latest) and jgbcme_all.csv (historical), decodes encoding,
parses date+tenor matrix, filters by [start, end] window and tenors.
"""

from __future__ import annotations

import argparse
import csv
import io
import math
import re
from datetime import date
from typing import Any

from _common import add_window_args, build_window_payload, emit, fail, resolve_window

LATEST_CSV_URL = "https://www.mof.go.jp/english/policy/jgbs/reference/interest_rate/jgbcme.csv"
HISTORICAL_CSV_URL = (
    "https://www.mof.go.jp/english/policy/jgbs/reference/interest_rate/historical/jgbcme_all.csv"
)
DOWNLOAD_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/csv,text/plain,*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.mof.go.jp/",
}
DATE_RE = re.compile(r"^\d{4}/\d{1,2}/\d{1,2}$")


def safe_float(v: Any) -> float | None:
    try:
        n = float(v)
        if math.isnan(n) or math.isinf(n):
            return None
        return n
    except Exception:
        return None


def round2(v: float) -> float:
    r = round(float(v), 2)
    return 0.0 if r == -0.0 else r


def to_iso_from_slash(value: str) -> str | None:
    try:
        y, m, d = [int(x) for x in value.strip().split("/")]
        return date(y, m, d).isoformat()
    except Exception:
        return None


def normalize_tenor_label(value: str) -> str | None:
    text = str(value or "").strip().upper()
    if not text:
        return None
    if text.endswith("Y"):
        try:
            n = float(text[:-1])
            return f"{int(n)}Y" if n.is_integer() else f"{n:.1f}Y"
        except Exception:
            return None
    if text.endswith("M"):
        try:
            return f"{int(float(text[:-1]))}M"
        except Exception:
            return None
    try:
        num = float(text)
    except Exception:
        return None
    if num < 1:
        return f"{max(1, int(round(num * 12)))}M"
    if num.is_integer():
        return f"{int(num)}Y"
    return f"{num:.1f}Y"


def normalize_tenor_filter(tenors: list[str]) -> set[str]:
    out: set[str] = set()
    for raw in tenors:
        t = normalize_tenor_label(raw)
        if t:
            out.add(t)
    return out


def tenor_sort_key(tenor: str) -> tuple[int, float]:
    text = str(tenor or "").strip().upper()
    if text.endswith("M"):
        try:
            return (0, float(text[:-1]))
        except Exception:
            return (0, 9999.0)
    if text.endswith("Y"):
        try:
            return (1, float(text[:-1]))
        except Exception:
            return (1, 9999.0)
    return (2, 9999.0)


def download_csv(url: str) -> bytes:
    try:
        import requests
    except Exception as exc:
        raise RuntimeError("requests is required") from exc

    response = requests.get(url, headers=DOWNLOAD_HEADERS, timeout=30, allow_redirects=True)
    if response.status_code == 403:
        response = requests.get(
            url,
            headers={**DOWNLOAD_HEADERS, "Cache-Control": "no-cache", "Pragma": "no-cache"},
            timeout=30,
            allow_redirects=True,
        )
    if response.status_code >= 400:
        raise RuntimeError(f"download failed status={response.status_code} url={url}")
    return response.content


def decode_csv(data: bytes) -> str:
    for enc in ("utf-8-sig", "utf-8", "cp932", "shift_jis"):
        try:
            return data.decode(enc)
        except Exception:
            continue
    return data.decode("utf-8", errors="replace")


def parse_csv_rows(csv_bytes: bytes) -> list[dict[str, Any]]:
    text = decode_csv(csv_bytes)
    reader = csv.reader(io.StringIO(text))

    header: list[str] | None = None
    tenor_map: list[tuple[int, str]] = []
    rows: list[dict[str, Any]] = []
    for raw_row in reader:
        if not raw_row:
            continue
        first = str(raw_row[0] or "").strip()
        if not first:
            continue

        if header is None and first.lower() == "date":
            header = [str(x or "").strip() for x in raw_row]
            for idx, col in enumerate(header):
                if idx == 0:
                    continue
                t = normalize_tenor_label(col)
                if t:
                    tenor_map.append((idx, t))
            continue

        if not DATE_RE.match(first):
            continue
        if header is None or not tenor_map:
            continue

        iso = to_iso_from_slash(first)
        if not iso:
            continue

        for idx, tenor in tenor_map:
            if idx >= len(raw_row):
                continue
            raw_val = str(raw_row[idx] or "").strip()
            if not raw_val or raw_val == "-":
                continue
            value = safe_float(raw_val)
            if value is None:
                continue
            rows.append({"date": iso, "tenor": tenor, "value": round2(value)})
    return rows


def coverage(rows: list[dict[str, Any]]) -> tuple[date | None, date | None]:
    dates: list[date] = []
    for r in rows:
        try:
            dates.append(date.fromisoformat(str(r.get("date") or "")))
        except Exception:
            continue
    if not dates:
        return None, None
    return min(dates), max(dates)


def merge_rows(base, override):
    merged: dict[tuple[str, str], dict[str, Any]] = {}
    for r in base:
        key = (str(r.get("date") or ""), str(r.get("tenor") or ""))
        if key[0] and key[1]:
            merged[key] = r
    for r in override:
        key = (str(r.get("date") or ""), str(r.get("tenor") or ""))
        if key[0] and key[1]:
            merged[key] = r
    return list(merged.values())


def main() -> None:
    parser = argparse.ArgumentParser(description="Japan MOF JGB yield curve.")
    add_window_args(parser, default_days=7)
    parser.add_argument("--tenors", default="2Y,5Y,10Y,30Y", help="Comma-separated tenors filter")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    start, end = resolve_window(args.start_date, args.end_date, days=args.days)
    tenor_list = [t.strip() for t in args.tenors.split(",") if t.strip()]
    tenor_filter = normalize_tenor_filter(tenor_list)
    if tenor_list and not tenor_filter:
        fail("Invalid tenors format", tenors=args.tenors)

    trace: list[dict[str, Any]] = []
    latest_rows: list[dict[str, Any]] = []
    latest_error: str | None = None
    try:
        latest_bytes = download_csv(LATEST_CSV_URL)
        latest_rows = parse_csv_rows(latest_bytes)
        trace.append({"stage": "latest_ok", "rows": len(latest_rows)})
    except Exception as exc:
        latest_error = str(exc)
        trace.append({"stage": "latest_failed", "error": latest_error})

    historical_rows: list[dict[str, Any]] = []
    historical_error: str | None = None
    try:
        hist_bytes = download_csv(HISTORICAL_CSV_URL)
        historical_rows = parse_csv_rows(hist_bytes)
        trace.append({"stage": "historical_ok", "rows": len(historical_rows)})
    except Exception as exc:
        historical_error = str(exc)
        trace.append({"stage": "historical_failed", "error": historical_error})

    merged = merge_rows(historical_rows, latest_rows)
    if not merged:
        fail(
            "Failed to fetch BOJ yield curve data",
            latest_source_error=latest_error,
            historical_source_error=historical_error,
            debug_trace=trace if args.debug else None,
        )

    filtered: list[dict[str, Any]] = []
    for row in merged:
        d = str(row.get("date") or "")
        if d < start or d > end:
            continue
        tenor = str(row.get("tenor") or "")
        if tenor_filter and tenor not in tenor_filter:
            continue
        filtered.append(row)
    filtered.sort(key=lambda x: (str(x["date"]), tenor_sort_key(str(x["tenor"]))))

    series_map: dict[str, list[dict[str, Any]]] = {}
    for row in filtered:
        series_map.setdefault(str(row["tenor"]), []).append({"date": row["date"], "value": row["value"]})

    sources_used: list[dict[str, Any]] = []
    if latest_rows:
        lmin, lmax = coverage(latest_rows)
        sources_used.append(
            {
                "source": "mof_latest",
                "url": LATEST_CSV_URL,
                "coverage": {
                    "start_date": lmin.isoformat() if lmin else None,
                    "end_date": lmax.isoformat() if lmax else None,
                },
                "rows": len(latest_rows),
            }
        )
    if historical_rows:
        hmin, hmax = coverage(historical_rows)
        sources_used.append(
            {
                "source": "mof_historical",
                "url": HISTORICAL_CSV_URL,
                "coverage": {
                    "start_date": hmin.isoformat() if hmin else None,
                    "end_date": hmax.isoformat() if hmax else None,
                },
                "rows": len(historical_rows),
            }
        )

    data_gaps: list[str] = []
    if latest_error:
        data_gaps.append(f"latest source failed: {latest_error}")
    if historical_error:
        data_gaps.append(f"historical source failed: {historical_error}")

    payload: dict[str, Any] = {
        "section": "fixed_income_jp",
        "source": "Japan Ministry of Finance",
        "sheet": "jgbcme.csv",
        "window": build_window_payload(start, end),
        "unit": "percent",
        "sources_used": sources_used,
        "tenors": sorted(series_map.keys(), key=tenor_sort_key),
        "row_count": len(filtered),
        "rows": filtered,
        "series": [
            {"tenor": tenor, "observations": obs}
            for tenor, obs in sorted(series_map.items(), key=lambda x: tenor_sort_key(x[0]))
        ],
        "data_gaps": data_gaps,
    }
    if args.debug:
        payload["debug_trace"] = trace
    emit(payload)


if __name__ == "__main__":
    main()
