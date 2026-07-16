from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_SCRIPTS = (
    REPO_ROOT / "skills/china-outbound-opportunity-briefing/scripts"
)
COLLECTOR = SKILL_SCRIPTS / "collect-companies-house.py"
DIFF = SKILL_SCRIPTS / "diff-company-snapshots.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class OpportunityScriptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.collector = load_module("companies_house_collector", COLLECTOR)

    def test_collector_requires_api_key(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            env = os.environ.copy()
            env.pop("COMPANIES_HOUSE_API_KEY", None)
            result = subprocess.run(
                [
                    sys.executable,
                    str(COLLECTOR),
                    "--start-date",
                    "2026-07-06",
                    "--end-date",
                    "2026-07-12",
                    "--output",
                    str(Path(temp_dir) / "snapshot.json"),
                ],
                env=env,
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertEqual(result.returncode, 3)
        self.assertIn("missing Companies House API key", result.stderr)

    def test_personal_fields_are_not_retained(self) -> None:
        raw_officers = {
            "items": [
                {
                    "name": "Example Director",
                    "officer_role": "director",
                    "appointed_on": "2026-07-09",
                    "date_of_birth": {"month": 1, "year": 1980},
                    "address": {"address_line_1": "Private residence"},
                }
            ]
        }
        raw_psc = {
            "items": [
                {
                    "name": "Example Controller",
                    "kind": "individual-person-with-significant-control",
                    "notified_on": "2026-07-10",
                    "date_of_birth": {"month": 2, "year": 1975},
                    "address": {"address_line_1": "Private residence"},
                }
            ]
        }
        officers = self.collector.clean_officers(raw_officers)
        pscs = self.collector.clean_psc(raw_psc)
        self.assertNotIn("date_of_birth", officers[0])
        self.assertNotIn("address", officers[0])
        self.assertNotIn("date_of_birth", pscs[0])
        self.assertNotIn("address", pscs[0])

    def test_diff_detects_material_changes(self) -> None:
        fingerprint = "scope-123"
        previous = {
            "fetched_at": "2026-07-05T12:00:00+00:00",
            "date_range": {"start": "2026-06-29", "end": "2026-07-05"},
            "collection_scope": {"watchlist_fingerprint": fingerprint},
            "companies": [
                {
                    "company_number": "01234567",
                    "profile": {
                        "company_name": "Example China UK Limited",
                        "company_status": "active",
                    },
                    "officers": [],
                    "persons_with_significant_control": [],
                    "filing_history": [],
                    "charges": [],
                }
            ],
        }
        current = {
            "fetched_at": "2026-07-12T12:00:00+00:00",
            "date_range": {"start": "2026-07-06", "end": "2026-07-12"},
            "collection_scope": {"watchlist_fingerprint": fingerprint},
            "companies": [
                {
                    "company_number": "01234567",
                    "profile": {
                        "company_name": "Example China UK Limited",
                        "company_status": "active-proposal-to-strike-off",
                    },
                    "officers": [
                        {
                            "name": "Example Director",
                            "officer_role": "director",
                            "appointed_on": "2026-07-09",
                            "appointments_link": "/officers/example/appointments",
                        }
                    ],
                    "persons_with_significant_control": [],
                    "filing_history": [
                        {
                            "date": "2026-07-10",
                            "type": "AP01",
                            "category": "officers",
                            "description": "appoint-person-director-company",
                            "transaction_id": "txn-1",
                        }
                    ],
                    "charges": [],
                }
            ],
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            previous_path = temp / "previous.json"
            current_path = temp / "current.json"
            output_path = temp / "diff.json"
            previous_path.write_text(json.dumps(previous), encoding="utf-8")
            current_path.write_text(json.dumps(current), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(DIFF),
                    "--previous",
                    str(previous_path),
                    "--current",
                    str(current_path),
                    "--output",
                    str(output_path),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(output_path.read_text(encoding="utf-8"))

        change_types = {change["change_type"] for change in payload["changes"]}
        self.assertEqual(payload["watchlist_scope_fingerprint"], fingerprint)
        self.assertIn("profile-status", change_types)
        self.assertIn("officer-added", change_types)
        self.assertIn("new-filing", change_types)

    def test_diff_rejects_mismatched_scope(self) -> None:
        previous = {
            "date_range": {"start": "2026-06-29", "end": "2026-07-05"},
            "collection_scope": {"watchlist_fingerprint": "scope-a"},
            "companies": [],
        }
        current = {
            "date_range": {"start": "2026-07-06", "end": "2026-07-12"},
            "collection_scope": {"watchlist_fingerprint": "scope-b"},
            "companies": [],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            previous_path = temp / "previous.json"
            current_path = temp / "current.json"
            previous_path.write_text(json.dumps(previous), encoding="utf-8")
            current_path.write_text(json.dumps(current), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(DIFF),
                    "--previous",
                    str(previous_path),
                    "--current",
                    str(current_path),
                    "--output",
                    str(temp / "diff.json"),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertEqual(result.returncode, 2)
        self.assertIn("watchlist scopes do not match", result.stderr)


if __name__ == "__main__":
    unittest.main()
