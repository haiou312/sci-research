#!/usr/bin/env python3
"""Validate a dynamically captured EU Member-State snapshot."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import re
import sys
from typing import Any


AUTHORITIES = {
    "eu_country_profiles": (
        "https://european-union.europa.eu/principles-countries-history/"
        "eu-countries_en"
    ),
    "eur_lex_member_states": (
        "https://eur-lex.europa.eu/legal-content/EN/ALL/"
        "?uri=LEGISSUM:member_states"
    ),
}
ALIASES = {
    "czech republic": "czechia",
}


def normalized_name(value: str) -> str:
    name = re.sub(r"\s+", " ", value.strip()).casefold()
    if name.startswith("the "):
        name = name[4:]
    return ALIASES.get(name, name)


def normalized_map(values: Any, label: str) -> dict[str, str]:
    if not isinstance(values, list) or not values:
        raise ValueError(f"{label}: countries must be a non-empty list")
    result: dict[str, str] = {}
    for value in values:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{label}: country names must be non-empty strings")
        key = normalized_name(value)
        if key in result:
            raise ValueError(f"{label}: duplicate country {value}")
        result[key] = value.strip()
    return result


def parse_timestamp(value: Any, label: str) -> None:
    if not isinstance(value, str):
        raise ValueError(f"{label}: timestamp must be a string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{label}: timestamp must be ISO 8601") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{label}: timestamp must include a timezone")


def validate_snapshot(data: dict[str, Any]) -> list[str]:
    if data.get("schema_version") != 1:
        raise ValueError("membership snapshot schema_version must be 1")
    parse_timestamp(data.get("checked_at"), "checked_at")
    top = normalized_map(data.get("countries"), "membership snapshot")
    count = data.get("count")
    if not isinstance(count, int) or isinstance(count, bool) or count != len(top):
        raise ValueError("membership snapshot count differs from countries")

    sources = data.get("sources")
    if not isinstance(sources, list) or len(sources) != len(AUTHORITIES):
        raise ValueError("membership snapshot must contain both official authorities")
    seen: set[str] = set()
    for source in sources:
        if not isinstance(source, dict):
            raise ValueError("membership source records must be objects")
        source_id = source.get("source_id")
        if source_id not in AUTHORITIES or source_id in seen:
            raise ValueError("membership source IDs must be unique official authorities")
        seen.add(source_id)
        if source.get("url") != AUTHORITIES[source_id]:
            raise ValueError(f"{source_id}: authority URL differs from the required URL")
        if source.get("available") is not True:
            raise ValueError(f"{source_id}: authority must be available")
        if source.get("pagination_complete") is not True:
            raise ValueError(f"{source_id}: pagination must be complete")
        parse_timestamp(source.get("retrieved_at"), f"{source_id}/retrieved_at")
        source_map = normalized_map(source.get("countries"), source_id)
        displayed_count = source.get("displayed_count")
        if (
            not isinstance(displayed_count, int)
            or isinstance(displayed_count, bool)
            or displayed_count != len(source_map)
        ):
            raise ValueError(f"{source_id}: displayed_count differs from countries")
        missing = sorted(top_key for top_key in top if top_key not in source_map)
        extra = sorted(key for key in source_map if key not in top)
        if missing or extra:
            details = []
            if missing:
                details.append("missing: " + ", ".join(top[key] for key in missing))
            if extra:
                details.append("extra: " + ", ".join(source_map[key] for key in extra))
            raise ValueError(f"{source_id}: differs from membership snapshot; " + "; ".join(details))

    if seen != set(AUTHORITIES):
        raise ValueError("membership snapshot is missing an official authority")
    return [value.strip() for value in data["countries"]]


def load_snapshot(path: Path) -> dict[str, Any]:
    data = json.loads(path.expanduser().read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("membership snapshot root must be an object")
    return data


def self_test() -> None:
    countries = ["Austria", "Czechia", "Germany"]
    fixture = {
        "schema_version": 1,
        "checked_at": "2026-08-03T07:00:00+01:00",
        "count": 3,
        "countries": countries,
        "sources": [
            {
                "source_id": "eu_country_profiles",
                "url": AUTHORITIES["eu_country_profiles"],
                "available": True,
                "pagination_complete": True,
                "retrieved_at": "2026-08-03T07:00:00+01:00",
                "displayed_count": 3,
                "countries": countries,
            },
            {
                "source_id": "eur_lex_member_states",
                "url": AUTHORITIES["eur_lex_member_states"],
                "available": True,
                "pagination_complete": True,
                "retrieved_at": "2026-08-03T07:01:00+01:00",
                "displayed_count": 3,
                "countries": ["Germany", "Czech Republic", "Austria"],
            },
        ],
    }
    if validate_snapshot(fixture) != countries:
        raise AssertionError("valid dynamic membership fixture did not validate")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", type=Path)
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.self_test:
        self_test()
        print("CRD_VI_MEMBERSHIP_SELF_TEST_OK")
        return 0
    if args.file is None:
        raise ValueError("--file is required unless --self-test is used")
    countries = validate_snapshot(load_snapshot(args.file))
    print(f"CRD_VI_MEMBERSHIP_OK countries={len(countries)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"CRD_VI_MEMBERSHIP_ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
