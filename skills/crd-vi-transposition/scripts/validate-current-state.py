#!/usr/bin/env python3
"""Validate a full-country CRD VI weekly current-state snapshot."""

from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta
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
DATE_FIELDS = {
    "measure_adopted",
    "measure_published",
    "milestone_date",
    "measure_effective",
    "article_21c_general_applies",
    "article_21c_5_existing_contracts_from",
}
COUNTRY_FIELDS = {
    "status",
    "commission_marker",
    "national_measure",
    "measure_adopted",
    "measure_published",
    "milestone_date",
    "measure_effective",
    "article_21c_general_applies",
    "article_21c_5_existing_contracts_from",
    "source_health",
    "last_verified",
    "source_urls",
}
ALIASES = {"czech republic": "czechia"}


def normalized_name(value: str) -> str:
    name = re.sub(r"\s+", " ", value.strip()).casefold()
    if name.startswith("the "):
        name = name[4:]
    return ALIASES.get(name, name)


def parse_date(value: Any, label: str, allow_none: bool = True) -> None:
    if value is None and allow_none:
        return
    if not isinstance(value, str):
        raise ValueError(f"{label}: date must be YYYY-MM-DD or null")
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{label}: date must be YYYY-MM-DD") from exc


def parse_timestamp(value: Any, label: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError(f"{label}: timestamp must be a string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{label}: timestamp must be ISO 8601") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{label}: timestamp must include a timezone")
    return parsed


def membership_map(data: dict[str, Any]) -> dict[str, str]:
    countries = data.get("countries")
    if not isinstance(countries, list) or not countries:
        raise ValueError("membership countries must be a non-empty list")
    result: dict[str, str] = {}
    for country in countries:
        if not isinstance(country, str) or not country.strip():
            raise ValueError("membership country names must be non-empty strings")
        key = normalized_name(country)
        if key in result:
            raise ValueError(f"duplicate membership country: {country}")
        result[key] = country.strip()
    if data.get("count") != len(result):
        raise ValueError("membership count differs from countries")
    return result


def validate_sources(sources: Any) -> None:
    if not isinstance(sources, dict):
        raise ValueError("current state sources must be an object")
    for source_id in ("commission", "ey"):
        source = sources.get(source_id)
        if not isinstance(source, dict):
            raise ValueError(f"current state sources missing {source_id}")
        if not isinstance(source.get("available"), bool):
            raise ValueError(f"{source_id}: available must be boolean")
        parse_date(source.get("last_updated"), f"{source_id}/last_updated")
        content_hash = source.get("content_hash")
        if content_hash is not None and (
            not isinstance(content_hash, str) or not content_hash.startswith("sha256:")
        ):
            raise ValueError(f"{source_id}: content_hash must start with sha256:")


def validate_country(country: str, record: Any) -> None:
    if not isinstance(record, dict):
        raise ValueError(f"{country}: current state record must be an object")
    missing = sorted(COUNTRY_FIELDS - set(record))
    if missing:
        raise ValueError(f"{country}: missing fields: {', '.join(missing)}")
    if record["status"] not in VALID_STATUSES:
        raise ValueError(f"{country}: invalid status")
    if record["commission_marker"] not in VALID_MARKERS:
        raise ValueError(f"{country}: invalid Commission marker")
    if record["source_health"] not in VALID_SOURCE_HEALTH:
        raise ValueError(f"{country}: invalid source_health")
    if record["national_measure"] is not None and not isinstance(
        record["national_measure"], str
    ):
        raise ValueError(f"{country}: national_measure must be a string or null")
    for field in DATE_FIELDS:
        parse_date(record[field], f"{country}/{field}")
    parse_date(record["last_verified"], f"{country}/last_verified", allow_none=False)
    urls = record["source_urls"]
    if not isinstance(urls, list) or len(urls) < 2:
        raise ValueError(f"{country}: source_urls must contain at least two URLs")
    if not all(isinstance(url, str) and url.startswith("https://") for url in urls):
        raise ValueError(f"{country}: source_urls must contain HTTPS URLs")
    if len(set(urls)) != len(urls):
        raise ValueError(f"{country}: source_urls contain duplicates")
    if "regression_reason" in record and not str(record["regression_reason"]).strip():
        raise ValueError(f"{country}: regression_reason cannot be empty")


def validate_state(data: dict[str, Any], membership: dict[str, Any]) -> list[str]:
    if data.get("schema_version") != 1:
        raise ValueError("current state schema_version must be 1")
    report_week = data.get("report_week")
    if not isinstance(report_week, str) or not re.fullmatch(r"\d{4}-W\d{2}", report_week):
        raise ValueError("current state report_week must be YYYY-Www")
    period_start = data.get("period_start")
    period_end = data.get("period_end")
    cutoff = data.get("status_cutoff")
    parse_date(period_start, "period_start", allow_none=False)
    parse_date(period_end, "period_end", allow_none=False)
    parse_date(cutoff, "status_cutoff", allow_none=False)
    start = date.fromisoformat(period_start)
    end = date.fromisoformat(period_end)
    if start.weekday() != 0 or end.weekday() != 6 or end - start != timedelta(days=6):
        raise ValueError("current state period must be Monday through Sunday")
    if cutoff != period_end:
        raise ValueError("status_cutoff must equal period_end")
    iso_year, iso_week, _ = end.isocalendar()
    if report_week != f"{iso_year}-W{iso_week:02d}":
        raise ValueError("report_week does not match period_end")
    checked_at = parse_timestamp(data.get("checked_at"), "checked_at")
    if checked_at.date() < end:
        raise ValueError("checked_at cannot be before period_end")
    validate_sources(data.get("sources"))

    members = membership_map(membership)
    countries = data.get("countries")
    if not isinstance(countries, dict) or not countries:
        raise ValueError("current state countries must be a non-empty object")
    state_map: dict[str, str] = {}
    for country, record in countries.items():
        if not isinstance(country, str):
            raise ValueError("current state country names must be strings")
        key = normalized_name(country)
        if key in state_map:
            raise ValueError(f"duplicate current state country alias: {country}")
        state_map[key] = country
        validate_country(country, record)
    missing = sorted(members[key] for key in members.keys() - state_map.keys())
    extra = sorted(state_map[key] for key in state_map.keys() - members.keys())
    if missing or extra:
        details = []
        if missing:
            details.append("missing: " + ", ".join(missing))
        if extra:
            details.append("extra: " + ", ".join(extra))
        raise ValueError("current state differs from membership; " + "; ".join(details))
    return [state_map[key] for key in members]


def load_object(path: Path, label: str) -> dict[str, Any]:
    data = json.loads(path.expanduser().read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{label} root must be an object")
    return data


def self_test() -> None:
    membership = {"count": 1, "countries": ["Germany"]}
    state = {
        "schema_version": 1,
        "report_week": "2026-W31",
        "period_start": "2026-07-27",
        "period_end": "2026-08-02",
        "status_cutoff": "2026-08-02",
        "checked_at": "2026-08-03T07:00:00+01:00",
        "sources": {
            "commission": {"last_updated": "2026-07-31", "content_hash": "sha256:x", "available": True},
            "ey": {"last_updated": "2026-07-30", "content_hash": "sha256:y", "available": True},
        },
        "countries": {
            "Germany": {
                "status": "Completed",
                "commission_marker": "Commission: Full",
                "national_measure": "Act 1/2026",
                "measure_adopted": "2026-07-29",
                "measure_published": None,
                "milestone_date": "2026-07-29",
                "measure_effective": None,
                "article_21c_general_applies": "2027-01-11",
                "article_21c_5_existing_contracts_from": "2026-07-11",
                "source_health": "verified",
                "last_verified": "2026-08-03",
                "source_urls": ["https://example.gov/act", "https://finance.ec.europa.eu/crd-vi"],
            }
        },
    }
    if validate_state(state, membership) != ["Germany"]:
        raise AssertionError("valid current-state fixture did not validate")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", type=Path)
    parser.add_argument("--membership", type=Path)
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.self_test:
        self_test()
        print("CRD_VI_STATE_SELF_TEST_OK")
        return 0
    if args.file is None or args.membership is None:
        raise ValueError("--file and --membership are required unless --self-test is used")
    countries = validate_state(
        load_object(args.file, "current state"),
        load_object(args.membership, "membership snapshot"),
    )
    print(f"CRD_VI_STATE_OK countries={len(countries)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"CRD_VI_STATE_ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
