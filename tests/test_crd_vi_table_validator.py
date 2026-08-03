from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = (
    REPO_ROOT
    / "skills/crd-vi-transposition/scripts/validate-country-table.py"
)
SPEC = importlib.util.spec_from_file_location("crd_vi_table_validator", VALIDATOR_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load validator at {VALIDATOR_PATH}")
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


def summary(marker: str = "Commission: Full") -> str:
    return (
        f"Final national measure confirmed in 2026. {marker}. "
        "[National source](https://example.com/national) "
        "[European Commission](https://example.com/commission)"
    )


def render(rows: list[tuple[str, str, str]]) -> str:
    body = "\n".join(
        f"| {country} | {status} | {text} |"
        for country, status, text in rows
    )
    return f"| Country | Current Status | Summary |\n|---|---|---|\n{body}\n"


class CrdViTableValidatorTests(unittest.TestCase):
    def test_all_27_member_states_pass(self) -> None:
        text = render(
            [
                (country, "Completed", summary())
                for country in VALIDATOR.EU_COUNTRIES
            ]
        )
        count, counts = VALIDATOR.validate(text)
        self.assertEqual(count, 27)
        self.assertEqual(counts["Completed"], 27)

    def test_filtered_table_requires_allow_subset(self) -> None:
        text = render([("Germany", "Completed", summary())])
        with self.assertRaisesRegex(ValueError, "exactly 27"):
            VALIDATOR.validate(text)
        count, _ = VALIDATOR.validate(text, allow_subset=True)
        self.assertEqual(count, 1)

    def test_invalid_status_fails(self) -> None:
        text = render([("Germany", "Finished", summary())])
        with self.assertRaisesRegex(ValueError, "invalid Current Status"):
            VALIDATOR.validate(text, allow_subset=True)

    def test_non_eu_country_fails(self) -> None:
        text = render([("Norway", "Ongoing", summary("Commission: Partial"))])
        with self.assertRaisesRegex(ValueError, "non-EU or unknown"):
            VALIDATOR.validate(text, allow_subset=True)

    def test_missing_commission_marker_fails(self) -> None:
        text = render(
            [
                (
                    "Germany",
                    "Completed",
                    summary().replace("Commission: Full", "Commission checked"),
                )
            ]
        )
        with self.assertRaisesRegex(ValueError, "Commission marker"):
            VALIDATOR.validate(text, allow_subset=True)

    def test_missing_second_link_fails(self) -> None:
        text = render(
            [
                (
                    "Germany",
                    "Completed",
                    "Measure adopted in 2026. Commission: Full. "
                    "[National source](https://example.com/national)",
                )
            ]
        )
        with self.assertRaisesRegex(ValueError, "at least two"):
            VALIDATOR.validate(text, allow_subset=True)


if __name__ == "__main__":
    unittest.main()
