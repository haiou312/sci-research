from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = (
    REPO_ROOT
    / "skills/crd-vi-transposition/scripts/validate-news-section.py"
)
SPEC = importlib.util.spec_from_file_location("crd_vi_news_validator", VALIDATOR_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load validator at {VALIDATOR_PATH}")
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


def report(row: str | None = None, news_count: int = 1) -> str:
    news_body = (
        "| Date | Country/Region | Development | Practical Impact | Sources |\n"
        "|---|---|---|---|---|\n"
        f"{row}\n"
        if row is not None
        else "No material CRD VI news identified for this reporting period.\n"
    )
    return (
        "---\n"
        "report_week: 2026-W31\n"
        "period_start: 2026-07-27\n"
        "period_end: 2026-08-02\n"
        f"news_count: {news_count}\n"
        "---\n\n"
        "## Weekly Changes\n\nNo material changes.\n\n"
        "## Regulatory News & Market Commentary\n\n"
        f"{news_body}\n"
        "| Country | Current Status | Summary |\n"
        "|---|---|---|\n"
        "| Austria | Ongoing | Example in 2026. Commission: Partial. "
        "[A](https://a.example) [B](https://b.example) |\n"
        "\n"
        "## Disclaimer\n\n"
        "This report was drafted and assembled with AI through a structured "
        "workflow using official sources for the reporting period and Member "
        "State checks. It reflects information checked as of 2026-08-03 and may "
        "contain omissions. It is not legal or professional advice and is not a "
        "substitute for qualified advice.\n"
    )


VALID_ROW = (
    "| 2026-07-30 | EU | EBA published a final third-country branch package. "
    "| Banks should update branch reporting and authorisation plans. "
    "| [EBA](https://eba.europa.eu/item) |"
)


def items() -> dict[str, object]:
    return {
        "schema_version": 1,
        "report_week": "2026-W31",
        "period_start": "2026-07-27",
        "period_end": "2026-08-02",
        "items": [
            {
                "date": "2026-07-30",
                "country_region": "EU",
                "development": "EBA published a final third-country branch package.",
                "practical_impact": "Banks should update branch reporting and authorisation plans.",
                "source_urls": ["https://eba.europa.eu/item"],
                "source_class": "official",
                "status_effect": "none",
            }
        ],
    }


def state(*urls: str) -> dict[str, object]:
    return {
        "countries": {
            "Austria": {
                "source_urls": list(urls),
            }
        }
    }


def audit() -> dict[str, object]:
    lanes = [
        "national_transposition",
        "third_country_branches",
        "supervisory_implementation",
        "market_response",
    ]
    return {
        "schema_version": 1,
        "report_week": "2026-W31",
        "period_start": "2026-07-27",
        "period_end": "2026-08-02",
        "lanes": [
            {"id": lane, "queries": [f"CRD VI {lane}"], "result_count": 1}
            for lane in lanes
        ],
        "candidates": [
            {
                "url": "https://eba.europa.eu/item",
                "published_date": "2026-07-30",
                "decision": "keep",
                "reason": "material CRD VI development",
            }
        ],
    }


class CrdViNewsValidatorTests(unittest.TestCase):
    def test_valid_news_report_and_items_pass(self) -> None:
        metadata, rows = VALIDATOR.validate_report(report(VALID_ROW))
        VALIDATOR.validate_items(metadata, rows, items())
        self.assertEqual(len(rows), 1)

    def test_zero_news_requires_exact_statement(self) -> None:
        metadata, rows = VALIDATOR.validate_report(report(None, news_count=0))
        self.assertEqual(metadata["news_count"], "0")
        self.assertEqual(rows, [])

    def test_news_date_outside_week_fails(self) -> None:
        text = report(VALID_ROW.replace("2026-07-30", "2026-07-20"))
        with self.assertRaisesRegex(ValueError, "outside"):
            VALIDATOR.validate_report(text)

    def test_google_news_redirect_fails(self) -> None:
        text = report(
            VALID_ROW.replace(
                "https://eba.europa.eu/item", "https://news.google.com/item"
            )
        )
        with self.assertRaisesRegex(ValueError, "Google News redirect"):
            VALIDATOR.validate_report(text)

    def test_count_mismatch_fails(self) -> None:
        with self.assertRaisesRegex(ValueError, "news_count"):
            VALIDATOR.validate_report(report(VALID_ROW, news_count=2))

    def test_missing_disclaimer_fails(self) -> None:
        text = report(VALID_ROW).split("\n## Disclaimer", 1)[0]
        with self.assertRaisesRegex(ValueError, "Disclaimer"):
            VALIDATOR.validate_report(text)

    def test_disclaimer_must_be_final_section(self) -> None:
        text = report(VALID_ROW) + "\n## Appendix\n\nExtra notes.\n"
        with self.assertRaisesRegex(ValueError, "final"):
            VALIDATOR.validate_report(text)

    def test_disclaimer_must_cover_ai_process_and_advice_boundary(self) -> None:
        text = report(VALID_ROW).replace("AI through a structured workflow", "research")
        with self.assertRaisesRegex(ValueError, "AI assistance"):
            VALIDATOR.validate_report(text)

    def test_items_must_match_rendered_report(self) -> None:
        metadata, rows = VALIDATOR.validate_report(report(VALID_ROW))
        selected = deepcopy(items())
        selected["items"][0]["country_region"] = "Germany"
        with self.assertRaisesRegex(ValueError, "country_region differs"):
            VALIDATOR.validate_items(metadata, rows, selected)

    def test_official_follow_up_requires_url(self) -> None:
        metadata, rows = VALIDATOR.validate_report(report(VALID_ROW))
        selected = deepcopy(items())
        selected["items"][0]["status_effect"] = "official_follow_up"
        with self.assertRaisesRegex(ValueError, "official URL"):
            VALIDATOR.validate_items(metadata, rows, selected)

    def test_official_follow_up_must_exist_in_current_state(self) -> None:
        metadata, rows = VALIDATOR.validate_report(report(VALID_ROW))
        selected = deepcopy(items())
        selected["items"][0]["status_effect"] = "official_follow_up"
        selected["items"][0]["official_follow_up_url"] = (
            "https://eba.europa.eu/item"
        )
        with self.assertRaisesRegex(ValueError, "absent from current-state"):
            VALIDATOR.validate_items(
                metadata,
                rows,
                selected,
                state("https://finance.ec.europa.eu/crd-vi"),
            )

        VALIDATOR.validate_items(
            metadata,
            rows,
            selected,
            state("https://eba.europa.eu/item"),
        )

    def test_complete_news_audit_passes(self) -> None:
        metadata, _ = VALIDATOR.validate_report(report(VALID_ROW))
        registry = {
            "search_lanes": [
                {"id": lane}
                for lane in (
                    "national_transposition",
                    "third_country_branches",
                    "supervisory_implementation",
                    "market_response",
                )
            ]
        }
        VALIDATOR.validate_audit(audit(), metadata, registry)

    def test_missing_news_lane_fails(self) -> None:
        metadata, _ = VALIDATOR.validate_report(report(VALID_ROW))
        registry = {
            "search_lanes": [
                {"id": lane}
                for lane in (
                    "national_transposition",
                    "third_country_branches",
                    "supervisory_implementation",
                    "market_response",
                )
            ]
        }
        selected = deepcopy(audit())
        selected["lanes"].pop()
        with self.assertRaisesRegex(ValueError, "every active search lane"):
            VALIDATOR.validate_audit(selected, metadata, registry)


if __name__ == "__main__":
    unittest.main()
