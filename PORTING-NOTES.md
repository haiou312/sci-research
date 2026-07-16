# Codex Plugin Status

The repository now uses native Codex plugin structure and TOML subagents. This note records only current validation status and remaining runtime checks.

## Completed

- Nine namespaced native agents are defined in `.codex/agents/sci-research-*.toml` with an explicit GPT-5.6 Sol / Terra / Luna allocation (plus GPT-5.4 mini for Fact Manifest extraction) and per-agent reasoning effort.
- Marketplace installation is treated as bundle distribution, not agent registration. `$sci-research:setup-sci-research-runtime` installs and verifies the agent payload under the active project's `.codex/agents/` with dry-run, backup, conflict protection, hashes, and uninstall support.
- The three pipeline skills select exact named custom-agent roles with `fork_turns="none"`, pass absolute runtime paths, and pass upstream outputs through prompt text.
- File-writing stages use `apply_patch`; the PostToolUse Markdown hook reports the resulting invalid state, and a direct pre-delivery check hard-stops export/email until it is corrected.
- Plugin packaging, TOML, JSON, Node, Python and Bash syntax checks have passed.
- The plugin has been installed successfully in isolated Codex homes.
- Pipeline E uses one Luna Scanner to resolve the company and current executives through Yahoo Finance, then search exact-date non-mainland-China media and public social content.
- Pipeline C and E default to user-level output directories; Pipeline D has separate input and output directories.
- Pipeline D declares python-docx in requirements.txt and no longer installs packages during a run.

## Remaining runtime validation

1. In a new task opened after runtime setup, spawn each `sci-research-*` role with a no-op contract probe. Confirm the custom-agent selector and the configured model/reasoning metadata on the child thread.
2. Run a minimal Pipeline C invocation without email. Confirm sequential handoff, PostToolUse feedback, the direct format gate, and pandoc output.
3. Install requirements.txt, then run Pipeline D against Pipeline C sample Markdown. Verify branded docx generation and email dry-run.
4. Run Pipeline E. Verify Yahoo company/executive resolution, non-mainland-China media and public-social discovery, low/medium/high verification, clean-scan silence, and email dry-run.

## Runtime assumptions to confirm

- The target Codex App/CLI surface exposes a custom-agent selector that can start the project-installed `sci-research-*` roles. File presence alone is not accepted as proof.
- A single skill invocation can complete its intended sequence of native agent stages under the user's approval mode.
- The configured gpt-5.6-sol, gpt-5.6-terra, gpt-5.6-luna and gpt-5.4-mini model identifiers, plus their requested reasoning-effort values, are accepted by the target Codex version.

If any assumption fails, record the exact Codex version, command, error, and stage in the validation report before changing the architecture.
