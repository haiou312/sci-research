"""Shared FRED client + series-fetch helpers for the weekly-report skill."""

from __future__ import annotations

import os
from typing import Any

from _common import safe_float, summarize_observations


def get_client() -> tuple[Any | None, dict[str, Any] | None]:
    """Return (Fred instance, None) on success or (None, error_dict) on failure."""
    api_key = (os.environ.get("FRED_API_KEY") or "").strip()
    if not api_key:
        return None, {
            "error": "FRED API key is not configured",
            "hint": "Set FRED_API_KEY environment variable",
        }
    try:
        from fredapi import Fred
    except Exception as exc:
        return None, {
            "error": "fredapi package is not installed",
            "hint": "pip install fredapi",
            "detail": str(exc),
        }
    return Fred(api_key=api_key), None


def fetch_series(
    fred: Any,
    series_id: str,
    start_date: str,
    end_date: str,
    max_points: int = 60,
) -> dict[str, Any]:
    """Fetch a single FRED series with summary + meta. Errors return {'series_id', 'error'}."""
    try:
        raw = fred.get_series(series_id, observation_start=start_date, observation_end=end_date)
    except Exception as exc:
        return {"series_id": series_id, "error": str(exc)}

    observations: list[dict[str, Any]] = []
    try:
        cleaned = raw.dropna()
        for idx, value in cleaned.items():
            if hasattr(idx, "date"):
                d = idx.date().isoformat()
            else:
                d = str(idx)[:10]
            num = safe_float(value)
            if num is None:
                continue
            observations.append({"date": d, "value": num})
    except Exception:
        observations = []

    limit = max(1, min(int(max_points), 365))
    observations = observations[-limit:]

    meta: dict[str, Any] = {}
    try:
        info = fred.get_series_info(series_id)
        meta = {
            "title": str(info.get("title") or ""),
            "frequency": str(info.get("frequency_short") or info.get("frequency") or ""),
            "units": str(info.get("units_short") or info.get("units") or ""),
            "seasonal_adjustment": str(
                info.get("seasonal_adjustment_short") or info.get("seasonal_adjustment") or ""
            ),
            "observation_start": str(info.get("observation_start") or ""),
            "observation_end": str(info.get("observation_end") or ""),
        }
    except Exception:
        meta = {}

    return {
        "series_id": series_id,
        "meta": meta,
        "summary": summarize_observations(observations),
        "observations": observations,
    }


def fetch_first_available(
    fred: Any,
    series_ids: list[str],
    start_date: str,
    end_date: str,
    max_points: int = 60,
) -> dict[str, Any]:
    """Try each series_id in order; return the first with non-empty observations."""
    errors: list[dict[str, str]] = []
    for sid in series_ids:
        result = fetch_series(fred, sid, start_date, end_date, max_points=max_points)
        if result.get("error"):
            errors.append({"series_id": sid, "error": str(result.get("error"))})
            continue
        if (result.get("summary") or {}).get("count", 0) <= 0:
            errors.append({"series_id": sid, "error": "no observations"})
            continue
        return {"selected_series_id": sid, "data": result, "fallback_errors": errors}
    return {"selected_series_id": None, "data": None, "fallback_errors": errors}
