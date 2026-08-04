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
    "china-outbound-opportunity-briefing",
    "crd-vi-transposition",
    "daily-news-intelligence",
    "daily-briefing",
    "monthly-news-intelligence",
    "reputation-track",
    "setup-sci-research-runtime",
}

REQUIRED_AGENTS = {
    "sci-research-briefing-curator",
    "sci-research-companies-house-analyst",
    "sci-research-daily-editor",
    "sci-research-daily-fact-extractor",
    "sci-research-daily-news-scanner",
    "sci-research-daily-news-writer",
    "sci-research-news-verifier",
    "sci-research-monthly-curator",
    "sci-research-monthly-editor",
    "sci-research-monthly-fact-extractor",
    "sci-research-monthly-verifier",
    "sci-research-monthly-writer",
    "sci-research-opportunity-editor",
    "sci-research-opportunity-fact-extractor",
    "sci-research-opportunity-scanner",
    "sci-research-opportunity-verifier",
    "sci-research-opportunity-writer",
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

    crd_root = skills_root / "crd-vi-transposition"
    crd_required = (
        "references/brave-search-method.md",
        "references/email-spec.md",
        "references/member-state-method.md",
        "references/news-method.md",
        "references/news-sources.json",
        "references/source-method.md",
        "references/table-spec.md",
        "references/weekly-method.md",
        "scripts/build-weekly-search-plan.py",
        "scripts/diff-weekly-state.py",
        "scripts/validate-country-table.py",
        "scripts/validate-current-state.py",
        "scripts/validate-member-states.py",
        "scripts/validate-news-section.py",
        "scripts/weekly-period.py",
    )
    missing_crd = [name for name in crd_required if not (crd_root / name).is_file()]
    if missing_crd:
        fail(f"missing CRD VI weekly resources: {', '.join(missing_crd)}")
    if (crd_root / "references/country-sources.json").exists():
        fail("CRD VI must not bundle a fixed country or national-source registry")
    brave_method_text = (crd_root / "references/brave-search-method.md").read_text(
        encoding="utf-8"
    )
    for tool_name in (
        "mcp__brave_search__brave_web_search",
        "mcp__brave_search__brave_news_search",
    ):
        if tool_name not in brave_method_text:
            fail(f"CRD VI Brave method is missing required MCP tool: {tool_name}")
    news_registry = json.loads(
        (crd_root / "references/news-sources.json").read_text(encoding="utf-8")
    )
    if news_registry.get("search_provider") != {
        "mcp_server": "brave_search",
        "web_tool": "mcp__brave_search__brave_web_search",
        "news_tool": "mcp__brave_search__brave_news_search",
        "context_tool": "mcp__brave_search__brave_llm_context",
        "native_search_fallback": False,
        "news_parameters": {
            "country": "ALL",
            "search_lang": "en",
            "count": 50,
            "offset": 0,
            "safesearch": "moderate",
            "spellcheck": True,
            "freshness": "<period_start>to<period_end>",
        },
    }:
        fail("CRD VI news registry must use Brave Search MCP without native fallback")
    news_lanes = news_registry.get("search_lanes")
    lane_ids = {
        item.get("id")
        for item in news_lanes or []
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    if lane_ids != {
        "national_transposition",
        "third_country_branches",
        "supervisory_implementation",
        "market_response",
    } or len(news_lanes or []) != 4:
        fail("CRD VI news registry must contain exactly the four search lanes")
    source_groups = news_registry.get("source_groups")
    source_classes = {
        item.get("class")
        for item in source_groups or []
        if isinstance(item, dict) and isinstance(item.get("class"), str)
    }
    if source_classes != {
        "official",
        "news_media",
        "industry",
        "professional_analysis",
    }:
        fail("CRD VI news registry has unexpected source classes")
    target_items = news_registry.get("target_items")
    if not isinstance(target_items, dict) or target_items.get("maximum") != 8:
        fail("CRD VI news registry maximum must be 8")

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

    daily_agent_contract = {
        "sci-research-daily-news-scanner": (
            "mcp__google_news__search_news",
            "Do not call `get_news_article`",
            "best-effort",
            "near-duplicates",
        ),
        "sci-research-daily-news-writer": (
            "mcp__google_news__search_news",
            "mcp__google_news__get_news_article",
        ),
        "sci-research-daily-editor": (
            "mcp__google_news__search_news",
            "mcp__google_news__get_news_article",
        ),
        "sci-research-news-verifier": (
            "first report of each event",
            "DROP_DUPLICATE",
            "DROP_NOT_SELECTED",
            "more than 6 unique events",
        ),
    }
    for agent_name, required_tokens in daily_agent_contract.items():
        agent_path = agents_dir / f"{agent_name}.toml"
        instructions = tomllib.loads(agent_path.read_text(encoding="utf-8"))[
            "developer_instructions"
        ]
        missing_tokens = [token for token in required_tokens if token not in instructions]
        if missing_tokens:
            fail(
                f"{agent_path} is missing the Pipeline C agent contract: "
                f"{', '.join(missing_tokens)}"
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
    if len(commands) != 4:
        fail(f"expected 4 hook commands, found {len(commands)}")
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
    web_search = config.get("web_search")
    max_threads = agents.get("max_threads") if isinstance(agents, dict) else None
    max_depth = agents.get("max_depth") if isinstance(agents, dict) else None
    if (
        isinstance(max_threads, bool)
        or not isinstance(max_threads, int)
        or max_threads < 10
    ):
        fail("runtime config template must set agents.max_threads >= 10")
    if web_search != "live":
        fail('runtime config template must set web_search = "live"')
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
