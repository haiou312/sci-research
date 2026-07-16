#!/usr/bin/env python3
"""Collect scoped Companies House snapshots for opportunity briefing analysis."""

from __future__ import annotations

import argparse
import base64
from datetime import UTC, date, datetime
import hashlib
import json
import os
from pathlib import Path
import sys
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


API_ROOT = "https://api.company-information.service.gov.uk"
DEFAULT_KEY_ENV = "COMPANIES_HOUSE_API_KEY"


class CollectionError(RuntimeError):
    """Expected collection failure."""


def parse_iso_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid ISO date: {value}") from exc


def normalise_company_number(value: str) -> str:
    return "".join(value.upper().split())


def clean_address(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    allowed = (
        "premises",
        "address_line_1",
        "address_line_2",
        "locality",
        "region",
        "postal_code",
        "country",
    )
    return {
        key: str(value[key]).strip()
        for key in allowed
        if value.get(key) not in (None, "")
    }


def clean_profile(raw: dict[str, Any]) -> dict[str, Any]:
    accounts = raw.get("accounts") if isinstance(raw.get("accounts"), dict) else {}
    confirmation = (
        raw.get("confirmation_statement")
        if isinstance(raw.get("confirmation_statement"), dict)
        else {}
    )
    return {
        "company_name": raw.get("company_name"),
        "company_number": raw.get("company_number"),
        "company_status": raw.get("company_status"),
        "company_status_detail": raw.get("company_status_detail"),
        "type": raw.get("type"),
        "subtype": raw.get("subtype"),
        "date_of_creation": raw.get("date_of_creation"),
        "date_of_cessation": raw.get("date_of_cessation"),
        "sic_codes": raw.get("sic_codes", []),
        "registered_office_address": clean_address(raw.get("registered_office_address")),
        "has_charges": raw.get("has_charges"),
        "has_insolvency_history": raw.get("has_insolvency_history"),
        "accounts": {
            "last_accounts": accounts.get("last_accounts"),
            "next_due": accounts.get("next_due"),
            "overdue": accounts.get("overdue"),
        },
        "confirmation_statement": {
            "last_made_up_to": confirmation.get("last_made_up_to"),
            "next_due": confirmation.get("next_due"),
            "overdue": confirmation.get("overdue"),
        },
        "links": raw.get("links", {}),
    }


def clean_officers(raw: dict[str, Any]) -> list[dict[str, Any]]:
    result = []
    for item in raw.get("items", []) if isinstance(raw, dict) else []:
        if not isinstance(item, dict):
            continue
        links = item.get("links") if isinstance(item.get("links"), dict) else {}
        officer_links = (
            links.get("officer") if isinstance(links.get("officer"), dict) else {}
        )
        result.append(
            {
                "name": item.get("name"),
                "officer_role": item.get("officer_role"),
                "appointed_on": item.get("appointed_on"),
                "resigned_on": item.get("resigned_on"),
                "nationality": item.get("nationality"),
                "country_of_residence": item.get("country_of_residence"),
                "appointments_link": officer_links.get("appointments"),
            }
        )
    return result


def clean_psc(raw: dict[str, Any]) -> list[dict[str, Any]]:
    result = []
    for item in raw.get("items", []) if isinstance(raw, dict) else []:
        if not isinstance(item, dict):
            continue
        identification = (
            item.get("identification")
            if isinstance(item.get("identification"), dict)
            else {}
        )
        links = item.get("links") if isinstance(item.get("links"), dict) else {}
        result.append(
            {
                "name": item.get("name"),
                "kind": item.get("kind"),
                "notified_on": item.get("notified_on"),
                "ceased_on": item.get("ceased_on"),
                "ceased": item.get("ceased"),
                "nationality": item.get("nationality"),
                "country_of_residence": item.get("country_of_residence"),
                "natures_of_control": item.get("natures_of_control", []),
                "identification": {
                    "country_registered": identification.get("country_registered"),
                    "legal_authority": identification.get("legal_authority"),
                    "legal_form": identification.get("legal_form"),
                    "place_registered": identification.get("place_registered"),
                    "registration_number": identification.get("registration_number"),
                },
                "self_link": links.get("self"),
            }
        )
    return result


def clean_filings(raw: dict[str, Any]) -> list[dict[str, Any]]:
    result = []
    for item in raw.get("items", []) if isinstance(raw, dict) else []:
        if not isinstance(item, dict):
            continue
        links = item.get("links") if isinstance(item.get("links"), dict) else {}
        result.append(
            {
                "date": item.get("date"),
                "type": item.get("type"),
                "category": item.get("category"),
                "subcategory": item.get("subcategory"),
                "description": item.get("description"),
                "transaction_id": item.get("transaction_id"),
                "pages": item.get("pages"),
                "document_metadata": links.get("document_metadata"),
                "self_link": links.get("self"),
            }
        )
    return result


def clean_charges(raw: dict[str, Any]) -> list[dict[str, Any]]:
    result = []
    for item in raw.get("items", []) if isinstance(raw, dict) else []:
        if not isinstance(item, dict):
            continue
        classification = (
            item.get("classification")
            if isinstance(item.get("classification"), dict)
            else {}
        )
        persons = []
        for person in item.get("persons_entitled", []):
            if isinstance(person, dict) and person.get("name"):
                persons.append(person["name"])
        result.append(
            {
                "charge_code": item.get("charge_code"),
                "delivered_on": item.get("delivered_on"),
                "created_on": item.get("created_on"),
                "satisfied_on": item.get("satisfied_on"),
                "status": item.get("status"),
                "classification": classification,
                "persons_entitled": persons,
                "transactions": item.get("transactions", []),
            }
        )
    return result


class CompaniesHouseClient:
    def __init__(self, api_key: str, timeout: float = 20.0) -> None:
        token = base64.b64encode(f"{api_key}:".encode("utf-8")).decode("ascii")
        self.headers = {
            "Authorization": f"Basic {token}",
            "Accept": "application/json",
            "User-Agent": "sci-research-china-opportunity-briefing/1",
        }
        self.timeout = timeout
        self.request_count = 0

    def get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        *,
        allow_404: bool = False,
    ) -> dict[str, Any]:
        query = f"?{urlencode(params, doseq=True)}" if params else ""
        url = f"{API_ROOT}{path}{query}"
        last_error: Exception | None = None
        for attempt in range(4):
            self.request_count += 1
            request = Request(url, headers=self.headers)
            try:
                with urlopen(request, timeout=self.timeout) as response:
                    payload = response.read()
                if not payload:
                    return {}
                data = json.loads(payload.decode("utf-8"))
                if not isinstance(data, dict):
                    raise CollectionError(f"non-object JSON returned by {path}")
                return data
            except HTTPError as exc:
                if exc.code == 404 and allow_404:
                    return {}
                if exc.code == 429 or 500 <= exc.code <= 599:
                    last_error = exc
                    time.sleep(2**attempt)
                    continue
                body = exc.read().decode("utf-8", errors="replace")[:300]
                raise CollectionError(
                    f"Companies House HTTP {exc.code} for {path}: {body}"
                ) from exc
            except (URLError, TimeoutError, json.JSONDecodeError) as exc:
                last_error = exc
                time.sleep(2**attempt)
        raise CollectionError(f"Companies House request failed for {path}: {last_error}")


def load_watchlist(path: Path | None) -> list[dict[str, Any]]:
    if path is None:
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CollectionError(f"cannot read watchlist {path}: {exc}") from exc
    parents = data.get("parents") if isinstance(data, dict) else None
    if not isinstance(parents, list):
        raise CollectionError("watchlist must contain a parents array")
    result = []
    for index, item in enumerate(parents, start=1):
        if not isinstance(item, dict):
            raise CollectionError(f"watchlist parent {index} is not an object")
        parent_name = item.get("parent_name")
        if not isinstance(parent_name, str) or not parent_name.strip():
            raise CollectionError(f"watchlist parent {index} lacks parent_name")
        aliases = item.get("aliases", [])
        numbers = item.get("company_numbers", [])
        if not isinstance(aliases, list) or not all(
            isinstance(value, str) and value.strip() for value in aliases
        ):
            raise CollectionError(f"watchlist parent {index} has invalid aliases")
        if not isinstance(numbers, list) or not all(
            isinstance(value, str) and value.strip() for value in numbers
        ):
            raise CollectionError(
                f"watchlist parent {index} has invalid company_numbers"
            )
        result.append(
            {
                "parent_name": parent_name.strip(),
                "aliases": [value.strip() for value in aliases],
                "company_numbers": [
                    normalise_company_number(value) for value in numbers
                ],
                "notes": item.get("notes"),
            }
        )
    return result


def add_discovery(
    discoveries: dict[str, list[dict[str, Any]]],
    company_number: str,
    discovery: dict[str, Any],
) -> None:
    bucket = discoveries.setdefault(company_number, [])
    if discovery not in bucket:
        bucket.append(discovery)


def build_watchlist_scope(
    watchlist: list[dict[str, Any]],
    watchlist_path: Path | None,
) -> dict[str, Any]:
    scope = {
        "watchlist_path": (
            str(watchlist_path.expanduser().resolve()) if watchlist_path else None
        ),
        "parents": [
            {
                "parent_name": item["parent_name"],
                "aliases": sorted(item["aliases"]),
                "company_numbers": sorted(item["company_numbers"]),
            }
            for item in watchlist
        ],
    }
    encoded = json.dumps(
        scope,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    scope["watchlist_fingerprint"] = hashlib.sha256(encoded).hexdigest()
    return scope


def collect_company(
    client: CompaniesHouseClient,
    company_number: str,
    discoveries: list[dict[str, Any]],
) -> dict[str, Any]:
    profile = client.get(f"/company/{company_number}")
    resolved_number = normalise_company_number(
        str(profile.get("company_number") or company_number)
    )
    base = f"/company/{resolved_number}"
    officers = client.get(
        f"{base}/officers",
        {"items_per_page": 100},
        allow_404=True,
    )
    psc = client.get(
        f"{base}/persons-with-significant-control",
        {"items_per_page": 100, "start_index": 0, "register_view": "false"},
        allow_404=True,
    )
    filings = client.get(
        f"{base}/filing-history",
        {"items_per_page": 100},
        allow_404=True,
    )
    charges = client.get(
        f"{base}/charges",
        {"items_per_page": 100},
        allow_404=True,
    )
    return {
        "company_number": resolved_number,
        "discovery": discoveries,
        "profile": clean_profile(profile),
        "officers": clean_officers(officers),
        "persons_with_significant_control": clean_psc(psc),
        "filing_history": clean_filings(filings),
        "charges": clean_charges(charges),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-date", required=True, type=parse_iso_date)
    parser.add_argument("--end-date", required=True, type=parse_iso_date)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--watchlist", type=Path)
    parser.add_argument("--company-number", action="append", default=[])
    parser.add_argument("--api-key-env", default=DEFAULT_KEY_ENV)
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--max-search-results", type=int, default=200)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.start_date > args.end_date:
        print("ERROR: start-date must not be after end-date", file=sys.stderr)
        return 2
    if not 1 <= args.max_search_results <= 5000:
        print("ERROR: max-search-results must be between 1 and 5000", file=sys.stderr)
        return 2

    api_key = os.environ.get(args.api_key_env, "").strip()
    if not api_key:
        print(
            f"ERROR: missing Companies House API key in {args.api_key_env}",
            file=sys.stderr,
        )
        return 3

    try:
        watchlist = load_watchlist(args.watchlist)
    except CollectionError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    client = CompaniesHouseClient(api_key, timeout=args.timeout)
    discoveries: dict[str, list[dict[str, Any]]] = {}
    queries: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []

    for raw_number in args.company_number:
        company_number = normalise_company_number(raw_number)
        if company_number:
            add_discovery(
                discoveries,
                company_number,
                {"method": "explicit-company-number", "value": company_number},
            )

    for parent in watchlist:
        for company_number in parent["company_numbers"]:
            add_discovery(
                discoveries,
                company_number,
                {
                    "method": "watchlist-company-number",
                    "parent_name": parent["parent_name"],
                },
            )
        for alias in parent["aliases"]:
            params = {
                "company_name_includes": alias,
                "incorporated_from": args.start_date.isoformat(),
                "incorporated_to": args.end_date.isoformat(),
                "size": args.max_search_results,
                "start_index": 0,
            }
            query_record = {
                "method": "advanced-search",
                "alias": alias,
                "parent_name": parent["parent_name"],
                "params": params,
            }
            try:
                response = client.get("/advanced-search/companies", params)
                items = response.get("items", [])
                query_record["results"] = len(items) if isinstance(items, list) else 0
                if isinstance(items, list):
                    for item in items:
                        if not isinstance(item, dict):
                            continue
                        number = normalise_company_number(
                            str(item.get("company_number", ""))
                        )
                        if number:
                            add_discovery(
                                discoveries,
                                number,
                                {
                                    "method": "watchlist-alias-search",
                                    "alias": alias,
                                    "parent_name": parent["parent_name"],
                                    "matched_name": item.get("company_name"),
                                },
                            )
            except CollectionError as exc:
                query_record["error"] = str(exc)
                errors.append({"scope": f"alias:{alias}", "error": str(exc)})
            queries.append(query_record)

    companies: list[dict[str, Any]] = []
    for company_number in sorted(discoveries):
        try:
            companies.append(
                collect_company(client, company_number, discoveries[company_number])
            )
        except CollectionError as exc:
            errors.append({"scope": f"company:{company_number}", "error": str(exc)})

    payload = {
        "schema_version": 1,
        "status": "partial" if errors else "complete",
        "fetched_at": datetime.now(UTC).isoformat(),
        "date_range": {
            "start": args.start_date.isoformat(),
            "end": args.end_date.isoformat(),
        },
        "watchlist": {
            "path": str(args.watchlist.expanduser()) if args.watchlist else None,
            "parents": [item["parent_name"] for item in watchlist],
        },
        "collection_scope": build_watchlist_scope(watchlist, args.watchlist),
        "coverage_note": (
            "Scoped collection from explicit company numbers and watchlist aliases; "
            "not an exhaustive nationality or ownership search."
        ),
        "request_count": client.request_count,
        "queries": queries,
        "companies": companies,
        "errors": errors,
    }
    output = args.output.expanduser()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"OK: wrote {output} companies={len(companies)} "
        f"requests={client.request_count} errors={len(errors)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
