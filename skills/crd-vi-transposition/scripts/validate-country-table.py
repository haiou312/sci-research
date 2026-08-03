#!/usr/bin/env python3
"""Validate a CRD VI EY-style Markdown country table."""

from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta
import json
from pathlib import Path
import re
import sys
from typing import Any


VALID_STATUSES = {"Completed", "Ongoing", "Pending"}
COMMISSION_MARKERS = {
    "Commission: Full",
    "Commission: Partial",
    "Commission: None communicated",
}
HEADER = ["Country", "Current Status", "Summary"]
WEEKLY_FIELDS = {
    "report_week",
    "period_start",
    "period_end",
    "timezone",
    "status_cutoff",
    "checked_at",
    "previous_successful_week",
    "country_filter",
    "change_count",
    "news_count",
}
SOURCE_HEALTH = {"verified", "carried_forward", "conflict", "unavailable"}


def split_row(line: str) -> list[str] | None:
    stripped = line.strip()
    if not (stripped.startswith("|") and stripped.endswith("|")):
        return None
    return [cell.strip() for cell in stripped[1:-1].split("|")]


def is_separator(cells: list[str] | None) -> bool:
    return bool(
        cells
        and len(cells) == 3
        and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)
    )


def extract_rows(text: str) -> list[list[str]]:
    lines = text.splitlines()
    header_indexes = [
        index for index, line in enumerate(lines) if split_row(line) == HEADER
    ]
    if len(header_indexes) != 1:
        raise ValueError(
            f"expected exactly one Country/Current Status/Summary table, found {len(header_indexes)}"
        )
    header_index = header_indexes[0]
    if header_index + 1 >= len(lines) or not is_separator(
        split_row(lines[header_index + 1])
    ):
        raise ValueError("the three-column header is not followed by a valid separator")

    rows: list[list[str]] = []
    for line in lines[header_index + 2 :]:
        cells = split_row(line)
        if cells is None:
            if rows:
                break
            if line.strip():
                raise ValueError("unexpected content between the header and first country row")
            continue
        if len(cells) != 3:
            raise ValueError(f"country row has {len(cells)} columns instead of 3: {line}")
        rows.append(cells)
    if not rows:
        raise ValueError("the country table has no data rows")
    return rows


def parse_frontmatter(text: str) -> dict[str, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("weekly report must start with YAML-style frontmatter")
    try:
        closing = lines.index("---", 1)
    except ValueError as exc:
        raise ValueError("weekly frontmatter is not closed") from exc
    metadata: dict[str, str] = {}
    for line in lines[1:closing]:
        if not line.strip():
            continue
        if ":" not in line:
            raise ValueError(f"invalid weekly frontmatter line: {line}")
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"').strip("'")
    missing = sorted(WEEKLY_FIELDS - set(metadata))
    if missing:
        raise ValueError(f"weekly frontmatter missing: {', '.join(missing)}")
    return metadata


def parse_country_filter(metadata: dict[str, str]) -> set[str] | None:
    value = metadata.get("country_filter", "").strip()
    if value == "all":
        return None
    if not value:
        raise ValueError("country_filter must be all or a comma-separated country list")
    countries = {country.strip() for country in value.split(",") if country.strip()}
    if not countries or len(countries) != len(value.split(",")):
        raise ValueError("country_filter contains an empty or duplicate country")
    return countries


def validate_weekly(text: str) -> dict[str, str]:
    metadata = parse_frontmatter(text)
    parse_country_filter(metadata)
    if metadata["timezone"] != "Europe/London":
        raise ValueError("weekly timezone must be Europe/London")
    try:
        period_start = date.fromisoformat(metadata["period_start"])
        period_end = date.fromisoformat(metadata["period_end"])
        cutoff = date.fromisoformat(metadata["status_cutoff"])
    except ValueError as exc:
        raise ValueError("weekly date fields must use YYYY-MM-DD") from exc
    if period_start.weekday() != 0 or period_end.weekday() != 6:
        raise ValueError("weekly period must run Monday through Sunday")
    if period_end - period_start != timedelta(days=6):
        raise ValueError("weekly period must contain exactly seven calendar days")
    if cutoff != period_end:
        raise ValueError("status_cutoff must equal period_end")
    iso_year, iso_week, _ = period_end.isocalendar()
    expected_week = f"{iso_year}-W{iso_week:02d}"
    if metadata["report_week"] != expected_week:
        raise ValueError(f"report_week must be {expected_week}")
    previous = metadata["previous_successful_week"]
    if previous != "none" and not re.fullmatch(r"\d{4}-W\d{2}", previous):
        raise ValueError("previous_successful_week must be YYYY-Www or none")
    try:
        change_count = int(metadata["change_count"])
    except ValueError as exc:
        raise ValueError("change_count must be a non-negative integer") from exc
    if change_count < 0:
        raise ValueError("change_count must be a non-negative integer")
    try:
        news_count = int(metadata["news_count"])
    except ValueError as exc:
        raise ValueError("news_count must be an integer between 0 and 8") from exc
    if not 0 <= news_count <= 8:
        raise ValueError("news_count must be an integer between 0 and 8")
    try:
        checked_at = datetime.fromisoformat(
            metadata["checked_at"].replace("Z", "+00:00")
        )
    except ValueError as exc:
        raise ValueError("checked_at must be an ISO timestamp") from exc
    if checked_at.tzinfo is None:
        raise ValueError("checked_at must include a timezone offset")
    if checked_at.date() < period_end:
        raise ValueError("checked_at cannot be before period_end")
    if len(re.findall(r"^## Weekly Changes\s*$", text, flags=re.MULTILINE)) != 1:
        raise ValueError("weekly report must contain exactly one ## Weekly Changes section")
    if len(
        re.findall(
            r"^## Regulatory News & Market Commentary\s*$",
            text,
            flags=re.MULTILINE,
        )
    ) != 1:
        raise ValueError("weekly report must contain exactly one regulatory-news section")
    return metadata


def load_json_object(path: Path, label: str) -> dict[str, Any]:
    data = json.loads(path.expanduser().read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{label} root must be an object")
    return data


def membership_countries(data: dict[str, Any]) -> list[str]:
    values = data.get("countries")
    if not isinstance(values, list) or not values:
        raise ValueError("membership snapshot countries must be a non-empty list")
    countries: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("membership country names must be non-empty strings")
        country = value.strip()
        if country in seen:
            raise ValueError(f"duplicate membership country: {country}")
        seen.add(country)
        countries.append(country)
    if data.get("count") != len(countries):
        raise ValueError("membership snapshot count differs from countries")
    return countries


def validate_state_alignment(
    rows: list[list[str]], metadata: dict[str, str], state: dict[str, Any]
) -> None:
    if state.get("schema_version") != 1:
        raise ValueError("current state schema_version must be 1")
    if state.get("report_week") != metadata["report_week"]:
        raise ValueError("report_week differs between report and current state")
    if state.get("period_start") != metadata["period_start"]:
        raise ValueError("period_start differs between report and current state")
    if state.get("period_end") != metadata["period_end"]:
        raise ValueError("period_end differs between report and current state")
    if state.get("status_cutoff") != metadata["status_cutoff"]:
        raise ValueError("status_cutoff differs between report and current state")
    if state.get("checked_at") != metadata["checked_at"]:
        raise ValueError("checked_at differs between report and current state")
    countries = state.get("countries")
    if not isinstance(countries, dict):
        raise ValueError("current state countries must be an object")
    table_countries = {row[0] for row in rows}
    country_filter = parse_country_filter(metadata)
    if country_filter is None:
        if set(countries) != table_countries:
            raise ValueError("country set differs between report and current state")
    else:
        if table_countries != country_filter:
            raise ValueError("report rows differ from country_filter")
        if not table_countries.issubset(set(countries)):
            raise ValueError("filtered report contains a country absent from current state")
    for country, status, summary in rows:
        record = countries[country]
        if not isinstance(record, dict):
            raise ValueError(f"{country}: current state record must be an object")
        if record.get("status") != status:
            raise ValueError(f"{country}: status differs between report and current state")
        marker = record.get("commission_marker")
        if marker not in COMMISSION_MARKERS or marker not in summary:
            raise ValueError(
                f"{country}: Commission marker differs between report and current state"
            )
        if record.get("source_health") not in SOURCE_HEALTH:
            raise ValueError(f"{country}: invalid source_health in current state")
        urls = record.get("source_urls")
        if not isinstance(urls, list) or len(urls) < 2:
            raise ValueError(f"{country}: current state needs at least two source URLs")


def validate_diff_alignment(metadata: dict[str, str], diff: dict[str, Any]) -> None:
    if diff.get("schema_version") != 1:
        raise ValueError("weekly diff schema_version must be 1")
    if diff.get("report_week") != metadata["report_week"]:
        raise ValueError("report_week differs between report and weekly diff")
    if diff.get("change_count") != int(metadata["change_count"]):
        raise ValueError("change_count differs between report and weekly diff")
    baseline = diff.get("baseline") is True
    previous = metadata["previous_successful_week"]
    if baseline and previous != "none":
        raise ValueError("baseline report must use previous_successful_week: none")
    if not baseline and diff.get("previous_week") != previous:
        raise ValueError("previous week differs between report and weekly diff")


def validate(
    text: str,
    member_states: list[str] | set[str] | tuple[str, ...],
    allow_subset: bool = False,
) -> tuple[int, dict[str, int]]:
    rows = extract_rows(text)
    countries = [row[0] for row in rows]
    member_set = set(member_states)
    if not member_set:
        raise ValueError("dynamic membership set cannot be empty")
    errors: list[str] = []

    duplicates = sorted({country for country in countries if countries.count(country) > 1})
    if duplicates:
        errors.append(f"duplicate countries: {', '.join(duplicates)}")

    unknown = sorted(set(countries) - member_set)
    if unknown:
        errors.append(f"countries outside the dynamic EU membership: {', '.join(unknown)}")

    if allow_subset:
        if not set(countries).issubset(member_set):
            errors.append("filtered table contains a non-member country")
    else:
        missing = sorted(member_set - set(countries))
        if len(rows) != len(member_set) or missing:
            errors.append(
                "all-country table must match the dynamic EU membership snapshot"
                + (f"; missing: {', '.join(missing)}" if missing else "")
            )

    counts = {status: 0 for status in sorted(VALID_STATUSES)}
    for row_number, (country, status, summary) in enumerate(rows, start=1):
        label = country or f"row {row_number}"
        if status not in VALID_STATUSES:
            errors.append(f"{label}: invalid Current Status {status!r}")
        else:
            counts[status] += 1
        markers = [marker for marker in COMMISSION_MARKERS if marker in summary]
        if len(markers) != 1:
            errors.append(f"{label}: Summary must contain exactly one Commission marker")
        if not re.search(r"\b20\d{2}\b", summary):
            errors.append(f"{label}: Summary must contain a verified year")
        links = re.findall(r"\[[^\]]+\]\(https://[^)]+\)", summary)
        if len(links) < 2:
            errors.append(f"{label}: Summary must contain at least two HTTPS Markdown links")

    if errors:
        raise ValueError("\n".join(errors))
    return len(rows), counts


def self_test() -> None:
    member_states = ["Austria", "Czechia", "Germany"]
    rows = "\n".join(
        f"| {country} | Completed | Final measure confirmed in 2026. "
        "Commission: Full. [National source](https://example.com/national) "
        "[European Commission](https://example.com/commission) |"
        for country in member_states
    )
    valid = f"| Country | Current Status | Summary |\n|---|---|---|\n{rows}\n"
    count, counts = validate(valid, member_states)
    if count != 3 or counts["Completed"] != 3:
        raise AssertionError("valid all-country fixture did not validate")

    invalid = valid.replace("| Austria | Completed |", "| Austria | Finished |", 1)
    try:
        validate(invalid, member_states)
    except ValueError as exc:
        if "invalid Current Status" not in str(exc):
            raise AssertionError("invalid fixture failed for the wrong reason") from exc
    else:
        raise AssertionError("invalid status fixture unexpectedly validated")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", type=Path, help="Markdown report to validate")
    parser.add_argument(
        "--allow-subset",
        action="store_true",
        help="allow a filtered table containing a subset of current Member States",
    )
    parser.add_argument(
        "--membership",
        type=Path,
        help="validated membership-snapshot.json; required for report validation",
    )
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument(
        "--weekly",
        action="store_true",
        help="validate weekly frontmatter and Weekly Changes section",
    )
    parser.add_argument(
        "--state",
        type=Path,
        help="current-state.json to compare with the table; requires --weekly",
    )
    parser.add_argument(
        "--diff",
        type=Path,
        help="weekly-diff.json to compare with report metadata; requires --weekly",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.self_test:
        self_test()
        print("CRD_VI_TABLE_SELF_TEST_OK")
        return 0
    if args.file is None:
        raise ValueError("--file is required unless --self-test is used")
    if args.membership is None:
        raise ValueError("--membership is required for report validation")
    text = args.file.expanduser().read_text(encoding="utf-8")
    membership = load_json_object(args.membership, "membership snapshot")
    count, counts = validate(
        text,
        membership_countries(membership),
        allow_subset=args.allow_subset,
    )
    if (args.state or args.diff) and not args.weekly:
        raise ValueError("--state and --diff require --weekly")
    if args.weekly:
        metadata = validate_weekly(text)
        rows = extract_rows(text)
        if args.state:
            validate_state_alignment(
                rows, metadata, load_json_object(args.state, "current state")
            )
        if args.diff:
            validate_diff_alignment(
                metadata, load_json_object(args.diff, "weekly diff")
            )
    print(
        "CRD_VI_TABLE_OK "
        f"rows={count} completed={counts['Completed']} "
        f"ongoing={counts['Ongoing']} pending={counts['Pending']}"
        + (" weekly=true" if args.weekly else "")
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as exc:
        print(f"CRD_VI_TABLE_ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
