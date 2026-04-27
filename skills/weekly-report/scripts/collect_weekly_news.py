#!/usr/bin/env python3
"""Collect last-7-days daily-news-intelligence reports as the news basis.

Walks NEWS_DIR for files like:
  zh: ``{country_zh}每日热点新闻-{YYYY-MM-DD}.md``
  en: ``{country_en}-daily-news-{YYYY-MM-DD}.md``
  ja: ``{country_ja}デイリーニュース-{YYYY-MM-DD}.md``

For each file in [start_date, end_date], extracts the H2 sections and the
H3 stories beneath them along with associated **References** APA blocks.
Emits a JSON document grouped by country code (CN/US/UK/EU/JP/KR/...).
"""

from __future__ import annotations

import argparse
import os
import re
from datetime import date
from pathlib import Path
from typing import Any

from _common import build_window_payload, date_range, emit, resolve_window

# Country code <-> per-language display name table.
# Keep extensible; weekly-report defaults to: CN, US, UK, EU, JP, KR.
COUNTRY_TABLE: dict[str, dict[str, str]] = {
    "CN": {"zh": "中国",       "en": "China",          "ja": "中国"},
    "US": {"zh": "美国",       "en": "United States",  "ja": "米国"},
    "UK": {"zh": "英国",       "en": "United Kingdom", "ja": "英国"},
    "EU": {"zh": "欧洲",       "en": "Europe",         "ja": "欧州"},
    "JP": {"zh": "日本",       "en": "Japan",          "ja": "日本"},
    "KR": {"zh": "韩国",       "en": "South Korea",    "ja": "韓国"},
    "DE": {"zh": "德国",       "en": "Germany",        "ja": "ドイツ"},
    "FR": {"zh": "法国",       "en": "France",         "ja": "フランス"},
    "IN": {"zh": "印度",       "en": "India",          "ja": "インド"},
    "RU": {"zh": "俄罗斯",     "en": "Russia",         "ja": "ロシア"},
}

# Reverse table: display name -> country code
DISPLAY_TO_CODE: dict[str, str] = {}
for code, names in COUNTRY_TABLE.items():
    for name in names.values():
        DISPLAY_TO_CODE[name] = code

DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")
URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)


def filename_pattern(lang: str) -> re.Pattern[str]:
    if lang == "zh":
        return re.compile(r"^(?P<country>.+?)每日热点新闻-(?P<date>\d{4}-\d{2}-\d{2})\.md$")
    if lang == "en":
        return re.compile(r"^(?P<country>.+?)-daily-news-(?P<date>\d{4}-\d{2}-\d{2})\.md$")
    if lang == "ja":
        return re.compile(r"^(?P<country>.+?)デイリーニュース-(?P<date>\d{4}-\d{2}-\d{2})\.md$")
    raise ValueError(f"Unsupported lang: {lang}")


def find_files(news_dir: Path, lang: str, start: str, end: str) -> list[dict[str, str]]:
    pattern = filename_pattern(lang)
    valid_dates = set(date_range(start, end))
    out: list[dict[str, str]] = []
    if not news_dir.exists():
        return out
    for entry in sorted(news_dir.iterdir()):
        if not entry.is_file() or entry.suffix != ".md":
            continue
        m = pattern.match(entry.name)
        if not m:
            continue
        d = m.group("date")
        if d not in valid_dates:
            continue
        country_display = m.group("country")
        country_code = DISPLAY_TO_CODE.get(country_display, country_display.upper()[:2])
        out.append(
            {
                "path": str(entry),
                "filename": entry.name,
                "date": d,
                "country_display": country_display,
                "country": country_code,
                "lang": lang,
            }
        )
    return out


def parse_report(path: str) -> list[dict[str, Any]]:
    """Parse a daily report MD into a list of stories.

    Returns: [{"section_h2": "...", "title": "...", "summary": "...", "analysis": "...",
               "references": [{"raw": "...", "url": "..."}]}, ...]
    """
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()

    stories: list[dict[str, Any]] = []
    current_h2: str = ""
    current_story: dict[str, Any] | None = None
    current_block: str | None = None  # one of: 'summary', 'analysis', 'references'
    buffers: dict[str, list[str]] = {"summary": [], "analysis": [], "references": []}

    def flush_story() -> None:
        nonlocal current_story, buffers
        if not current_story:
            return
        summary = "\n".join(buffers["summary"]).strip()
        analysis = "\n".join(buffers["analysis"]).strip()
        ref_block = "\n".join(buffers["references"]).strip()
        refs: list[dict[str, str]] = []
        if ref_block:
            for raw_line in ref_block.splitlines():
                raw = raw_line.strip()
                if not raw:
                    continue
                url_match = URL_RE.search(raw)
                refs.append({"raw": raw, "url": url_match.group(0) if url_match else ""})
        current_story["summary"] = summary
        current_story["analysis"] = analysis
        current_story["references"] = refs
        stories.append(current_story)
        current_story = None
        buffers = {"summary": [], "analysis": [], "references": []}

    for raw_line in lines:
        line = raw_line.rstrip()
        if line.startswith("## "):
            flush_story()
            current_h2 = line[3:].strip()
            current_block = None
            continue
        if line.startswith("### "):
            flush_story()
            current_story = {
                "section_h2": current_h2,
                "title": line[4:].strip(),
            }
            current_block = None
            continue
        if not current_story:
            continue
        stripped = line.strip()
        if stripped in ("**摘要**", "**Summary**", "**要約**"):
            current_block = "summary"
            continue
        if stripped in ("**分析**", "**Analysis**"):
            current_block = "analysis"
            continue
        if stripped == "**References**":
            current_block = "references"
            continue
        if stripped.startswith("---"):
            flush_story()
            current_block = None
            continue
        if current_block:
            buffers[current_block].append(line)

    flush_story()
    return stories


def is_economy_section(h2: str) -> bool:
    """Return True if this H2 belongs to the Economy & Markets category."""
    if not h2:
        return False
    text = h2.strip()
    # zh: "一、经济与市场" / en: "1. Economy & Markets" / ja: "1. 経済と市場"
    return any(
        marker in text
        for marker in ("经济与市场", "Economy & Markets", "経済と市場")
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect daily-news-reports for the past week.")
    parser.add_argument("--news-dir", default=os.path.expanduser("~/Desktop/daily-news-reports"))
    parser.add_argument("--start-date", help="ISO YYYY-MM-DD")
    parser.add_argument("--end-date", help="ISO YYYY-MM-DD; default today")
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--countries", default="CN,US,UK,EU,JP,KR")
    parser.add_argument("--lang", default="zh", choices=["zh", "en", "ja"])
    parser.add_argument(
        "--economy-only",
        action="store_true",
        default=True,
        help="Filter stories to the Economy & Markets section (default on; matches Market event scope)",
    )
    parser.add_argument(
        "--include-all-sections",
        dest="economy_only",
        action="store_false",
        help="Include all H2 sections (politics, technology, etc.)",
    )
    args = parser.parse_args()

    start, end = resolve_window(args.start_date, args.end_date, days=args.days)
    countries = [c.strip().upper() for c in args.countries.split(",") if c.strip()]
    news_dir = Path(args.news_dir).expanduser()

    files = find_files(news_dir, args.lang, start, end)
    files_by_country: dict[str, list[dict[str, str]]] = {c: [] for c in countries}
    for f in files:
        if f["country"] in files_by_country:
            files_by_country[f["country"]].append(f)
        else:
            files_by_country.setdefault(f["country"], []).append(f)

    events_by_country: dict[str, list[dict[str, Any]]] = {c: [] for c in countries}
    data_gaps: list[str] = []

    expected_dates = list(date_range(start, end))
    for country in countries:
        country_files = sorted(files_by_country.get(country, []), key=lambda f: f["date"])
        seen_dates = {f["date"] for f in country_files}
        for d in expected_dates:
            if d not in seen_dates:
                data_gaps.append(f"No daily file found for {country} on {d}")
        for f in country_files:
            try:
                stories = parse_report(f["path"])
            except Exception as exc:
                data_gaps.append(f"Parse failed for {f['filename']}: {exc}")
                continue
            for story in stories:
                if args.economy_only and not is_economy_section(story.get("section_h2", "")):
                    continue
                events_by_country[country].append(
                    {
                        "country": country,
                        "country_display": f["country_display"],
                        "date": f["date"],
                        "section_h2": story.get("section_h2", ""),
                        "title": story.get("title", ""),
                        "summary": story.get("summary", ""),
                        "analysis": story.get("analysis", ""),
                        "references": story.get("references", []),
                        "source_file": f["filename"],
                    }
                )

    emit(
        {
            "window": build_window_payload(start, end),
            "lang": args.lang,
            "countries": countries,
            "news_dir": str(news_dir),
            "files_consumed": files,
            "events_by_country": events_by_country,
            "summary": {
                "files_count": len(files),
                "events_count": sum(len(v) for v in events_by_country.values()),
                "events_per_country": {c: len(v) for c, v in events_by_country.items()},
            },
            "data_gaps": data_gaps,
            "filter": {"economy_only": bool(args.economy_only)},
        }
    )


if __name__ == "__main__":
    main()
