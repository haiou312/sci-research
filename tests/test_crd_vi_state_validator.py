from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "skills/crd-vi-transposition/scripts/validate-current-state.py"
SPEC = importlib.util.spec_from_file_location("crd_vi_state", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load validator at {SCRIPT}")
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


def membership() -> dict[str, object]:
    return {"count": 2, "countries": ["Austria", "Germany"]}


def record() -> dict[str, object]:
    return {
        "status": "Ongoing",
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


def state() -> dict[str, object]:
    return {
        "schema_version": 1,
        "report_week": "2026-W31",
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
        "countries": {"Austria": record(), "Germany": record()},
    }


class CrdViStateValidatorTests(unittest.TestCase):
    def test_full_state_passes(self) -> None:
        self.assertEqual(
            VALIDATOR.validate_state(state(), membership()),
            ["Austria", "Germany"],
        )

    def test_filtered_state_fails(self) -> None:
        data = deepcopy(state())
        data["countries"].pop("Austria")
        with self.assertRaisesRegex(ValueError, "missing: Austria"):
            VALIDATOR.validate_state(data, membership())

    def test_missing_article_21c_field_fails(self) -> None:
        data = deepcopy(state())
        data["countries"]["Germany"].pop("article_21c_5_existing_contracts_from")
        with self.assertRaisesRegex(ValueError, "missing fields"):
            VALIDATOR.validate_state(data, membership())

    def test_non_https_source_fails(self) -> None:
        data = deepcopy(state())
        data["countries"]["Germany"]["source_urls"][0] = "http://example.gov/law"
        with self.assertRaisesRegex(ValueError, "HTTPS"):
            VALIDATOR.validate_state(data, membership())


if __name__ == "__main__":
    unittest.main()
