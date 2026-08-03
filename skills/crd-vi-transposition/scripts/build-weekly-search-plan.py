#!/usr/bin/env python3
"""Build a deterministic CRD VI weekly official-source search plan."""

from __future__ import annotations

import argparse
from datetime import date, timedelta
import json
from pathlib import Path
import sys
from typing import Any


DEEP_STATUSES = {"Pending", "Ongoing"}
UNHEALTHY = {"carried_forward", "conflict", "unavailable"}


def load_object(path: Path, label: str) -> dict[str, Any]:
    data = json.loads(path.expanduser().read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{label} root must be an object")
    return data


def build_plan(
    registry: dict[str, Any],
    period_end: date,
    previous: dict[str, Any] | None = None,
    changed_countries: set[str] | None = None,
    full_refresh: bool = False,
    stale_days: int = 28,
) -> dict[str, Any]:
    entries = registry.get("countries")
    if not isinstance(entries, list) or not entries:
        raise ValueError("registry countries must be a non-empty list")
    registry_by_country = {
        entry.get("country"): entry for entry in entries if isinstance(entry, dict)
    }
    if len(registry_by_country) != len(entries) or None in registry_by_country:
        raise ValueError("registry country names must be present and unique")
    changed = changed_countries or set()
    unknown_changed = sorted(changed - set(registry_by_country))
    if unknown_changed:
        raise ValueError(f"unknown changed countries: {', '.join(unknown_changed)}")
    previous_countries: dict[str, Any] = {}
    if previous is not None:
        value = previous.get("countries")
        if not isinstance(value, dict):
            raise ValueError("previous state countries must be an object")
        previous_countries = value

    deep: list[dict[str, Any]] = []
    light: list[dict[str, Any]] = []
    stale_before = period_end - timedelta(days=stale_days)
    baseline = previous is None
    for country, registry_entry in registry_by_country.items():
        record = previous_countries.get(country, {})
        reasons: list[str] = []
        if baseline:
            reasons.append("baseline")
        if full_refresh:
            reasons.append("scheduled_full_refresh")
        if country in changed:
            reasons.append("central_or_known_source_changed")
        if record.get("status") in DEEP_STATUSES:
            reasons.append(f"prior_status_{str(record['status']).lower()}")
        if record.get("source_health") in UNHEALTHY:
            reasons.append(f"source_health_{record['source_health']}")
        last_verified_value = record.get("last_verified")
        if not baseline and not last_verified_value:
            reasons.append("missing_last_verified")
        elif last_verified_value:
            try:
                last_verified = date.fromisoformat(str(last_verified_value))
            except ValueError as exc:
                raise ValueError(f"{country}: invalid last_verified") from exc
            if last_verified < stale_before:
                reasons.append("official_refresh_overdue")

        item = {
            "country": country,
            "mode": "deep_official" if reasons else "light_known_url",
            "reasons": reasons or ["completed_recently_verified"],
            "official_sources": registry_entry.get("official_sources", []),
            "search_terms": registry_entry.get("search_terms", []),
        }
        (deep if reasons else light).append(item)

    return {
        "schema_version": 1,
        "period_end": period_end.isoformat(),
        "baseline": baseline,
        "full_refresh": full_refresh,
        "stale_days": stale_days,
        "eu_hubs": registry.get("eu_hubs", []),
        "deep_check_count": len(deep),
        "light_check_count": len(light),
        "deep_checks": deep,
        "light_checks": light,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--period-end", type=date.fromisoformat, required=True)
    parser.add_argument("--previous", type=Path)
    parser.add_argument("--changed-country", action="append", default=[])
    parser.add_argument("--full-refresh", action="store_true")
    parser.add_argument("--stale-days", type=int, default=28)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.stale_days < 1:
        raise ValueError("stale-days must be positive")
    registry = load_object(args.registry, "registry")
    previous = load_object(args.previous, "previous state") if args.previous else None
    plan = build_plan(
        registry,
        args.period_end,
        previous,
        set(args.changed_country),
        args.full_refresh,
        args.stale_days,
    )
    print(json.dumps(plan, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"CRD_VI_SEARCH_PLAN_ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
