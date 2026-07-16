#!/usr/bin/env python3
"""Diff two scoped Companies House snapshots."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Callable


def load_snapshot(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read snapshot {path}: {exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("companies"), list):
        raise ValueError(f"invalid snapshot shape: {path}")
    return data


def company_map(snapshot: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result = {}
    for item in snapshot.get("companies", []):
        if not isinstance(item, dict):
            continue
        number = item.get("company_number")
        if isinstance(number, str) and number:
            result[number] = item
    return result


def validate_comparable_snapshots(
    previous: dict[str, Any],
    current: dict[str, Any],
) -> str:
    previous_range = (
        previous.get("date_range")
        if isinstance(previous.get("date_range"), dict)
        else {}
    )
    current_range = (
        current.get("date_range")
        if isinstance(current.get("date_range"), dict)
        else {}
    )
    previous_end = previous_range.get("end")
    current_start = current_range.get("start")
    if not isinstance(previous_end, str) or not isinstance(current_start, str):
        raise ValueError("snapshots must include ISO date_range.start/end values")
    if previous_end >= current_start:
        raise ValueError(
            "previous snapshot report period must end before current period starts"
        )

    previous_scope = (
        previous.get("collection_scope")
        if isinstance(previous.get("collection_scope"), dict)
        else {}
    )
    current_scope = (
        current.get("collection_scope")
        if isinstance(current.get("collection_scope"), dict)
        else {}
    )
    previous_fingerprint = previous_scope.get("watchlist_fingerprint")
    current_fingerprint = current_scope.get("watchlist_fingerprint")
    if not isinstance(previous_fingerprint, str) or not isinstance(
        current_fingerprint, str
    ):
        raise ValueError(
            "snapshots must include collection_scope.watchlist_fingerprint"
        )
    if previous_fingerprint != current_fingerprint:
        raise ValueError("snapshot watchlist scopes do not match")
    return current_fingerprint


def stable(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def add_change(
    changes: list[dict[str, Any]],
    company: dict[str, Any],
    change_type: str,
    importance: str,
    before: Any,
    after: Any,
    evidence_date: str | None = None,
) -> None:
    profile = company.get("profile") if isinstance(company.get("profile"), dict) else {}
    changes.append(
        {
            "company_number": company.get("company_number"),
            "company_name": profile.get("company_name"),
            "change_type": change_type,
            "importance_hint": importance,
            "evidence_date": evidence_date,
            "before": before,
            "after": after,
        }
    )


def index_items(
    items: Any,
    key_fn: Callable[[dict[str, Any]], str],
) -> dict[str, dict[str, Any]]:
    result = {}
    for item in items if isinstance(items, list) else []:
        if isinstance(item, dict):
            key = key_fn(item)
            if key:
                result[key] = item
    return result


def officer_key(item: dict[str, Any]) -> str:
    return str(
        item.get("appointments_link")
        or "|".join(
            str(item.get(field) or "")
            for field in ("name", "officer_role", "appointed_on")
        )
    )


def psc_key(item: dict[str, Any]) -> str:
    identification = (
        item.get("identification")
        if isinstance(item.get("identification"), dict)
        else {}
    )
    return str(
        item.get("self_link")
        or "|".join(
            [
                str(item.get("name") or ""),
                str(item.get("kind") or ""),
                str(identification.get("registration_number") or ""),
            ]
        )
    )


def filing_key(item: dict[str, Any]) -> str:
    return str(
        item.get("transaction_id")
        or "|".join(
            str(item.get(field) or "")
            for field in ("date", "type", "description")
        )
    )


def charge_key(item: dict[str, Any]) -> str:
    return str(
        item.get("charge_code")
        or "|".join(
            str(item.get(field) or "")
            for field in ("created_on", "delivered_on", "status")
        )
    )


def compare_profile(
    previous: dict[str, Any],
    current: dict[str, Any],
    changes: list[dict[str, Any]],
) -> None:
    old = previous.get("profile") if isinstance(previous.get("profile"), dict) else {}
    new = current.get("profile") if isinstance(current.get("profile"), dict) else {}
    fields = {
        "company_name": ("name", "high"),
        "company_status": ("status", "high"),
        "company_status_detail": ("status-detail", "high"),
        "type": ("company-type", "medium"),
        "subtype": ("company-subtype", "medium"),
        "date_of_cessation": ("cessation", "high"),
        "sic_codes": ("sic-codes", "medium"),
        "registered_office_address": ("registered-office", "medium"),
        "has_insolvency_history": ("insolvency-history", "high"),
    }
    for field, (label, importance) in fields.items():
        if stable(old.get(field)) != stable(new.get(field)):
            add_change(
                changes,
                current,
                f"profile-{label}",
                importance,
                old.get(field),
                new.get(field),
            )


def compare_collection(
    previous: dict[str, Any],
    current: dict[str, Any],
    field: str,
    key_fn: Callable[[dict[str, Any]], str],
    added_type: str,
    removed_type: str,
    importance: str,
    changes: list[dict[str, Any]],
    date_field: str | None = None,
) -> None:
    old_items = index_items(previous.get(field), key_fn)
    new_items = index_items(current.get(field), key_fn)
    for key in sorted(new_items.keys() - old_items.keys()):
        item = new_items[key]
        add_change(
            changes,
            current,
            added_type,
            importance,
            None,
            item,
            str(item.get(date_field)) if date_field and item.get(date_field) else None,
        )
    for key in sorted(old_items.keys() - new_items.keys()):
        item = old_items[key]
        add_change(
            changes,
            current,
            removed_type,
            importance,
            item,
            None,
            str(item.get(date_field)) if date_field and item.get(date_field) else None,
        )
    for key in sorted(old_items.keys() & new_items.keys()):
        if stable(old_items[key]) != stable(new_items[key]):
            item = new_items[key]
            add_change(
                changes,
                current,
                f"{added_type}-updated",
                importance,
                old_items[key],
                item,
                str(item.get(date_field))
                if date_field and item.get(date_field)
                else None,
            )


def filing_importance(item: dict[str, Any]) -> str:
    category = item.get("category")
    if category in {"capital", "liquidation", "mortgage", "change-of-name"}:
        return "high"
    if category in {"accounts", "officers", "address", "resolution"}:
        return "medium"
    return "monitor"


def compare_filings(
    previous: dict[str, Any],
    current: dict[str, Any],
    changes: list[dict[str, Any]],
) -> None:
    old_items = index_items(previous.get("filing_history"), filing_key)
    new_items = index_items(current.get("filing_history"), filing_key)
    for key in sorted(new_items.keys() - old_items.keys()):
        item = new_items[key]
        add_change(
            changes,
            current,
            "new-filing",
            filing_importance(item),
            None,
            item,
            str(item.get("date")) if item.get("date") else None,
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--previous", required=True, type=Path)
    parser.add_argument("--current", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        previous_snapshot = load_snapshot(args.previous.expanduser())
        current_snapshot = load_snapshot(args.current.expanduser())
        scope_fingerprint = validate_comparable_snapshots(
            previous_snapshot,
            current_snapshot,
        )
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    old_companies = company_map(previous_snapshot)
    new_companies = company_map(current_snapshot)
    changes: list[dict[str, Any]] = []

    for number in sorted(new_companies.keys() - old_companies.keys()):
        company = new_companies[number]
        profile = company.get("profile") if isinstance(company.get("profile"), dict) else {}
        add_change(
            changes,
            company,
            "newly-observed-company",
            "high"
            if profile.get("date_of_creation")
            and profile.get("date_of_creation")
            >= current_snapshot.get("date_range", {}).get("start", "")
            else "medium",
            None,
            profile,
            profile.get("date_of_creation"),
        )

    for number in sorted(old_companies.keys() - new_companies.keys()):
        old = old_companies[number]
        profile = old.get("profile") if isinstance(old.get("profile"), dict) else {}
        changes.append(
            {
                "company_number": number,
                "company_name": profile.get("company_name"),
                "change_type": "company-missing-from-current-snapshot",
                "importance_hint": "investigate",
                "evidence_date": None,
                "before": profile,
                "after": None,
            }
        )

    for number in sorted(old_companies.keys() & new_companies.keys()):
        old = old_companies[number]
        new = new_companies[number]
        compare_profile(old, new, changes)
        compare_collection(
            old,
            new,
            "officers",
            officer_key,
            "officer-added",
            "officer-removed",
            "medium",
            changes,
            date_field="appointed_on",
        )
        compare_collection(
            old,
            new,
            "persons_with_significant_control",
            psc_key,
            "psc-added",
            "psc-removed",
            "high",
            changes,
            date_field="notified_on",
        )
        compare_filings(old, new, changes)
        compare_collection(
            old,
            new,
            "charges",
            charge_key,
            "charge-added",
            "charge-removed",
            "high",
            changes,
            date_field="delivered_on",
        )

    payload = {
        "schema_version": 1,
        "status": "complete",
        "previous_snapshot": str(args.previous.expanduser()),
        "current_snapshot": str(args.current.expanduser()),
        "previous_fetched_at": previous_snapshot.get("fetched_at"),
        "current_fetched_at": current_snapshot.get("fetched_at"),
        "previous_company_count": len(old_companies),
        "current_company_count": len(new_companies),
        "watchlist_scope_fingerprint": scope_fingerprint,
        "change_count": len(changes),
        "changes": changes,
        "interpretation_warning": (
            "Observed snapshot differences require filing-date and ownership "
            "verification before being described as effective corporate changes."
        ),
    }
    output = args.output.expanduser()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"OK: wrote {output} changes={len(changes)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
