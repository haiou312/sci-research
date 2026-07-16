#!/usr/bin/env python3
"""Validate the installed Sci-Research plugin bundle without running a pipeline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
import tomllib


REQUIRED_SKILLS = {
    "daily-news-intelligence",
    "daily-briefing",
    "reputation-track",
    "setup-sci-research-runtime",
}

REQUIRED_AGENTS = {
    "sci-research-briefing-curator",
    "sci-research-daily-editor",
    "sci-research-daily-fact-extractor",
    "sci-research-daily-news-scanner",
    "sci-research-daily-news-writer",
    "sci-research-news-verifier",
    "sci-research-reputation-scanner",
    "sci-research-reputation-verifier",
    "sci-research-reputation-writer",
}


def fail(message: str) -> None:
    raise ValueError(message)


def inside(root: Path, candidate: Path) -> bool:
    try:
        candidate.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def validate(plugin_root: Path) -> tuple[int, int]:
    manifest_path = plugin_root / ".codex-plugin/plugin.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("name") != "sci-research":
        fail(f"unexpected plugin name in {manifest_path}")
    skills_value = manifest.get("skills")
    if not isinstance(skills_value, str):
        fail("plugin manifest must declare a string skills path")
    skills_root = (plugin_root / skills_value).resolve()
    if not inside(plugin_root, skills_root) or not skills_root.is_dir():
        fail(f"skills path escapes the plugin or is missing: {skills_root}")
    skill_names = {
        path.parent.name for path in skills_root.glob("*/SKILL.md") if path.is_file()
    }
    missing_skills = sorted(REQUIRED_SKILLS - skill_names)
    if missing_skills:
        fail(f"missing required skills: {', '.join(missing_skills)}")

    agents_dir = plugin_root / ".codex/agents"
    names: set[str] = set()
    for path in sorted(agents_dir.glob("*.toml")):
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        for key in ("name", "description", "developer_instructions"):
            if not isinstance(data.get(key), str) or not data[key].strip():
                fail(f"{path} is missing required string field {key}")
        name = data["name"]
        if not name.startswith("sci-research-"):
            fail(f"agent name is not namespaced: {name}")
        if path.stem != name:
            fail(f"agent filename does not match name: {path.name} != {name}.toml")
        if name in names:
            fail(f"duplicate agent name: {name}")
        names.add(name)
    missing_agents = sorted(REQUIRED_AGENTS - names)
    unexpected_agents = sorted(names - REQUIRED_AGENTS)
    if missing_agents or unexpected_agents:
        fail(
            "agent payload mismatch: "
            f"missing={missing_agents or 'none'} "
            f"unexpected={unexpected_agents or 'none'}"
        )

    hooks_path = plugin_root / "hooks/hooks.json"
    hooks = json.loads(hooks_path.read_text(encoding="utf-8"))
    commands: list[str] = []
    for entries in hooks.get("hooks", {}).values():
        for entry in entries:
            for hook in entry.get("hooks", []):
                command = hook.get("command")
                if isinstance(command, str):
                    commands.append(command)
    if len(commands) != 2:
        fail(f"expected 2 hook commands, found {len(commands)}")
    for command in commands:
        if "$PLUGIN_ROOT" not in command:
            fail(f"hook command does not use $PLUGIN_ROOT: {command}")
        match = re.search(r"\$PLUGIN_ROOT/([^\"']+)", command)
        if not match:
            fail(f"cannot resolve hook command path: {command}")
        target = plugin_root / match.group(1)
        if not inside(plugin_root, target) or not target.is_file():
            fail(f"hook command target is missing or unsafe: {target}")

    setup_script = (
        plugin_root
        / "skills/setup-sci-research-runtime/scripts/sync_runtime.py"
    )
    if not setup_script.is_file():
        fail(f"runtime sync script is missing: {setup_script}")
    runtime_config = (
        plugin_root
        / "skills/setup-sci-research-runtime/runtime/config.toml"
    )
    try:
        config = tomllib.loads(runtime_config.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        fail(f"runtime config template is invalid: {runtime_config}: {exc}")
    agents = config.get("agents")
    max_threads = agents.get("max_threads") if isinstance(agents, dict) else None
    max_depth = agents.get("max_depth") if isinstance(agents, dict) else None
    if (
        isinstance(max_threads, bool)
        or not isinstance(max_threads, int)
        or max_threads < 10
    ):
        fail("runtime config template must set agents.max_threads >= 10")
    if max_depth != 1:
        fail("runtime config template must set agents.max_depth = 1")
    return len(skill_names), len(names)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--plugin-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Plugin root to validate (default: root containing this script)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    plugin_root = args.plugin_root.expanduser().resolve()
    try:
        skill_count, agent_count = validate(plugin_root)
    except (OSError, ValueError, KeyError, json.JSONDecodeError, tomllib.TOMLDecodeError) as exc:
        print(f"PLUGIN_BUNDLE_ERROR: {exc}", file=sys.stderr)
        return 2
    print(
        f"PLUGIN_BUNDLE_OK: root={plugin_root} skills={skill_count} agents={agent_count}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
