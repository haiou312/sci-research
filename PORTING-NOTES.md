# Codex Plugin Status

The repository now uses native Codex plugin structure and TOML subagents. This note records only current validation status and remaining runtime checks.

## Completed

- Ten native agents are defined in .codex/agents/*.toml with an explicit GPT-5.6 Sol / Terra / Luna allocation (plus GPT-5.4 mini for Fact Manifest extraction) and per-agent reasoning effort.
- The three skills dispatch their named TOML agents and pass upstream outputs through prompt text.
- File-writing stages and the Markdown hook use apply_patch semantics.
- Plugin packaging, TOML, JSON, Node, Python and Bash syntax checks have passed.
- The plugin has been installed successfully in isolated Codex homes.
- Pipeline E social discovery uses WebSearch `search` / `open_page` for publicly indexed Reddit and X content. No MCP configuration, credentials or platform API is required.
- Pipeline C and E default to user-level output directories; Pipeline D has separate input and output directories.
- GitHub Pages publishing is explicit opt-in and requires a user-provided target repository.
- Pipeline D declares its pinned python-docx dependency in requirements.txt and no longer installs packages during a run.

## Remaining runtime validation

1. Run a minimal Pipeline C invocation without email or publishing. Confirm native agent discovery, sequential handoff, apply_patch hook behavior, and pandoc output.
2. Install requirements.txt, then run Pipeline D against Pipeline C sample Markdown. Verify branded docx generation and email dry-run.
3. Run Pipeline E with News, Reddit and X enabled. Verify date handling, social coverage gaps, clean-scan silence, and email dry-run.

## Runtime assumptions to confirm

- The target Codex installation makes plugin-bundled .codex/agents/*.toml available to skill orchestration.
- A single skill invocation can complete its intended sequence of native agent stages under the user's approval mode.
- The configured gpt-5.6-sol, gpt-5.6-terra, gpt-5.6-luna and gpt-5.4-mini model identifiers, plus their requested reasoning-effort values, are accepted by the target Codex version.

If any assumption fails, record the exact Codex version, command, error, and stage in the validation report before changing the architecture.
