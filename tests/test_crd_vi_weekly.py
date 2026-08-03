from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime
import importlib.util
import json
from pathlib import Path
import unittest
from zoneinfo import ZoneInfo


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / "skills/crd-vi-transposition"
MEMBERS = ["Austria", "Czechia", "France", "Germany", "Spain"]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PERIOD = load_module("crd_vi_weekly_period", SKILL_ROOT / "scripts/weekly-period.py")
PLAN = load_module(
    "crd_vi_weekly_search_plan",
    SKILL_ROOT / "scripts/build-weekly-search-plan.py",
)
DIFF = load_module("crd_vi_weekly_diff", SKILL_ROOT / "scripts/diff-weekly-state.py")
VALIDATOR = load_module(
    "crd_vi_weekly_validator", SKILL_ROOT / "scripts/validate-country-table.py"
)


def membership(members: list[str] | None = None) -> dict[str, object]:
    countries = list(members or MEMBERS)
    return {
        "schema_version": 1,
        "checked_at": "2026-08-03T07:00:00+01:00",
        "count": len(countries),
        "countries": countries,
        "sources": [
            {"url": "https://european-union.europa.eu/eu-countries_en"},
            {"url": "https://eur-lex.europa.eu/member_states"},
        ],
    }


def country_record(status: str = "Ongoing") -> dict[str, object]:
    return {
        "status": status,
        "commission_marker": "Commission: Partial",
        "national_measure": "Bill 1/2026",
        "measure_adopted": None,
        "measure_published": None,
        "milestone_date": "2026-07-31",
        "measure_effective": None,
        "article_21c_general_applies": "2027-01-11",
        "article_21c_5_existing_contracts_from": "2026-07-11",
        "source_health": "verified",
        "last_verified": "2026-08-03",
        "source_urls": [
            "https://example.gov/law",
            "https://finance.ec.europa.eu/crd-vi",
        ],
    }


def state(
    report_week: str = "2026-W31", members: list[str] | None = None
) -> dict[str, object]:
    countries = members or MEMBERS
    return {
        "schema_version": 1,
        "report_week": report_week,
        "period_start": "2026-07-27",
        "period_end": "2026-08-02",
        "status_cutoff": "2026-08-02",
        "checked_at": "2026-08-03T07:00:00+01:00",
        "sources": {
            "commission": {
                "last_updated": "2026-07-31",
                "content_hash": "sha256:commission",
                "available": True,
            },
            "ey": {
                "last_updated": "2026-07-30",
                "content_hash": "sha256:ey",
                "available": True,
            },
        },
        "countries": {country: country_record() for country in countries},
    }


def weekly_report(change_count: int = 0) -> str:
    rows = "\n".join(
        f"| {country} | Ongoing | Bill progressed in 2026. Commission: Partial. "
        "[National](https://example.gov/law) "
        "[Commission](https://finance.ec.europa.eu/crd-vi) |"
        for country in MEMBERS
    )
    return (
        "---\n"
        "report_week: 2026-W31\n"
        "period_start: 2026-07-27\n"
        "period_end: 2026-08-02\n"
        "timezone: Europe/London\n"
        "status_cutoff: 2026-08-02\n"
        "checked_at: 2026-08-03T07:00:00+01:00\n"
        "previous_successful_week: 2026-W30\n"
        "country_filter: all\n"
        f"change_count: {change_count}\n"
        "news_count: 0\n"
        "---\n\n"
        "## Weekly Changes\n\nNo material changes.\n\n"
        "## Regulatory News & Market Commentary\n\n"
        "No material CRD VI news identified for this reporting period.\n\n"
        "| Country | Current Status | Summary |\n"
        "|---|---|---|\n"
        f"{rows}\n"
    )


class WeeklyPeriodTests(unittest.TestCase):
    def test_monday_run_reports_previous_completed_week(self) -> None:
        timezone = ZoneInfo("Europe/London")
        run_at = datetime.fromisoformat("2026-08-03T07:00:00+01:00")
        result = PERIOD.build_period(run_at, timezone)
        self.assertEqual(result["report_week"], "2026-W31")
        self.assertEqual(result["period_start"], "2026-07-27")
        self.assertEqual(result["period_end"], "2026-08-02")
        self.assertEqual(result["discovery_start"], "2026-07-25")

    def test_sunday_run_does_not_report_incomplete_sunday(self) -> None:
        timezone = ZoneInfo("Europe/London")
        run_at = datetime.fromisoformat("2026-08-02T12:00:00+01:00")
        result = PERIOD.build_period(run_at, timezone)
        self.assertEqual(result["period_end"], "2026-07-26")

    def test_explicit_week_ending_must_be_sunday(self) -> None:
        timezone = ZoneInfo("Europe/London")
        run_at = datetime.fromisoformat("2026-08-03T07:00:00+01:00")
        with self.assertRaisesRegex(ValueError, "Sunday"):
            PERIOD.build_period(run_at, timezone, date(2026, 8, 3))


class WeeklyDiffTests(unittest.TestCase):
    def test_baseline_uses_dynamic_member_count(self) -> None:
        result = DIFF.compare(state(), membership())
        self.assertTrue(result["baseline"])
        self.assertEqual(result["change_count"], 0)
        self.assertEqual(result["baseline_country_count"], len(MEMBERS))

    def test_status_transition_is_material(self) -> None:
        previous = state("2026-W30")
        current = deepcopy(state())
        current["countries"]["Austria"]["status"] = "Completed"
        result = DIFF.compare(current, membership(), previous)
        self.assertEqual(result["change_count"], 1)
        self.assertEqual(
            result["status_transitions"],
            [{"country": "Austria", "before": "Ongoing", "after": "Completed"}],
        )

    def test_membership_addition_is_material(self) -> None:
        previous_members = [country for country in MEMBERS if country != "France"]
        result = DIFF.compare(
            state(), membership(), state("2026-W30", previous_members)
        )
        self.assertEqual(result["membership_changes"]["added"], ["France"])
        self.assertEqual(result["change_count"], 1)

    def test_country_alias_does_not_create_membership_change(self) -> None:
        previous = state("2026-W30")
        previous["countries"]["Czech Republic"] = previous["countries"].pop("Czechia")
        result = DIFF.compare(state(), membership(), previous)
        self.assertEqual(result["membership_changes"], {"added": [], "removed": []})

    def test_source_outage_cannot_change_status(self) -> None:
        previous = state("2026-W30")
        current = deepcopy(state())
        current["countries"]["Austria"]["status"] = "Completed"
        current["countries"]["Austria"]["source_health"] = "unavailable"
        with self.assertRaisesRegex(ValueError, "source failure"):
            DIFF.compare(current, membership(), previous)

    def test_regression_requires_reason(self) -> None:
        previous = state("2026-W30")
        previous["countries"]["Austria"]["status"] = "Completed"
        with self.assertRaisesRegex(ValueError, "regression_reason"):
            DIFF.compare(state(), membership(), previous)

    def test_source_health_only_change_is_not_material(self) -> None:
        previous = state("2026-W30")
        current = deepcopy(state())
        current["countries"]["Austria"]["source_health"] = "conflict"
        result = DIFF.compare(current, membership(), previous)
        self.assertEqual(result["change_count"], 0)
        self.assertIn("Austria", result["changed_countries"])


class WeeklySearchPlanTests(unittest.TestCase):
    def test_baseline_deep_checks_dynamic_membership(self) -> None:
        result = PLAN.build_plan(membership(), date(2026, 8, 2))
        self.assertEqual(result["deep_check_count"], len(MEMBERS))
        self.assertEqual(result["light_check_count"], 0)

    def test_weekly_plan_upgrades_only_triggered_countries(self) -> None:
        previous = state("2026-W30")
        for record in previous["countries"].values():
            record["status"] = "Completed"
            record["last_verified"] = "2026-07-31"
        previous["countries"]["Austria"]["status"] = "Ongoing"
        previous["countries"]["France"]["last_verified"] = "2026-06-01"
        previous["countries"]["Spain"]["source_health"] = "conflict"
        result = PLAN.build_plan(
            membership(), date(2026, 8, 2), previous, {"Germany"}
        )
        deep_names = {item["country"] for item in result["deep_checks"]}
        self.assertEqual(deep_names, {"Austria", "France", "Germany", "Spain"})
        self.assertEqual(result["light_check_count"], 1)

    def test_new_member_without_history_is_deep_checked(self) -> None:
        current_members = MEMBERS + ["Portugal"]
        result = PLAN.build_plan(
            membership(current_members), date(2026, 8, 2), state("2026-W30")
        )
        portugal = next(item for item in result["deep_checks"] if item["country"] == "Portugal")
        self.assertIn("new_member_state", portugal["reasons"])
        self.assertIn("no_historical_official_sources", portugal["reasons"])

    def test_full_refresh_deep_checks_dynamic_membership(self) -> None:
        previous = state("2026-W30")
        for record in previous["countries"].values():
            record["status"] = "Completed"
        result = PLAN.build_plan(
            membership(), date(2026, 8, 2), previous, full_refresh=True
        )
        self.assertEqual(result["deep_check_count"], len(MEMBERS))


class WeeklyContractTests(unittest.TestCase):
    def test_fixed_country_source_registry_is_absent(self) -> None:
        self.assertFalse(
            (SKILL_ROOT / "references/country-sources.json").exists()
        )

    def test_news_registry_has_four_lanes_and_source_classes(self) -> None:
        registry = json.loads(
            (SKILL_ROOT / "references/news-sources.json").read_text(encoding="utf-8")
        )
        self.assertEqual(len(registry["search_lanes"]), 4)
        self.assertEqual(
            {group["class"] for group in registry["source_groups"]},
            {"official", "news_media", "industry", "professional_analysis"},
        )

    def test_weekly_metadata_state_and_membership_alignment_pass(self) -> None:
        text = weekly_report()
        rows = VALIDATOR.extract_rows(text)
        metadata = VALIDATOR.validate_weekly(text)
        VALIDATOR.validate(text, MEMBERS)
        VALIDATOR.validate_state_alignment(rows, metadata, state())
        VALIDATOR.validate_diff_alignment(
            metadata,
            {
                "schema_version": 1,
                "report_week": "2026-W31",
                "previous_week": "2026-W30",
                "baseline": False,
                "change_count": 0,
            },
        )

    def test_invalid_period_fails(self) -> None:
        text = weekly_report().replace("period_start: 2026-07-27", "period_start: 2026-07-28")
        with self.assertRaisesRegex(ValueError, "Monday through Sunday"):
            VALIDATOR.validate_weekly(text)

    def test_report_and_state_status_mismatch_fails(self) -> None:
        text = weekly_report()
        current = state()
        current["countries"]["Austria"]["status"] = "Completed"
        with self.assertRaisesRegex(ValueError, "status differs"):
            VALIDATOR.validate_state_alignment(
                VALIDATOR.extract_rows(text), VALIDATOR.validate_weekly(text), current
            )

    def test_filtered_report_can_use_full_current_state(self) -> None:
        text = weekly_report().replace(
            "country_filter: all",
            "country_filter: Germany",
        )
        lines = text.splitlines()
        table_start = lines.index("| Country | Current Status | Summary |")
        filtered = [line for line in lines[table_start:] if "| Germany |" in line]
        filtered_text = "\n".join(
            lines[:table_start]
            + [
                "| Country | Current Status | Summary |",
                "|---|---|---|",
            ]
            + filtered
            + [""]
        )
        rows = VALIDATOR.extract_rows(filtered_text)
        metadata = VALIDATOR.validate_weekly(filtered_text)
        VALIDATOR.validate(filtered_text, MEMBERS, allow_subset=True)
        VALIDATOR.validate_state_alignment(rows, metadata, state())


if __name__ == "__main__":
    unittest.main()
