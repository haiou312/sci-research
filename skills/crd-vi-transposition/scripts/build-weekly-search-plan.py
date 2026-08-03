#!/usr/bin/env python3
"""Build a CRD VI search plan from the current dynamic EU membership."""

from __future__ import annotations

import argparse
from datetime import date, timedelta
import json
from pathlib import Path
import re
import sys
from typing import Any


DEEP_STATUSES = {"Pending", "Ongoing"}
UNHEALTHY = {"carried_forward", "conflict", "unavailable"}
ALIASES = {"czech republic": "czechia"}


def normalized_name(value: str) -> str:
    name = re.sub(r"\s+", " ", value.strip()).casefold()
    if name.startswith("the "):
        name = name[4:]
    return ALIASES.get(name, name)


def load_object(path: Path, label: str) -> dict[str, Any]:
    data = json.loads(path.expanduser().read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{label} root must be an object")
    return data


def membership_names(membership: dict[str, Any]) -> list[str]:
    values = membership.get("countries")
    if not isinstance(values, list) or not values:
        raise ValueError("membership countries must be a non-empty list")
    names: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("membership country names must be non-empty strings")
        key = normalized_name(value)
        if key in seen:
            raise ValueError(f"duplicate membership country: {value}")
        seen.add(key)
        names.append(value.strip())
    if membership.get("count") != len(names):
        raise ValueError("membership count differs from countries")
    return names


def normalized_records(countries: Any, label: str) -> dict[str, tuple[str, dict[str, Any]]]:
    if countries is None:
        return {}
    if not isinstance(countries, dict):
        raise ValueError(f"{label} countries must be an object")
    result: dict[str, tuple[str, dict[str, Any]]] = {}
    for country, record in countries.items():
        if not isinstance(country, str) or not isinstance(record, dict):
            raise ValueError(f"{label} country records must be objects")
        key = normalized_name(country)
        if key in result:
            raise ValueError(f"{label} contains duplicate country aliases")
        result[key] = (country, record)
    return result


def source_hints(record: dict[str, Any]) -> list[dict[str, str]]:
    urls = record.get("source_urls")
    if not isinstance(urls, list):
        return []
    return [
        {"role": "previous_verified", "url": url}
        for url in urls
        if isinstance(url, str) and url.startswith("https://")
    ]


def build_plan(
    membership: dict[str, Any],
    period_end: date,
    previous: dict[str, Any] | None = None,
    changed_countries: set[str] | None = None,
    full_refresh: bool = False,
    stale_days: int = 28,
) -> dict[str, Any]:
    members = membership_names(membership)
    member_keys = {normalized_name(country): country for country in members}
    previous_by_key = normalized_records(
        previous.get("countries") if previous else None, "previous state"
    )
    changed_keys = {
        normalized_name(country): country for country in (changed_countries or set())
    }
    unknown_changed = sorted(
        original for key, original in changed_keys.items() if key not in member_keys
    )
    if unknown_changed:
        raise ValueError(f"changed countries are not current members: {', '.join(unknown_changed)}")

    deep: list[dict[str, Any]] = []
    light: list[dict[str, Any]] = []
    stale_before = period_end - timedelta(days=stale_days)
    baseline = previous is None
    for country in members:
        key = normalized_name(country)
        prior = previous_by_key.get(key)
        record = prior[1] if prior else {}
        hints = source_hints(record)
        reasons: list[str] = []
        if baseline:
            reasons.append("baseline")
        elif prior is None:
            reasons.append("new_member_state")
        if full_refresh:
            reasons.append("scheduled_full_refresh")
        if key in changed_keys:
            reasons.append("central_or_known_source_changed")
        if record.get("status") in DEEP_STATUSES:
            reasons.append(f"prior_status_{str(record['status']).lower()}")
        if record.get("source_health") in UNHEALTHY:
            reasons.append(f"source_health_{record['source_health']}")
        if not hints:
            reasons.append("no_historical_official_sources")
        last_verified_value = record.get("last_verified")
        if prior is not None and not last_verified_value:
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
            "official_source_hints": hints,
            "search_terms": [
                f'"Directive (EU) 2024/1619" {country}',
                f'"CRD VI" {country}',
                f'"Article 21c" {country}',
            ],
            "discover_national_sources": bool(reasons),
        }
        (deep if reasons else light).append(item)

    return {
        "schema_version": 1,
        "period_end": period_end.isoformat(),
        "baseline": baseline,
        "full_refresh": full_refresh,
        "stale_days": stale_days,
        "membership_count": len(members),
        "membership_sources": [source.get("url") for source in membership.get("sources", [])],
        "deep_check_count": len(deep),
        "light_check_count": len(light),
        "deep_checks": deep,
        "light_checks": light,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--membership", type=Path, required=True)
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
    membership = load_object(args.membership, "membership snapshot")
    previous = load_object(args.previous, "previous state") if args.previous else None
    plan = build_plan(
        membership,
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
