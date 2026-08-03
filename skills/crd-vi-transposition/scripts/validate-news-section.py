#!/usr/bin/env python3
"""Validate the weekly CRD VI regulatory-news section and selected items."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import re
import sys
from typing import Any


NEWS_HEADING = "## Regulatory News & Market Commentary"
NEWS_HEADER = ["Date", "Country/Region", "Development", "Practical Impact", "Sources"]
COUNTRY_HEADER = "| Country | Current Status | Summary |"
DISCLAIMER_HEADING = "## Disclaimer"
NO_NEWS_TEXT = "No material CRD VI news identified for this reporting period."
SOURCE_CLASSES = {"official", "news_media", "industry", "professional_analysis"}
STATUS_EFFECTS = {"none", "official_follow_up"}
DEFAULT_SOURCES = Path(__file__).resolve().parents[1] / "references/news-sources.json"


def split_row(line: str) -> list[str] | None:
    stripped = line.strip()
    if not (stripped.startswith("|") and stripped.endswith("|")):
        return None
    return [cell.strip() for cell in stripped[1:-1].split("|")]


def is_separator(cells: list[str] | None) -> bool:
    return bool(
        cells
        and len(cells) == 5
        and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)
    )


def parse_frontmatter(text: str) -> dict[str, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("weekly report must start with frontmatter")
    try:
        closing = lines.index("---", 1)
    except ValueError as exc:
        raise ValueError("weekly frontmatter is not closed") from exc
    result: dict[str, str] = {}
    for line in lines[1:closing]:
        if not line.strip():
            continue
        if ":" not in line:
            raise ValueError(f"invalid frontmatter line: {line}")
        key, value = line.split(":", 1)
        result[key.strip()] = value.strip().strip('"').strip("'")
    required = {"report_week", "period_start", "period_end", "news_count"}
    missing = sorted(required - set(result))
    if missing:
        raise ValueError(f"news frontmatter missing: {', '.join(missing)}")
    return result


def extract_news_rows(text: str) -> list[list[str]]:
    lines = text.splitlines()
    weekly_indexes = [
        index for index, line in enumerate(lines) if line.strip() == "## Weekly Changes"
    ]
    if len(weekly_indexes) != 1:
        raise ValueError("expected exactly one ## Weekly Changes section")
    headings = [index for index, line in enumerate(lines) if line.strip() == NEWS_HEADING]
    if len(headings) != 1:
        raise ValueError(f"expected exactly one {NEWS_HEADING} section")
    heading_index = headings[0]
    if heading_index <= weekly_indexes[0]:
        raise ValueError("regulatory news must appear after Weekly Changes")
    country_indexes = [
        index for index, line in enumerate(lines) if line.strip() == COUNTRY_HEADER
    ]
    if len(country_indexes) != 1 or country_indexes[0] <= heading_index:
        raise ValueError("regulatory news must appear before the country table")
    section = lines[heading_index + 1 : country_indexes[0]]
    header_indexes = [index for index, line in enumerate(section) if split_row(line) == NEWS_HEADER]
    if not header_indexes:
        return []
    if len(header_indexes) != 1:
        raise ValueError("expected at most one regulatory-news table")
    header_index = header_indexes[0]
    if header_index + 1 >= len(section) or not is_separator(split_row(section[header_index + 1])):
        raise ValueError("regulatory-news header lacks a valid five-column separator")
    rows: list[list[str]] = []
    for line in section[header_index + 2 :]:
        cells = split_row(line)
        if cells is None:
            if rows:
                break
            if line.strip():
                raise ValueError("unexpected content before the first regulatory-news row")
            continue
        if len(cells) != 5:
            raise ValueError("regulatory-news row must have exactly five columns")
        rows.append(cells)
    return rows


def markdown_urls(value: str) -> list[str]:
    return re.findall(r"\[[^\]]+\]\((https://[^)]+)\)", value)


def validate_disclaimer(text: str) -> None:
    lines = text.splitlines()
    headings = [index for index, line in enumerate(lines) if line.strip() == DISCLAIMER_HEADING]
    if len(headings) != 1:
        raise ValueError(f"expected exactly one {DISCLAIMER_HEADING} section")
    heading_index = headings[0]
    country_indexes = [
        index for index, line in enumerate(lines) if line.strip() == COUNTRY_HEADER
    ]
    if len(country_indexes) != 1 or heading_index <= country_indexes[0]:
        raise ValueError("disclaimer must appear after the country table")
    later_h2 = [
        index
        for index, line in enumerate(lines)
        if index > heading_index and re.fullmatch(r"## .+", line.strip())
    ]
    if later_h2:
        raise ValueError("disclaimer must be the final level-two section")
    body = "\n".join(lines[heading_index + 1 :]).casefold()
    if not (
        any(marker in body for marker in ("ai-assisted", "ai-generated", "artificial intelligence"))
        or re.search(r"\bai\b", body)
    ):
        raise ValueError("disclaimer must disclose AI assistance")
    if not any(marker in body for marker in ("workflow", "sources", "reporting period")):
        raise ValueError("disclaimer must summarize the report workflow")
    if not any(marker in body for marker in ("not legal", "professional advice", "not a substitute")):
        raise ValueError("disclaimer must state that the report is not professional advice")


def validate_report(text: str) -> tuple[dict[str, str], list[list[str]]]:
    metadata = parse_frontmatter(text)
    validate_disclaimer(text)
    try:
        period_start = date.fromisoformat(metadata["period_start"])
        period_end = date.fromisoformat(metadata["period_end"])
        news_count = int(metadata["news_count"])
    except ValueError as exc:
        raise ValueError("news dates/count have invalid format") from exc
    if news_count < 0 or news_count > 8:
        raise ValueError("news_count must be between 0 and 8")
    rows = extract_news_rows(text)
    if len(rows) != news_count:
        raise ValueError("news_count differs from the rendered news rows")
    section_start = text.index(NEWS_HEADING)
    section_end = text.index(COUNTRY_HEADER)
    section_text = text[section_start:section_end]
    if news_count == 0:
        if NO_NEWS_TEXT not in section_text:
            raise ValueError("zero-news report must contain the exact no-news statement")
        return metadata, rows
    if NO_NEWS_TEXT in section_text:
        raise ValueError("non-empty news section cannot contain the no-news statement")

    seen_primary_urls: set[str] = set()
    for number, (date_value, region, development, impact, sources) in enumerate(rows, start=1):
        try:
            published = date.fromisoformat(date_value)
        except ValueError as exc:
            raise ValueError(f"news row {number}: Date must be YYYY-MM-DD") from exc
        if not period_start <= published <= period_end:
            raise ValueError(f"news row {number}: Date falls outside the reporting week")
        if not region or len(development) < 15 or len(impact) < 15:
            raise ValueError(f"news row {number}: region, development, or impact is too thin")
        urls = markdown_urls(sources)
        if not 1 <= len(urls) <= 3:
            raise ValueError(f"news row {number}: Sources must contain one to three links")
        if any("news.google.com" in url for url in urls):
            raise ValueError(f"news row {number}: Google News redirect is not a final source")
        if urls[0] in seen_primary_urls:
            raise ValueError(f"news row {number}: duplicate primary source/event")
        seen_primary_urls.add(urls[0])
    return metadata, rows


def load_items(path: Path) -> dict[str, Any]:
    data = json.loads(path.expanduser().read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("news-items root must be an object")
    return data


def load_state(path: Path) -> dict[str, Any]:
    data = json.loads(path.expanduser().read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("current-state root must be an object")
    return data


def validate_audit(
    data: dict[str, Any],
    metadata: dict[str, str],
    registry: dict[str, Any],
) -> None:
    if data.get("schema_version") != 1:
        raise ValueError("news-search-audit schema_version must be 1")
    for field in ("report_week", "period_start", "period_end"):
        if data.get(field) != metadata[field]:
            raise ValueError(f"{field} differs between report and news-search-audit")

    expected_lanes = registry.get("search_lanes")
    if not isinstance(expected_lanes, list) or not expected_lanes:
        raise ValueError("news-sources.json must contain search_lanes")
    expected_ids = {
        lane.get("id") for lane in expected_lanes if isinstance(lane, dict)
    }
    lanes = data.get("lanes")
    if not isinstance(lanes, list) or len(lanes) != len(expected_ids):
        raise ValueError("news-search-audit must contain every active search lane")
    seen_lanes: set[str] = set()
    for lane in lanes:
        if not isinstance(lane, dict):
            raise ValueError("news-search-audit lanes must be objects")
        lane_id = lane.get("id")
        if lane_id not in expected_ids or lane_id in seen_lanes:
            raise ValueError("news-search-audit contains an unknown or duplicate lane")
        seen_lanes.add(lane_id)
        queries = lane.get("queries")
        if not isinstance(queries, list) or not queries or not all(
            isinstance(query, str) and query.strip() for query in queries
        ):
            raise ValueError(f"{lane_id}: queries must be non-empty strings")
        result_count = lane.get("result_count")
        if not isinstance(result_count, int) or isinstance(result_count, bool) or result_count < 0:
            raise ValueError(f"{lane_id}: result_count must be a non-negative integer")
    if seen_lanes != expected_ids:
        raise ValueError("news-search-audit is missing an active search lane")

    candidates = data.get("candidates")
    if not isinstance(candidates, list):
        raise ValueError("news-search-audit candidates must be a list")
    for number, candidate in enumerate(candidates, start=1):
        if not isinstance(candidate, dict):
            raise ValueError(f"news candidate {number} must be an object")
        url = candidate.get("url")
        if not isinstance(url, str) or not url.startswith("https://"):
            raise ValueError(f"news candidate {number}: url must be HTTPS")
        published_date = candidate.get("published_date")
        if published_date is not None:
            try:
                date.fromisoformat(published_date)
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"news candidate {number}: published_date must be YYYY-MM-DD or null"
                ) from exc
        if candidate.get("decision") not in {"keep", "drop"}:
            raise ValueError(f"news candidate {number}: decision must be keep or drop")
        if not isinstance(candidate.get("reason"), str) or not candidate["reason"].strip():
            raise ValueError(f"news candidate {number}: reason is required")


def official_state_urls(data: dict[str, Any]) -> set[str]:
    countries = data.get("countries")
    if not isinstance(countries, dict):
        raise ValueError("current-state must contain a countries object")
    urls: set[str] = set()
    for country, record in countries.items():
        if not isinstance(country, str) or not isinstance(record, dict):
            raise ValueError("current-state country records must be objects")
        source_urls = record.get("source_urls")
        if not isinstance(source_urls, list) or not all(
            isinstance(url, str) and url.startswith("https://") for url in source_urls
        ):
            raise ValueError(f"current-state {country}: invalid source_urls")
        urls.update(source_urls)
    return urls


def validate_items(
    metadata: dict[str, str],
    rows: list[list[str]],
    data: dict[str, Any],
    state: dict[str, Any] | None = None,
) -> None:
    state_urls = official_state_urls(state) if state is not None else None
    if data.get("schema_version") != 1:
        raise ValueError("news-items schema_version must be 1")
    for field in ("report_week", "period_start", "period_end"):
        if data.get(field) != metadata[field]:
            raise ValueError(f"{field} differs between report and news-items")
    items = data.get("items")
    if not isinstance(items, list) or len(items) != len(rows):
        raise ValueError("news-items count differs from report")
    for number, (row, item) in enumerate(zip(rows, items, strict=True), start=1):
        if not isinstance(item, dict):
            raise ValueError(f"news item {number}: item must be an object")
        date_value, region, development, impact, sources = row
        expected = {
            "date": date_value,
            "country_region": region,
            "development": development,
            "practical_impact": impact,
        }
        for field, value in expected.items():
            if item.get(field) != value:
                raise ValueError(f"news item {number}: {field} differs from report")
        if item.get("source_class") not in SOURCE_CLASSES:
            raise ValueError(f"news item {number}: invalid source_class")
        if item.get("status_effect") not in STATUS_EFFECTS:
            raise ValueError(f"news item {number}: invalid status_effect")
        urls = item.get("source_urls")
        if not isinstance(urls, list) or urls != markdown_urls(sources):
            raise ValueError(f"news item {number}: source_urls differ from report")
        if item.get("status_effect") == "official_follow_up":
            follow_up = item.get("official_follow_up_url")
            if not isinstance(follow_up, str) or not follow_up.startswith("https://"):
                raise ValueError(
                    f"news item {number}: official_follow_up requires an official URL"
                )
            if state_urls is not None and follow_up not in state_urls:
                raise ValueError(
                    f"news item {number}: official follow-up URL is absent from current-state"
                )


def self_test() -> None:
    report = """---
report_week: 2026-W31
period_start: 2026-07-27
period_end: 2026-08-02
news_count: 1
---

## Weekly Changes

No material country changes.

## Regulatory News & Market Commentary

| Date | Country/Region | Development | Practical Impact | Sources |
|---|---|---|---|---|
| 2026-07-30 | EU | EBA published a final branch reporting package. | Third-country banks should update reporting implementation plans. | [EBA](https://eba.europa.eu/item) |

| Country | Current Status | Summary |
|---|---|---|
| Austria | Ongoing | Example 2026. Commission: Partial. [A](https://a.example) [B](https://b.example) |
"""
    metadata, rows = validate_report(report)
    if metadata["news_count"] != "1" or len(rows) != 1:
        raise AssertionError("valid news fixture did not validate")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", type=Path)
    parser.add_argument("--items", type=Path)
    parser.add_argument("--state", type=Path)
    parser.add_argument("--audit", type=Path)
    parser.add_argument("--sources", type=Path, default=DEFAULT_SOURCES)
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.self_test:
        self_test()
        print("CRD_VI_NEWS_SELF_TEST_OK")
        return 0
    if args.file is None:
        raise ValueError("--file is required unless --self-test is used")
    text = args.file.expanduser().read_text(encoding="utf-8")
    metadata, rows = validate_report(text)
    if args.items:
        state = load_state(args.state) if args.state else None
        validate_items(metadata, rows, load_items(args.items), state)
    elif args.state:
        raise ValueError("--state requires --items")
    if args.audit:
        validate_audit(
            load_items(args.audit),
            metadata,
            load_items(args.sources),
        )
    print(f"CRD_VI_NEWS_OK rows={len(rows)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"CRD_VI_NEWS_ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
