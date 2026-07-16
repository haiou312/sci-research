---
name: setup-sci-research-runtime
description: "Install, update, verify, or remove the project-scoped Codex agents and concurrency config required by the Sci-Research marketplace skills. Use when Sci-Research reports missing named agents or agent thread limits, after installing or updating the plugin, or when preparing a dedicated ~/.sci-research workspace."
---

# Setup Sci-Research Runtime

Install the plugin's native Codex agents and required subagent concurrency setting into the current workspace. This skill configures the runtime only; it never runs Pipelines C, D, E, or F.

## Rules

- Default `PROJECT_ROOT` to the current working directory. Use another directory only when the user explicitly names it.
- Install only under `${PROJECT_ROOT}/.codex/`; never modify `~/.codex/config.toml`, global agents, MCP servers, prompts, Git hooks, or Python packages.
- Pipeline C needs seven concurrent Scanner threads for China. Require project config `agents.max_threads >= 10`; keep `agents.max_depth = 1` in a newly created config because Sci-Research does not use recursive delegation.
- If `${PROJECT_ROOT}/.codex/config.toml` is absent, create it from the bundled runtime template. If it already exists, validate `agents.max_threads >= 10` and preserve the file byte-for-byte. Stop with the exact required TOML block when an existing config is missing the setting or sets it below 10.
- Resolve `SKILL_DIR` as the absolute directory containing this `SKILL.md`, and derive `PLUGIN_ROOT` from it. Never hard-code a marketplace cache version.
- Run the bundle checker before install or update.
- Run a dry-run before applying changes.
- After install or update, tell the user to start a new Codex task in `PROJECT_ROOT`; the current task may not refresh its custom-agent registry.
- Plugin hooks are loaded from the installed bundle, not copied into the project. After a plugin install or update, tell the user to review and trust the Sci-Research hooks in `/hooks` if Codex asks for approval.

## Commands

```bash
SKILL_DIR=<absolute path to skills/setup-sci-research-runtime>
PLUGIN_ROOT="$(cd "$SKILL_DIR/../.." && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$PWD}"
CHECKER="$PLUGIN_ROOT/scripts/codex/check-plugin-bundle.py"
SYNC="$SKILL_DIR/scripts/sync_runtime.py"
```

### Install Or Update

```bash
python3 "$CHECKER"
python3 "$SYNC" --project-root "$PROJECT_ROOT" --dry-run
python3 "$SYNC" --project-root "$PROJECT_ROOT"
python3 "$SYNC" --project-root "$PROJECT_ROOT" --check
```

If dry-run reports an unmanaged-file conflict or a locally modified managed file, stop and report the exact path. Do not use shell copy commands or overwrite the file manually.

### Check

```bash
python3 "$CHECKER"
python3 "$SYNC" --project-root "$PROJECT_ROOT" --check
```

### Uninstall

Run only when the user explicitly asks to remove the runtime:

```bash
python3 "$SYNC" --project-root "$PROJECT_ROOT" --uninstall
```

Uninstall removes only files recorded in the runtime manifest and refuses to delete locally modified agent files. It removes `.codex/config.toml` only when setup created it and its content is unchanged; user-owned or modified config is retained.

## Completion

Report the project root, plugin version, number of installed agents, verified `max_threads`, manifest path, and backup path when one was created. Remind the user to review `/hooks` when hook trust is pending. Do not claim the pipelines are ready until a new task successfully spawns a named Sci-Research agent.
