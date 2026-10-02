from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
EMAIL_GUARD = REPO_ROOT / "scripts/hooks/email-send-guard.js"
FORMAT_CHECK = REPO_ROOT / "scripts/hooks/daily-news-format-check.js"
MONTHLY_FORMAT_CHECK = REPO_ROOT / "scripts/hooks/monthly-news-format-check.js"
OPPORTUNITY_FORMAT_CHECK = (
    REPO_ROOT / "scripts/hooks/opportunity-briefing-format-check.js"
)
OPPORTUNITY_FIXTURE = (
    REPO_ROOT / "tests/fixtures/opportunity-briefing-sample.md"
)


class HookTests(unittest.TestCase):
    def run_hook(
        self, script: Path, payload: dict[str, object]
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["node", str(script)],
            input=json.dumps(payload),
            check=False,
            capture_output=True,
            text=True,
        )

    def test_email_guard_denies_inline_smtp(self) -> None:
        result = self.run_hook(
            EMAIL_GUARD,
            {"hook_event_name": "PreToolUse", "tool_input": {"cmd": "python3 -c 'import smtplib'"}},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(result.stdout)
        decision = output["hookSpecificOutput"]
        self.assertEqual(decision["hookEventName"], "PreToolUse")
        self.assertEqual(decision["permissionDecision"], "deny")

    def test_email_guard_allows_sanctioned_script(self) -> None:
        result = self.run_hook(
            EMAIL_GUARD,
            {
                "hook_event_name": "PreToolUse",
                "tool_input": {
                    "cmd": 'python3 "$PLUGIN_ROOT/scripts/send-report-email.py" --help'
                },
            },
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")

    def test_format_hook_finds_apply_patch_freeform_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            report = project_root / "daily-news/report.md"
            report.parent.mkdir(parents=True)
            report.write_text("# Japan Daily News Intelligence\n", encoding="utf-8")
            patch = f"*** Begin Patch\n*** Update File: {report}\n*** End Patch"
            result = self.run_hook(
                FORMAT_CHECK,
                {
                    "hook_event_name": "PostToolUse",
                    "cwd": str(project_root),
                    "tool_input": patch,
                },
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            output = json.loads(result.stdout)
            self.assertIn("daily-news format check FAILED", output["systemMessage"])
            self.assertEqual(
                output["hookSpecificOutput"]["hookEventName"], "PostToolUse"
            )

    def test_direct_format_check_fails_invalid_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report = Path(temp_dir) / "daily-news/report.md"
            report.parent.mkdir(parents=True)
            report.write_text("# Japan Daily News Intelligence\n", encoding="utf-8")
            result = subprocess.run(
                ["node", str(FORMAT_CHECK), "--file", str(report)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("daily-news format check FAILED", result.stderr)

    def test_direct_format_check_rejects_english_below_minimum(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report = Path(temp_dir) / "daily-news/report.md"
            report.parent.mkdir(parents=True)
            body = " ".join(["fact"] * 249)
            report.write_text(
                f"""# Japan Daily News Intelligence — July 16, 2026

## 1. Economy & Markets

### Bank of Japan keeps policy unchanged

{body}

**References**

[1] Reuters. (2026, July 16). Bank of Japan keeps policy unchanged. Reuters. https://example.com/story
""",
                encoding="utf-8",
            )
            result = subprocess.run(
                ["node", str(FORMAT_CHECK), "--file", str(report)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("minimum 250", result.stderr)

    def test_direct_format_check_accepts_english_at_minimum(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report = Path(temp_dir) / "daily-news/report.md"
            report.parent.mkdir(parents=True)
            body = " ".join(["fact"] * 250)
            report.write_text(
                f"""# Japan Daily News Intelligence — July 16, 2026

## 1. Economy & Markets

### Bank of Japan keeps policy unchanged

{body}

**References**

[1] Reuters. (2026, July 16). Bank of Japan keeps policy unchanged. Reuters. https://example.com/story
""",
                encoding="utf-8",
            )
            result = subprocess.run(
                ["node", str(FORMAT_CHECK), "--file", str(report)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("FORMAT_OK", result.stdout)
            self.assertIn("LENGTH_INFO: lang=en", result.stdout)
            self.assertIn("required>=250", result.stdout)

    def test_direct_format_check_rejects_more_than_six_stories_in_category(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report = Path(temp_dir) / "daily-news/report.md"
            report.parent.mkdir(parents=True)
            body = " ".join(["fact"] * 250)
            stories = []
            for number in range(1, 8):
                stories.append(
                    f"""### Economy story {number}

{body}

**References**

[{number}] Reuters. (2026, July 16). Economy story {number}. Reuters. https://example.com/story/{number}

---"""
                )
            report.write_text(
                "\n\n".join(
                    [
                        "# Japan Daily News Intelligence — July 16, 2026",
                        "## 1. Economy & Markets",
                        *stories,
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                ["node", str(FORMAT_CHECK), "--file", str(report)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("has 7 stories; maximum 6", result.stderr)

    def test_direct_format_check_rejects_chinese_below_minimum(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report = Path(temp_dir) / "daily-news/report.md"
            report.parent.mkdir(parents=True)
            body = "中" * 299
            report.write_text(
                f"""# 日本每日热点新闻 — 2026年7月16日

## 一、经济与市场

### 日本央行维持政策不变

{body}

**References**

[1] Reuters. (2026, July 16). Bank of Japan keeps policy unchanged. Reuters. https://example.com/story
""",
                encoding="utf-8",
            )
            result = subprocess.run(
                ["node", str(FORMAT_CHECK), "--file", str(report)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("minimum 300", result.stderr)

    def test_direct_format_check_accepts_chinese_at_minimum(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report = Path(temp_dir) / "daily-news/report.md"
            report.parent.mkdir(parents=True)
            body = "中" * 300
            report.write_text(
                f"""# 日本每日热点新闻 — 2026年7月16日

## 一、经济与市场

### 日本央行维持政策不变

{body}

**References**

[1] Reuters. (2026, July 16). Bank of Japan keeps policy unchanged. Reuters. https://example.com/story
""",
                encoding="utf-8",
            )
            result = subprocess.run(
                ["node", str(FORMAT_CHECK), "--file", str(report)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("FORMAT_OK", result.stdout)
            self.assertIn("LENGTH_INFO: lang=zh", result.stdout)
            self.assertIn("required=300..450", result.stdout)

    def write_length_report(
        self, root: Path, bodies: list[str], lang: str = "zh", monthly: bool = False
    ) -> Path:
        headings = {
            "zh": ("日本每日热点新闻 — 2026年7月16日", "一、经济与市场"),
            "en": ("Japan Daily News Intelligence — July 16, 2026", "1. Economy & Markets"),
            "ja": ("日本デイリーニュース — 2026年7月16日", "1. 経済と市場"),
        }
        h1, h2 = headings[lang]
        prefix = [f"# {h1}", f"## {h2}"]
        if monthly:
            self.assertEqual(lang, "zh")
            prefix = [
                "# 日本月度热点新闻 — 2026年7月",
                "*资料范围：本报告基于2026年7月现有31份日本每日热点新闻，覆盖全部日期。*",
            ]
            categories = [
                "一、经济与市场", "二、政治与外交", "三、科技与产业",
                "四、社会与民生", "五、企业IPO与并购", "六、其他重要事件",
            ]
            self.assertEqual(len(bodies), len(categories))
        sections = []
        for number, body in enumerate(bodies, start=1):
            if monthly:
                sections.append(f"## {categories[number - 1]}")
            sections.append(
                f"### 新闻标题{number}\n\n{body}\n\n**References**\n\n"
                f"[{number}] Reuters. (2026, July 16). {'参考资料' * 150}. "
                f"Reuters. https://example.com/story/{number}\n\n---"
            )
        report = root / ("monthly-news" if monthly else "daily-news") / "report.md"
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text("\n\n".join([*prefix, *sections]) + "\n", encoding="utf-8")
        return report

    def check_report(self, report: Path, script: Path = FORMAT_CHECK) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["node", str(script), "--file", str(report)],
            check=False, capture_output=True, text=True,
        )

    def test_chinese_maximum_is_inclusive_and_counts_only_han_body(self) -> None:
        for han_count, expected_code in [(300, 0), (450, 0), (451, 2)]:
            with self.subTest(han_count=han_count), tempfile.TemporaryDirectory() as temp_dir:
                # Supplementary-plane Han counts as one; punctuation, Latin text,
                # digits, headings, and the long reference must not inflate it.
                body = "中" * (han_count - 1) + "𠀀" + "，。ABC 123 " * 30
                report = self.write_length_report(Path(temp_dir), [body])
                result = self.check_report(report)
                self.assertEqual(result.returncode, expected_code, result.stderr)
                if expected_code:
                    self.assertIn("451 Han characters; maximum 450", result.stderr)
                    self.assertIn("新闻标题1", result.stderr)
                else:
                    self.assertIn(f"min={han_count}, max={han_count}", result.stdout)
                    self.assertIn("required=300..450", result.stdout)

    def test_chinese_length_range_applies_per_story_not_average(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report = self.write_length_report(Path(temp_dir), ["中" * 299, "中" * 451])
            result = self.check_report(report)
            self.assertEqual(result.returncode, 2)
            self.assertIn('Story "新闻标题1" body length is 299', result.stderr)
            self.assertIn('Story "新闻标题2" body length is 451', result.stderr)

    def test_format_hook_warns_after_patch_for_chinese_above_maximum(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report = self.write_length_report(Path(temp_dir), ["中" * 451])
            result = self.run_hook(FORMAT_CHECK, {
                "hook_event_name": "PostToolUse",
                "tool_input": f"*** Begin Patch\n*** Update File: {report}\n*** End Patch",
            })
            self.assertEqual(result.returncode, 0, result.stderr)
            output = json.loads(result.stdout)
            self.assertIn("maximum 450", output["hookSpecificOutput"]["additionalContext"])
            self.assertIn("do not truncate mechanically", output["systemMessage"])

    def test_english_keeps_no_maximum_and_japanese_has_no_length_bounds(self) -> None:
        for lang, body in [("en", "fact " * 600), ("ja", "中"), ("ja", "中" * 600)]:
            with self.subTest(lang=lang, size=len(body)), tempfile.TemporaryDirectory() as temp_dir:
                report = self.write_length_report(Path(temp_dir), [body], lang=lang)
                result = self.check_report(report)
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_monthly_chinese_retains_400_minimum_and_no_maximum(self) -> None:
        for han_count, expected_code in [(399, 2), (400, 0), (600, 0)]:
            with self.subTest(han_count=han_count), tempfile.TemporaryDirectory() as temp_dir:
                report = self.write_length_report(
                    Path(temp_dir), ["中" * han_count] * 6, monthly=True,
                )
                result = self.check_report(report, MONTHLY_FORMAT_CHECK)
                self.assertEqual(result.returncode, expected_code, result.stderr)
                if expected_code:
                    self.assertIn("minimum 400", result.stderr)
                else:
                    self.assertIn("required>=400", result.stdout)
                    self.assertIn(f"min={han_count}, max={han_count}", result.stdout)

    def test_direct_format_check_rejects_chinese_headline_whitespace_separator(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report = Path(temp_dir) / "daily-news/report.md"
            report.parent.mkdir(parents=True)
            report.write_text(
                f"""# 韩国每日热点新闻 — 2026年7月16日

## 一、经济与市场

### 芯片出口激增 韩国前二十天出口额创新高

{"中" * 400}

**References**

[1] Reuters. (2026, July 16). South Korean exports rise. Reuters. https://example.com/story
""",
                encoding="utf-8",
            )
            result = subprocess.run(
                ["node", str(FORMAT_CHECK), "--file", str(report)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("contains whitespace between Chinese text fragments", result.stderr)
            self.assertIn("do not mechanically replace", result.stderr)

    def test_direct_format_check_accepts_chinese_comma_and_foreign_name_spaces(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report = Path(temp_dir) / "daily-news/report.md"
            report.parent.mkdir(parents=True)
            report.write_text(
                f"""# 日本每日热点新闻 — 2026年7月16日

## 一、经济与市场

### Seven & i接受收购提议，交易仍待监管审查

{"中" * 400}

**References**

[1] Reuters. (2026, July 16). Seven & i reviews bid. Reuters. https://example.com/story
""",
                encoding="utf-8",
            )
            result = subprocess.run(
                ["node", str(FORMAT_CHECK), "--file", str(report)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("FORMAT_OK", result.stdout)

    def test_direct_monthly_format_check_accepts_matching_structure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report = Path(temp_dir) / "monthly-news/report.md"
            report.parent.mkdir(parents=True)
            body = " ".join(["fact"] * 250)
            headings = [
                "1. Economy & Markets",
                "2. Politics & Diplomacy",
                "3. Technology & Industry",
                "4. Society & Livelihood",
                "5. Corporate IPO & M&A",
                "6. Other Notable Events",
            ]
            sections = []
            for number, heading in enumerate(headings, start=1):
                sections.append(
                    f"""## {heading}

### Monthly story {number}

{body}

**References**

[{number}] Reuters. (2026, July 16). Monthly story {number}. Reuters. https://example.com/monthly/{number}

---"""
                )
            report.write_text(
                "\n\n".join(
                    [
                        "# Japan Monthly News Intelligence — July 2026",
                        "*Source coverage: this report uses 31 available Japan daily reports for July 2026; all expected dates were covered.*",
                        *sections,
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                ["node", str(MONTHLY_FORMAT_CHECK), "--file", str(report)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("FORMAT_OK", result.stdout)
            self.assertIn("LENGTH_INFO: lang=en", result.stdout)

    def test_direct_monthly_format_check_requires_coverage_note(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report = Path(temp_dir) / "monthly-news/report.md"
            report.parent.mkdir(parents=True)
            report.write_text(
                "# Japan Monthly News Intelligence — July 2026\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                ["node", str(MONTHLY_FORMAT_CHECK), "--file", str(report)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("source-coverage note", result.stderr)

    def test_direct_monthly_format_check_accepts_china_chinese_categories(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report = Path(temp_dir) / "monthly-news/report.md"
            report.parent.mkdir(parents=True)
            headings = [
                "一、经济与市场",
                "二、政治与外交",
                "三、科技与产业",
                "四、社会与民生",
                "五、海外涉华财经",
                "六、企业IPO与并购",
                "七、其他重要事件",
            ]
            sections = []
            for number, heading in enumerate(headings, start=1):
                sections.append(
                    f"""## {heading}

### 中国月度新闻{number}

{"中" * 400}

**References**

[{number}] Reuters. (2026, July 16). China monthly story {number}. Reuters. https://example.com/china-monthly/{number}

---"""
                )
            report.write_text(
                "\n\n".join(
                    [
                        "# 中国月度热点新闻 — 2026年7月",
                        "*资料范围：本报告基于2026年7月现有31份中国每日热点新闻，覆盖该月全部31个日期。*",
                        *sections,
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                ["node", str(MONTHLY_FORMAT_CHECK), "--file", str(report)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("FORMAT_OK", result.stdout)
            self.assertIn("stories=7", result.stdout)

    def test_direct_opportunity_format_check_accepts_fixture(self) -> None:
        result = subprocess.run(
            [
                "node",
                str(OPPORTUNITY_FORMAT_CHECK),
                "--file",
                str(OPPORTUNITY_FIXTURE),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("FORMAT_OK", result.stdout)

    def test_opportunity_format_hook_reports_missing_story_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            report = project_root / "china-opportunity-briefings/report.md"
            report.parent.mkdir(parents=True)
            report.write_text(
                "# 中资企业商机拓展简报\n",
                encoding="utf-8",
            )
            patch = f"*** Begin Patch\n*** Update File: {report}\n*** End Patch"
            result = self.run_hook(
                OPPORTUNITY_FORMAT_CHECK,
                {
                    "hook_event_name": "PostToolUse",
                    "cwd": str(project_root),
                    "tool_input": patch,
                },
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            output = json.loads(result.stdout)
            self.assertIn(
                "opportunity briefing format check FAILED",
                output["systemMessage"],
            )
            self.assertEqual(
                output["hookSpecificOutput"]["hookEventName"],
                "PostToolUse",
            )


if __name__ == "__main__":
    unittest.main()
