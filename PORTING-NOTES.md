# Codex Plugin Status

The repository now uses native Codex plugin structure and TOML subagents. This note records only current validation status and remaining runtime checks.

## Completed

- Fifteen namespaced native agents are defined in `.codex/agents/sci-research-*.toml` with an explicit GPT-5.6 Sol / Terra / Luna allocation (plus GPT-5.4 mini for Fact Manifest extraction) and per-agent reasoning effort.
- Marketplace installation is treated as bundle distribution, not agent registration. `$sci-research:setup-sci-research-runtime` installs and verifies the agent payload under the active project's `.codex/agents/`, plus project-scoped `agents.max_threads >= 10`, with dry-run, backup, conflict protection, hashes, and uninstall support.
- The four pipeline skills select exact named custom-agent roles with `fork_turns="none"`, pass absolute runtime paths, pass upstream outputs through prompt text, and close each child after durable handoff so completed threads do not accumulate.
- File-writing stages use `apply_patch`; Pipeline C and F PostToolUse Markdown hooks report invalid output, and direct pre-delivery checks hard-stop export/email until it is corrected.
- Plugin packaging, TOML, JSON, Node, Python and Bash syntax checks have passed.
- The plugin has been installed successfully in isolated Codex homes.
- Pipeline E uses one Luna Scanner to resolve the company and current executives through Yahoo Finance, then search exact-date non-mainland-China media and public social content.
- Pipeline C, E, and F default to user-level output directories; Pipeline D has separate input and output directories.
- Pipelines D and F declare python-docx in requirements.txt and never install packages during a run.
- Pipeline F defines five parallel discovery lanes, a deterministic Companies House collector/diff, a dedicated entity analyst, Verifier, Fact Manifest, Chinese Writer/Editor, a format gate, and institutional DOCX export.

## Remaining runtime validation

1. In a new task opened after runtime setup, spawn each `sci-research-*` role with a no-op contract probe. Confirm the custom-agent selector and the configured model/reasoning metadata on the child thread.
2. Run a minimal Pipeline C invocation without email. Confirm sequential handoff, PostToolUse feedback, the direct format gate, and pandoc output.
3. Install requirements.txt, then run Pipeline D against Pipeline C sample Markdown. Verify branded docx generation and email dry-run.
4. Run Pipeline E. Verify Yahoo company/executive resolution, non-mainland-China media and public-social discovery, low/medium/high verification, clean-scan silence, and email dry-run.
5. Run Pipeline F without email. Verify all five Scanner lanes, scoped Companies House API/watchlist coverage, identity confidence labels, format gate, image fallback, DOCX generation, and agent closure.

## Runtime assumptions to confirm

- The target Codex App/CLI surface exposes a custom-agent selector that can start the project-installed `sci-research-*` roles. File presence alone is not accepted as proof.
- The target Codex App/CLI surface honors project `.codex/config.toml`, supports `agents.max_threads`, and releases a child slot after `close_agent`.
- A single skill invocation can complete its intended sequence of native agent stages under the user's approval mode.
- The configured gpt-5.6-sol, gpt-5.6-terra, gpt-5.6-luna and gpt-5.4-mini model identifiers, plus their requested reasoning-effort values, are accepted by the target Codex version.

If any assumption fails, record the exact Codex version, command, error, and stage in the validation report before changing the architecture.
