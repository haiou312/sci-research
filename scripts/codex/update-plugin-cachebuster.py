#!/usr/bin/env python3
"""Refresh the Codex cachebuster suffix in this plugin's manifest."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
import re
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "plugin_root",
        nargs="?",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Plugin root containing .codex-plugin/plugin.json",
    )
    parser.add_argument(
        "--cachebuster",
        help="Optional cachebuster token; defaults to a UTC timestamp",
    )
    return parser.parse_args()


def sanitize(value: str) -> str:
    sanitized = re.sub(r"[^a-z0-9-]+", "-", value.strip().lower())
    sanitized = re.sub(r"-{2,}", "-", sanitized).strip("-")
    if not sanitized:
        raise ValueError("cachebuster must contain at least one letter or digit")
    return sanitized


def main() -> int:
    args = parse_args()
    plugin_root = args.plugin_root.expanduser().resolve()
    manifest_path = plugin_root / ".codex-plugin/plugin.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    version = manifest.get("version")
    if not isinstance(version, str) or not version.strip():
        raise ValueError(f"{manifest_path} has no valid version")

    token = args.cachebuster or datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    next_version = f"{version.split('+', 1)[0]}+codex.{sanitize(token)}"
    manifest["version"] = next_version
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    print(f"Updated plugin version: {version} -> {next_version}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
