#!/usr/bin/env python3
"""Collect one country's Pipeline C Markdown reports into a monthly JSON index.

The script is deliberately read-only. It prints the index to stdout so the
orchestrator can persist it with apply_patch.
"""

from __future__ import annotations

import argparse
import calendar
from collections import Counter
from dataclasses import dataclass
from datetime import date
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any


LANGS = ("en", "zh", "ja")
CATEGORY_NAMES = {
    "en": {
        "econ": "Economy & Markets",
        "politics": "Politics & Diplomacy",
        "tech": "Technology & Industry",
        "society": "Society & Livelihood",
        "china_nexus": "China-Nexus Finance & Investment",
        "ipo_ma": "Corporate IPO & M&A",
        "other": "Other Notable Events",
    },
    "zh": {
        "econ": "经济与市场",
        "politics": "政治与外交",
        "tech": "科技与产业",
        "society": "社会与民生",
        "china_nexus": "海外涉华财经",
        "ipo_ma": "企业IPO与并购",
        "other": "其他重要事件",
    },
    "ja": {
        "econ": "経済と市場",
        "politics": "政治と外交",
        "tech": "テクノロジーと産業",
        "society": "社会と生活",
        "china_nexus": "海外の対中経済・投資",
        "ipo_ma": "企業のIPO・M&A",
        "other": "その他の重要事項",
    },
}
REFERENCE_RE = re.compile(r"^\[(?P<number>\d+)\]\s+(?P<text>.+)$")
URL_RE = re.compile(r"https?://\S+")
GAP_NOTE_RE = re.compile(r"^\*(?:注：|Note:).+\*$")
H2_RE = re.compile(r"^##\s+(?P<title>[^\n]+)\s*$", re.MULTILINE)
STORY_RE = re.compile(
    r"^###\s+(?P<title>[^\n]+)\n+"
    r"(?P<body>[\s\S]*?)\n+"
    r"\*\*References\*\*\n+"
    r"(?P<references>[\s\S]*?)"
    r"(?=^---\s*$|^###\s+|\Z)",
    re.MULTILINE,
)


class SourceError(ValueError):
    """Raised when source discovery or parsing cannot preserve provenance."""


@dataclass(frozen=True)
class LocatedReport:
    report_date: date
    lang: str
    display_country: str
    path: Path


def active_categories(country: str) -> list[str]:
    categories = ["econ", "politics", "tech", "society"]
    if country.casefold() == "china":
        categories.append("china_nexus")
    return categories + ["ipo_ma", "other"]


def parse_month(value: str) -> tuple[int, int]:
    match = re.fullmatch(r"(\d{4})-(\d{2})", value)
    if not match:
        raise SourceError("--month must use ISO YYYY-MM")
    year, month = (int(part) for part in match.groups())
    if not 1 <= month <= 12:
        raise SourceError("--month contains an invalid month number")
    return year, month


def parse_aliases(values: list[str], country: str) -> dict[str, str]:
    aliases: dict[str, str] = {"en": country.strip()}
    for value in values:
        if "=" not in value:
            raise SourceError("--country-alias must use LANG=DISPLAY")
        lang, display = value.split("=", 1)
        lang = lang.strip()
        display = display.strip()
        if lang not in LANGS or not display:
            raise SourceError(
                "--country-alias language must be en, zh, or ja and display cannot be empty"
            )
        aliases[lang] = display
    return aliases


def filename_for(lang: str, display_country: str, report_date: date) -> str:
    iso_date = report_date.isoformat()
    if lang == "en":
        return f"{display_country}-daily-news-{iso_date}.md"
    if lang == "zh":
        return f"{display_country}每日热点新闻-{iso_date}.md"
    return f"{display_country}デイリーニュース-{iso_date}.md"


def expected_h1(lang: str, display_country: str, report_date: date) -> str:
    if lang == "en":
        display_date = (
            f"{calendar.month_name[report_date.month]} "
            f"{report_date.day}, {report_date.year}"
        )
        return (
            f"# {display_country} Daily News Intelligence — {display_date}"
        )
    display_date = (
        f"{report_date.year}年{report_date.month}月{report_date.day}日"
    )
    if lang == "zh":
        return f"# {display_country}每日热点新闻 — {display_date}"
    return f"# {display_country}デイリーニュース — {display_date}"


def normalize_h2(title: str, lang: str) -> str:
    if lang == "zh":
        return re.sub(r"^[一二三四五六七]、", "", title).strip()
    return re.sub(r"^\d+\.\s*", "", title).strip()


def category_from_h2(title: str, lang: str) -> str:
    normalized = normalize_h2(title, lang)
    for category, display in CATEGORY_NAMES[lang].items():
        if normalized == display:
            return category
    raise SourceError(f"unrecognized {lang} H2 category: {title}")


def parse_reference_lines(raw: str, path: Path, story_title: str) -> list[dict[str, Any]]:
    references: list[dict[str, Any]] = []
    for line in (item.strip() for item in raw.splitlines()):
        if not line:
            continue
        if GAP_NOTE_RE.fullmatch(line):
            continue
        match = REFERENCE_RE.fullmatch(line)
        if not match:
            raise SourceError(
                f"{path}: story {story_title!r} contains a malformed reference line: {line}"
            )
        urls = URL_RE.findall(match.group("text"))
        if not urls:
            raise SourceError(
                f"{path}: story {story_title!r} contains a reference without URL"
            )
        references.append(
            {
                "source_number": int(match.group("number")),
                "apa": match.group("text"),
                "url": urls[-1].rstrip(".,;"),
            }
        )
    if not references:
        raise SourceError(
            f"{path}: story {story_title!r} has no usable references"
        )
    return references


def parse_report(
    located: LocatedReport,
    country: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    try:
        content = located.path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SourceError(f"cannot read {located.path}: {exc}") from exc

    first_line = next(
        (line.strip() for line in content.splitlines() if line.strip()),
        "",
    )
    required_h1 = expected_h1(
        located.lang, located.display_country, located.report_date
    )
    if first_line != required_h1:
        raise SourceError(
            f"{located.path}: unexpected H1; expected {required_h1!r}, got {first_line!r}"
        )

    headings = list(H2_RE.finditer(content))
    categories = [
        category_from_h2(match.group("title"), located.lang)
        for match in headings
    ]
    expected_categories = active_categories(country)
    if categories != expected_categories:
        raise SourceError(
            f"{located.path}: category order {categories} does not match "
            f"{expected_categories}"
        )

    stories: list[dict[str, Any]] = []
    category_counts: Counter[str] = Counter()
    for index, heading in enumerate(headings):
        category = categories[index]
        section_end = (
            headings[index + 1].start()
            if index + 1 < len(headings)
            else len(content)
        )
        section = content[heading.end() : section_end]
        for story_index, match in enumerate(STORY_RE.finditer(section), start=1):
            title = match.group("title").strip()
            body = match.group("body").strip()
            if not body:
                raise SourceError(
                    f"{located.path}: story {title!r} has an empty body"
                )
            references = parse_reference_lines(
                match.group("references"),
                located.path,
                title,
            )
            story_id = (
                f"{located.report_date.isoformat()}:{category}:{story_index:02d}"
            )
            stories.append(
                {
                    "id": story_id,
                    "source_date": located.report_date.isoformat(),
                    "source_lang": located.lang,
                    "source_path": str(located.path),
                    "category": category,
                    "source_order": story_index,
                    "title": title,
                    "body": body,
                    "references": references,
                }
            )
            category_counts[category] += 1

    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    report = {
        "date": located.report_date.isoformat(),
        "lang": located.lang,
        "path": str(located.path),
        "sha256": digest,
        "story_count": len(stories),
        "category_story_counts": {
            category: category_counts[category]
            for category in expected_categories
        },
    }
    return report, stories


def language_priority(
    source_lang: str,
    preferred_lang: str,
    aliases: dict[str, str],
) -> list[str]:
    if source_lang != "auto":
        if source_lang not in aliases:
            raise SourceError(
                f"no --country-alias was provided for source language {source_lang}"
            )
        return [source_lang]
    ordered = [preferred_lang, "en", "zh", "ja"]
    return list(dict.fromkeys(lang for lang in ordered if lang in aliases))


def locate_report(
    source_dir: Path,
    report_date: date,
    priority: list[str],
    aliases: dict[str, str],
) -> LocatedReport | None:
    date_dir = source_dir / report_date.isoformat()
    for lang in priority:
        display_country = aliases[lang]
        path = date_dir / filename_for(lang, display_country, report_date)
        if path.is_file():
            return LocatedReport(report_date, lang, display_country, path.resolve())
    return None


def build_index(args: argparse.Namespace) -> dict[str, Any]:
    country = args.country.strip()
    if not country:
        raise SourceError("--country cannot be empty")
    year, month = parse_month(args.month)
    aliases = parse_aliases(args.country_alias, country)
    priority = language_priority(
        args.source_lang, args.preferred_lang, aliases
    )
    source_dir = args.source_dir.expanduser().resolve()
    if not source_dir.is_dir():
        raise SourceError(f"source directory does not exist: {source_dir}")

    try:
        as_of = date.fromisoformat(args.as_of)
    except ValueError as exc:
        raise SourceError("--as-of must use ISO YYYY-MM-DD") from exc
    month_start = date(year, month, 1)
    month_end = date(year, month, calendar.monthrange(year, month)[1])
    if month_start > as_of:
        raise SourceError(
            f"requested month {args.month} begins after --as-of {as_of}"
        )
    period_end = min(month_end, as_of)

    dates: list[date] = []
    current = month_start
    while current <= period_end:
        dates.append(current)
        current = date.fromordinal(current.toordinal() + 1)

    reports: list[dict[str, Any]] = []
    stories: list[dict[str, Any]] = []
    found_dates: list[str] = []
    missing_dates: list[str] = []
    for report_date in dates:
        located = locate_report(
            source_dir, report_date, priority, aliases
        )
        if located is None:
            missing_dates.append(report_date.isoformat())
            continue
        report, report_stories = parse_report(located, country)
        reports.append(report)
        stories.extend(report_stories)
        found_dates.append(report_date.isoformat())

    categories = active_categories(country)
    story_counts = Counter(story["category"] for story in stories)
    return {
        "schema_version": 1,
        "country": country,
        "country_aliases": aliases,
        "month": args.month,
        "as_of": as_of.isoformat(),
        "source_dir": str(source_dir),
        "source_lang": args.source_lang,
        "preferred_lang": args.preferred_lang,
        "language_priority": priority,
        "active_categories": categories,
        "coverage": {
            "period_start": month_start.isoformat(),
            "period_end": period_end.isoformat(),
            "calendar_month_end": month_end.isoformat(),
            "partial_calendar_month": period_end < month_end,
            "calendar_days_considered": len(dates),
            "reports_found": len(reports),
            "coverage_complete": len(reports) == len(dates),
            "dates_found": found_dates,
            "missing_dates": missing_dates,
        },
        "counts": {
            "reports": len(reports),
            "stories": len(stories),
            "stories_by_category": {
                category: story_counts[category]
                for category in categories
            },
        },
        "reports": reports,
        "stories": stories,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--country", required=True)
    parser.add_argument("--month", required=True, help="ISO YYYY-MM")
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=Path("~/.sci-research/reports/daily-news/"),
    )
    parser.add_argument(
        "--source-lang",
        choices=("auto",) + LANGS,
        default="auto",
        help="Use one language only, or auto-select one report per date",
    )
    parser.add_argument(
        "--preferred-lang",
        choices=LANGS,
        default="en",
        help="First language tried when --source-lang=auto",
    )
    parser.add_argument(
        "--country-alias",
        action="append",
        default=[],
        metavar="LANG=DISPLAY",
        help="Localized country display used in Pipeline C filenames",
    )
    parser.add_argument(
        "--as-of",
        default=date.today().isoformat(),
        help="Upper date boundary for current-month runs (default: today)",
    )
    return parser.parse_args()


def main() -> int:
    try:
        index = build_index(parse_args())
    except (OSError, SourceError) as exc:
        print(f"MONTHLY_SOURCE_ERROR: {exc}", file=sys.stderr)
        return 2
    json.dump(index, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
