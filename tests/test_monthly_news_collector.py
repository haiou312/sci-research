from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
COLLECTOR = (
    REPO_ROOT
    / "skills/monthly-news-intelligence/scripts/collect-monthly-reports.py"
)

CATEGORIES = {
    "en": [
        "1. Economy & Markets",
        "2. Politics & Diplomacy",
        "3. Technology & Industry",
        "4. Society & Livelihood",
        "5. Corporate IPO & M&A",
        "6. Other Notable Events",
    ],
    "zh": [
        "一、经济与市场",
        "二、政治与外交",
        "三、科技与产业",
        "四、社会与民生",
        "五、企业IPO与并购",
        "六、其他重要事件",
    ],
}


def report_text(
    *,
    lang: str,
    country_display: str,
    iso_date: str,
    categories: list[str] | None = None,
) -> str:
    year, month, day = (int(part) for part in iso_date.split("-"))
    if lang == "en":
        h1 = (
            f"# {country_display} Daily News Intelligence — "
            f"July {day}, {year}"
        )
    else:
        h1 = (
            f"# {country_display}每日热点新闻 — "
            f"{year}年{month}月{day}日"
        )
    blocks = [h1]
    for number, heading in enumerate(categories or CATEGORIES[lang], start=1):
        blocks.append(
            "\n".join(
                [
                    f"## {heading}",
                    "",
                    f"### Story {number} {lang}",
                    "",
                    f"Factual body {number}.",
                    "",
                    "**References**",
                    "",
                    (
                        f"[{number}] Reuters. (2026, July {day}). "
                        f"Story {number}. Reuters. "
                        f"https://example.com/{iso_date}/{lang}/{number}"
                    ),
                    "",
                    "---",
                ]
            )
        )
    return "\n\n".join(blocks) + "\n"


def filename(lang: str, display: str, iso_date: str) -> str:
    if lang == "en":
        return f"{display}-daily-news-{iso_date}.md"
    return f"{display}每日热点新闻-{iso_date}.md"


class MonthlyCollectorTests(unittest.TestCase):
    def run_collector(
        self,
        source_dir: Path,
        *extra: str,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(COLLECTOR),
                "--country",
                "United Kingdom",
                "--month",
                "2026-07",
                "--source-dir",
                str(source_dir),
                "--as-of",
                "2026-07-02",
                "--country-alias",
                "zh=英国",
                *extra,
            ],
            check=False,
            capture_output=True,
            text=True,
        )

    def write_report(
        self,
        source_dir: Path,
        iso_date: str,
        lang: str,
        display: str,
        *,
        categories: list[str] | None = None,
    ) -> Path:
        date_dir = source_dir / iso_date
        date_dir.mkdir(parents=True, exist_ok=True)
        path = date_dir / filename(lang, display, iso_date)
        path.write_text(
            report_text(
                lang=lang,
                country_display=display,
                iso_date=iso_date,
                categories=categories,
            ),
            encoding="utf-8",
        )
        return path

    def test_auto_uses_one_preferred_report_per_date(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir)
            self.write_report(
                source_dir, "2026-07-01", "en", "United Kingdom"
            )
            selected = self.write_report(
                source_dir, "2026-07-01", "zh", "英国"
            )
            result = self.run_collector(
                source_dir, "--preferred-lang", "zh"
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            index = json.loads(result.stdout)
            self.assertEqual(index["coverage"]["reports_found"], 1)
            self.assertEqual(index["counts"]["stories"], 6)
            self.assertEqual(index["reports"][0]["lang"], "zh")
            self.assertEqual(index["reports"][0]["path"], str(selected.resolve()))
            self.assertEqual(
                index["stories"][0]["id"], "2026-07-01:econ:01"
            )

    def test_auto_falls_back_to_english_and_records_missing_dates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir)
            self.write_report(
                source_dir, "2026-07-01", "en", "United Kingdom"
            )
            result = self.run_collector(
                source_dir, "--preferred-lang", "zh"
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            index = json.loads(result.stdout)
            self.assertEqual(index["reports"][0]["lang"], "en")
            self.assertEqual(
                index["coverage"]["missing_dates"], ["2026-07-02"]
            )
            self.assertFalse(index["coverage"]["coverage_complete"])

    def test_explicit_language_does_not_fall_back(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir)
            self.write_report(
                source_dir, "2026-07-01", "en", "United Kingdom"
            )
            result = self.run_collector(
                source_dir,
                "--source-lang",
                "zh",
                "--preferred-lang",
                "zh",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            index = json.loads(result.stdout)
            self.assertEqual(index["coverage"]["reports_found"], 0)
            self.assertEqual(
                index["coverage"]["missing_dates"],
                ["2026-07-01", "2026-07-02"],
            )

    def test_invalid_category_order_fails_without_silent_skip(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir)
            invalid = list(CATEGORIES["en"])
            invalid[0], invalid[1] = invalid[1], invalid[0]
            self.write_report(
                source_dir,
                "2026-07-01",
                "en",
                "United Kingdom",
                categories=invalid,
            )
            result = self.run_collector(source_dir)
            self.assertEqual(result.returncode, 2)
            self.assertIn("category order", result.stderr)

    def test_future_month_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = subprocess.run(
                [
                    sys.executable,
                    str(COLLECTOR),
                    "--country",
                    "United Kingdom",
                    "--month",
                    "2026-08",
                    "--source-dir",
                    temp_dir,
                    "--as-of",
                    "2026-07-20",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("begins after", result.stderr)


if __name__ == "__main__":
    unittest.main()
