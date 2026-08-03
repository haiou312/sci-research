#!/usr/bin/env python3
"""Compare CRD VI snapshots against dynamic EU membership."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any


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
    "measure_adopted",
    "measure_published",
    "milestone_date",
    "measure_effective",
    "article_21c_general_applies",
    "article_21c_5_existing_contracts_from",
)
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


def membership_map(membership: dict[str, Any]) -> dict[str, str]:
    values = membership.get("countries")
    if not isinstance(values, list) or not values:
        raise ValueError("membership countries must be a non-empty list")
    result: dict[str, str] = {}
    for value in values:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("membership country names must be non-empty strings")
        key = normalized_name(value)
        if key in result:
            raise ValueError(f"duplicate membership country: {value}")
        result[key] = value.strip()
    if membership.get("count") != len(result):
        raise ValueError("membership count differs from countries")
    return result


def validate_state(data: dict[str, Any], label: str) -> dict[str, tuple[str, dict[str, Any]]]:
    if data.get("schema_version") != 1:
        raise ValueError(f"{label}: schema_version must be 1")
    countries = data.get("countries")
    if not isinstance(countries, dict) or not countries:
        raise ValueError(f"{label}: countries must be a non-empty object")
    result: dict[str, tuple[str, dict[str, Any]]] = {}
    for country, record in countries.items():
        if not isinstance(country, str) or not isinstance(record, dict):
            raise ValueError(f"{label}: country records must be objects")
        key = normalized_name(country)
        if key in result:
            raise ValueError(f"{label}: duplicate country aliases")
        if record.get("status") not in VALID_STATUSES:
            raise ValueError(f"{label}/{country}: invalid status")
        if record.get("commission_marker") not in VALID_MARKERS:
            raise ValueError(f"{label}/{country}: invalid Commission marker")
        if record.get("source_health") not in VALID_SOURCE_HEALTH:
            raise ValueError(f"{label}/{country}: invalid source_health")
        urls = record.get("source_urls")
        if not isinstance(urls, list) or len(urls) < 2:
            raise ValueError(f"{label}/{country}: source_urls must contain at least two URLs")
        result[key] = (country, record)
    return result


def compare(
    current: dict[str, Any],
    membership: dict[str, Any],
    previous: dict[str, Any] | None = None,
) -> dict[str, Any]:
    members = membership_map(membership)
    current_map = validate_state(current, "current")
    current_keys = set(current_map)
    member_keys = set(members)
    if current_keys != member_keys:
        missing = sorted(members[key] for key in member_keys - current_keys)
        extra = sorted(current_map[key][0] for key in current_keys - member_keys)
        details = []
        if missing:
            details.append("missing: " + ", ".join(missing))
        if extra:
            details.append("extra: " + ", ".join(extra))
        raise ValueError("current snapshot differs from dynamic membership; " + "; ".join(details))

    current_countries = current["countries"]
    if previous is None:
        return {
            "schema_version": 1,
            "report_week": current.get("report_week"),
            "previous_week": None,
            "baseline": True,
            "change_count": 0,
            "baseline_country_count": len(current_countries),
            "membership_changes": {"added": [], "removed": []},
            "changed_countries": list(current_countries),
            "unchanged_countries": [],
            "status_transitions": [],
            "changes": [],
        }

    previous_map = validate_state(previous, "previous")
    previous_keys = set(previous_map)
    added_keys = current_keys - previous_keys
    removed_keys = previous_keys - current_keys
    added = [current_map[key][0] for key in sorted(added_keys)]
    removed = [previous_map[key][0] for key in sorted(removed_keys)]

    changes: list[dict[str, Any]] = [
        {"country": country, "material": True, "membership_change": "added"}
        for country in added
    ] + [
        {"country": country, "material": True, "membership_change": "removed"}
        for country in removed
    ]
    transitions: list[dict[str, str]] = []
    changed_countries: list[str] = added + removed
    unchanged_countries: list[str] = []
    for key in sorted(current_keys & previous_keys):
        country, after = current_map[key]
        _, before = previous_map[key]
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
                raise ValueError(f"{country}: source failure cannot create a status transition")
            if STATUS_RANK[after_status] < STATUS_RANK[before_status] and not str(
                after.get("regression_reason", "")
            ).strip():
                raise ValueError(f"{country}: status regression requires regression_reason")
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
        "membership_changes": {"added": added, "removed": removed},
        "changed_countries": changed_countries,
        "unchanged_countries": unchanged_countries,
        "status_transitions": transitions,
        "changes": changes,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--current", type=Path, required=True)
    parser.add_argument("--membership", type=Path, required=True)
    parser.add_argument("--previous", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    current = load_object(args.current, "current state")
    membership = load_object(args.membership, "membership snapshot")
    previous = load_object(args.previous, "previous state") if args.previous else None
    result = compare(current, membership, previous)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"CRD_VI_DIFF_ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
