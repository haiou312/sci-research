from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "skills/crd-vi-transposition/scripts/validate-member-states.py"
SPEC = importlib.util.spec_from_file_location("crd_vi_membership", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load validator at {SCRIPT}")
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


def snapshot() -> dict[str, object]:
    countries = ["Austria", "Czechia", "Germany"]
    return {
        "schema_version": 1,
        "checked_at": "2026-08-03T07:00:00+01:00",
        "count": 3,
        "countries": countries,
        "sources": [
            {
                "source_id": "eu_country_profiles",
                "url": VALIDATOR.AUTHORITIES["eu_country_profiles"],
                "available": True,
                "pagination_complete": True,
                "retrieved_at": "2026-08-03T07:00:00+01:00",
                "displayed_count": 3,
                "countries": countries,
            },
            {
                "source_id": "eur_lex_member_states",
                "url": VALIDATOR.AUTHORITIES["eur_lex_member_states"],
                "available": True,
                "pagination_complete": True,
                "retrieved_at": "2026-08-03T07:01:00+01:00",
                "displayed_count": 3,
                "countries": ["Germany", "Czech Republic", "Austria"],
            },
        ],
    }


class CrdViMembershipTests(unittest.TestCase):
    def test_two_official_lists_and_alias_pass(self) -> None:
        self.assertEqual(
            VALIDATOR.validate_snapshot(snapshot()),
            ["Austria", "Czechia", "Germany"],
        )

    def test_missing_country_fails(self) -> None:
        data = deepcopy(snapshot())
        data["sources"][1]["countries"].remove("Austria")
        data["sources"][1]["displayed_count"] = 2
        with self.assertRaisesRegex(ValueError, "missing: Austria"):
            VALIDATOR.validate_snapshot(data)

    def test_extra_country_fails(self) -> None:
        data = deepcopy(snapshot())
        data["sources"][1]["countries"].append("Norway")
        data["sources"][1]["displayed_count"] = 4
        with self.assertRaisesRegex(ValueError, "extra: Norway"):
            VALIDATOR.validate_snapshot(data)

    def test_duplicate_country_fails(self) -> None:
        data = deepcopy(snapshot())
        data["sources"][0]["countries"].append("Austria")
        data["sources"][0]["displayed_count"] = 4
        with self.assertRaisesRegex(ValueError, "duplicate country"):
            VALIDATOR.validate_snapshot(data)

    def test_wrong_top_level_count_fails(self) -> None:
        data = deepcopy(snapshot())
        data["count"] = 27
        with self.assertRaisesRegex(ValueError, "count differs"):
            VALIDATOR.validate_snapshot(data)

    def test_missing_authority_fails(self) -> None:
        data = deepcopy(snapshot())
        data["sources"].pop()
        with self.assertRaisesRegex(ValueError, "both official authorities"):
            VALIDATOR.validate_snapshot(data)

    def test_unavailable_authority_fails(self) -> None:
        data = deepcopy(snapshot())
        data["sources"][0]["available"] = False
        with self.assertRaisesRegex(ValueError, "must be available"):
            VALIDATOR.validate_snapshot(data)

    def test_incomplete_pagination_fails(self) -> None:
        data = deepcopy(snapshot())
        data["sources"][1]["pagination_complete"] = False
        with self.assertRaisesRegex(ValueError, "pagination must be complete"):
            VALIDATOR.validate_snapshot(data)


if __name__ == "__main__":
    unittest.main()
