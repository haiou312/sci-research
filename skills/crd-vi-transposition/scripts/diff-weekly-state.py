#!/usr/bin/env python3
"""Compare CRD VI weekly state snapshots and reject unsafe transitions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


EU_COUNTRIES = (
    "Austria", "Belgium", "Bulgaria", "Croatia", "Cyprus",
    "Czech Republic", "Denmark", "Estonia", "Finland", "France",
    "Germany", "Greece", "Hungary", "Ireland", "Italy", "Latvia",
    "Lithuania", "Luxembourg", "Malta", "Netherlands", "Poland",
    "Portugal", "Romania", "Slovakia", "Slovenia", "Spain", "Sweden",
)
VALID_STATUSES = {"Completed", "Ongoing", "Pending"}
VALID_MARKERS = {
    "Commission: Full",
    "Commission: Partial",
    "Commission: None communicated",
}
VALID_SOURCE_HEALTH = {"verified", "carried_forward", "conflict", "unavailable"}
STATUS_RANK = {"Pending": 0, "Ongoing": 1, "Completed": 2}
MATERIAL_FIELDS = (
    "status",
    "commission_marker",
    "national_measure",
    "milestone_date",
    "measure_effective",
    "article_21c_applies",
)


def load_state(path: Path) -> dict[str, Any]:
    data = json.loads(path.expanduser().read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: state root must be an object")
    return data


def validate_state(data: dict[str, Any], label: str, allow_subset: bool) -> None:
    if data.get("schema_version") != 1:
        raise ValueError(f"{label}: schema_version must be 1")
    countries = data.get("countries")
    if not isinstance(countries, dict) or not countries:
        raise ValueError(f"{label}: countries must be a non-empty object")
    names = set(countries)
    unknown = sorted(names - set(EU_COUNTRIES))
    if unknown:
        raise ValueError(f"{label}: unknown countries: {', '.join(unknown)}")
    if not allow_subset and names != set(EU_COUNTRIES):
        missing = sorted(set(EU_COUNTRIES) - names)
        raise ValueError(
            f"{label}: full snapshot must contain all 27 countries"
            + (f"; missing: {', '.join(missing)}" if missing else "")
        )
    for country, record in countries.items():
        if not isinstance(record, dict):
            raise ValueError(f"{label}/{country}: record must be an object")
        if record.get("status") not in VALID_STATUSES:
            raise ValueError(f"{label}/{country}: invalid status")
        if record.get("commission_marker") not in VALID_MARKERS:
            raise ValueError(f"{label}/{country}: invalid Commission marker")
        if record.get("source_health") not in VALID_SOURCE_HEALTH:
            raise ValueError(f"{label}/{country}: invalid source_health")
        urls = record.get("source_urls")
        if not isinstance(urls, list) or len(urls) < 2:
            raise ValueError(f"{label}/{country}: source_urls must contain at least two URLs")


def compare(
    current: dict[str, Any],
    previous: dict[str, Any] | None = None,
    allow_subset: bool = False,
) -> dict[str, Any]:
    validate_state(current, "current", allow_subset)
    current_countries = current["countries"]
    if previous is None:
        return {
            "schema_version": 1,
            "report_week": current.get("report_week"),
            "previous_week": None,
            "baseline": True,
            "change_count": 0,
            "baseline_country_count": len(current_countries),
            "changed_countries": list(current_countries),
            "unchanged_countries": [],
            "status_transitions": [],
            "changes": [],
        }

    validate_state(previous, "previous", allow_subset)
    previous_countries = previous["countries"]
    if set(current_countries) != set(previous_countries):
        raise ValueError("current and previous snapshots must contain the same countries")

    changes: list[dict[str, Any]] = []
    transitions: list[dict[str, str]] = []
    changed_countries: list[str] = []
    unchanged_countries: list[str] = []
    for country in current_countries:
        before = previous_countries[country]
        after = current_countries[country]
        field_changes = {
            field: {"before": before.get(field), "after": after.get(field)}
            for field in MATERIAL_FIELDS
            if before.get(field) != after.get(field)
        }
        health_changed = before.get("source_health") != after.get("source_health")
        urls_changed = before.get("source_urls") != after.get("source_urls")

        before_status = before["status"]
        after_status = after["status"]
        if before_status != after_status:
            if after.get("source_health") in {"carried_forward", "unavailable"}:
                raise ValueError(
                    f"{country}: source failure cannot create a status transition"
                )
            if STATUS_RANK[after_status] < STATUS_RANK[before_status] and not str(
                after.get("regression_reason", "")
            ).strip():
                raise ValueError(
                    f"{country}: status regression requires regression_reason"
                )
            transitions.append(
                {"country": country, "before": before_status, "after": after_status}
            )

        if field_changes or health_changed or urls_changed:
            changed_countries.append(country)
            changes.append(
                {
                    "country": country,
                    "material": bool(field_changes),
                    "fields": field_changes,
                    "source_health": (
                        {"before": before.get("source_health"), "after": after.get("source_health")}
                        if health_changed
                        else None
                    ),
                    "source_urls_changed": urls_changed,
                }
            )
        else:
            unchanged_countries.append(country)

    material_count = sum(1 for change in changes if change["material"])
    return {
        "schema_version": 1,
        "report_week": current.get("report_week"),
        "previous_week": previous.get("report_week"),
        "baseline": False,
        "change_count": material_count,
        "changed_countries": changed_countries,
        "unchanged_countries": unchanged_countries,
        "status_transitions": transitions,
        "changes": changes,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--current", type=Path, required=True)
    parser.add_argument("--previous", type=Path)
    parser.add_argument("--allow-subset", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    current = load_state(args.current)
    previous = load_state(args.previous) if args.previous else None
    result = compare(current, previous, args.allow_subset)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"CRD_VI_DIFF_ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
