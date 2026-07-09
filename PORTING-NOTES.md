# Codex Port — Migration Notes & Continuation Checklist

Status of the Claude Code → **Codex plugin** migration (official native-TOML-subagent route).
Plugin name kept: `sci-research`. Three pipelines: C `/daily-news-intelligence`, D `/daily-briefing`, E `/reputation-track`.

---

## ✅ DONE (committed)

1. **10 native TOML subagents** — `.codex/agents/*.toml`, generated from `skills/*/agents/*.md` bodies (frontmatter stripped, body → `developer_instructions` TOML literal string). All 10 validated with `tomllib` (parse OK, required fields present, full bodies preserved — scanner = 55 458 chars).
   - Fields per file: `name`, `description` (concise Codex trigger), `model = "gpt-5-codex"`, `model_reasoning_effort` (`low` for ex-sonnet, `high` for ex-opus), `developer_instructions`.
   - Model tiering map applied: sonnet→low (daily-news-scanner, news-verifier, daily-fact-extractor, reputation-scanner, reputation-classifier); opus→high (daily-news-writer, daily-editor, briefing-curator, reputation-resolver, reputation-writer).
2. **Packaging** — `.codex-plugin/plugin.json` (manifest: skills + hooks + mcpServers + interface), `.agents/plugins/marketplace.json` (local source + policy), `.mcp.json` (apidirect placeholder for E).

---

## ⬜ REMAINING (do in a fresh session — context-heavy)

### 1. Rewrite the 3 `SKILL.md` orchestration sections (the functional core)
For each `skills/*/SKILL.md`:
- Replace every "**Subagent Dispatch Rule**" / "general-purpose + embed `agents/*.md` body + explicit model" passage with the **Codex pattern**: the skill instructs the Codex parent to **spawn the named TOML subagent** for each stage, in order, passing the prior stage's full output into the next.
- Fold the **flag table** from the deleted `commands/*.md` into a "## Usage / Arguments" section: list every flag + default; instruct the model to parse `--flag value` / `--flag "quoted"` from the user message; **validate required flags** (C: `--country`; E: `--company`) with halt-and-ask (Codex has no required-param enforcement).
- Keep the pipeline logic identical (no 4-fan-out redesign — the sequential Scanner→Verifier→Fact-Extractor→Writer→Editor chain and the bilingual per-lang Writer/Editor fan-out stay exactly as they are).
- Orchestration skeleton to drop in (C):
  ```
  Parse flags (--country required; --lang default zh; --min-per-category default 2; 6 bilingual combos …).
  Run IN ORDER, spawning the named subagent for each, piping output → next:
    1. spawn daily-news-scanner   -> Scanner Bundle
    2. spawn news-verifier        -> KEEP set
    3. spawn daily-fact-extractor -> Fact Manifest
    4. per lang: spawn daily-news-writer (parallel) -> drafts
    5. per lang: spawn daily-editor (parallel)      -> final docs
    then pandoc + email.
  ```

### 2. Add `skills/*/agents/openai.yaml` x3 (skill metadata)
```yaml
display_name: Daily News Intelligence
short_description: Dated single-country daily news briefing
default_prompt: '--country "" --date  --lang zh'
allow_implicit_invocation: true
```
(Adapt per skill. Note: `skills/*/agents/` in Codex holds `openai.yaml` metadata, NOT agent bodies — the old `agents/*.md` bodies now live in `.codex/agents/*.toml`.)

### 3. Adapt hooks for Codex `apply_patch`
- `hooks/hooks.json`: the PostToolUse `daily-news-format-check` entries currently match `Write` and `Edit`. Codex has no separate Write/Edit tool — edits go through **`apply_patch`**. Replace the two matcher entries with a **single `apply_patch` matcher** (avoids double-firing). PreToolUse `email-send-guard` keeps matcher `Bash`.
- `scripts/hooks/daily-news-format-check.js`: Codex's apply_patch payload does NOT carry Claude's `tool_input.content`. Make the **disk-read the PRIMARY path** (read the edited file from disk), and pull the edited file path from Codex's apply_patch payload shape (verify field name). `process.exit(2)` blocking stays valid.
- `scripts/hooks/email-send-guard.js`: PreToolUse Bash payload — confirm it reads `data.tool_input.command` (Codex Bash payload). Likely 1:1. `exit(2)` block stays valid. Caveat: Codex "doesn't intercept all shell calls yet, only the simple ones" -> guard is best-effort.
- `${CLAUDE_PLUGIN_ROOT}` in hook commands: **works unchanged** (Codex sets CLAUDE_PLUGIN_ROOT/CLAUDE_PLUGIN_DATA compatibility aliases).

### 4. Clean the Claude-specific preamble inside the TOML bodies
Each `developer_instructions` still opens with the Claude-era "**Tool access — you run as a `general-purpose` subagent … call `ToolSearch` with `select:<ToolName>`**" note (the #21318 workaround). On Codex native agents this is wrong/irrelevant. Strip that opening paragraph from each `.codex/agents/*.toml` (or replace with a short "you are a Codex subagent; your tools are available directly" line). Do the same for any in-body reference to "general-purpose + embed" dispatch.

### 5. `reputation-scanner.toml` needs an `[mcp_servers]` block
It calls `mcp__apidirect__search_reddit` / `search_twitter`. Declare the apidirect server inside that agent's TOML (verify the per-agent `mcp_servers` TOML syntax) so the subagent can reach those tools. Fill `.mcp.json` with the real apidirect launch command.

### 6. Docs + cleanup
- `CLAUDE.md` -> rename to **`AGENTS.md`** (Codex's durable-repo-rules file); adjust wording from "Claude Code plugin" to "Codex plugin".
- Delete: `.claude-plugin/`, `commands/`, and the now-duplicated `skills/*/agents/*.md` (their content lives in `.codex/agents/*.toml`).
- `README.md`: retarget install instructions to `codex plugin marketplace add …` and the Codex structure.

---

## ⚠️ TWO THINGS TO VERIFY ON FIRST CODEX RUN (the real unknowns)

1. **Inter-round autonomy (blocker #1)** — does the Codex parent, given ONE skill invocation, autonomously spawn all pipeline stages in sequence WITHOUT stopping to ask you between stages? Docs are contradictory. **Run in a full-auto / auto-approve mode** (this removes the documented "needs fresh approval -> halts" failure). Test with C first. If it stalls between stages, the fallback is a single mega-skill that runs all stages inline in one context (a core change we deliberately deferred).
2. **Plugin-bundled subagents registration** — Codex's `plugin.json` has no `agents` field; `.codex/agents/*.toml` is documented as project/personal scope. Confirm that installing this plugin makes its bundled `.codex/agents/*.toml` visible to the skill's spawn calls. If NOT auto-registered, either (a) ship the TOMLs as project-level `.codex/agents/` the user drops in, or (b) have each SKILL spawn ad-hoc agents with the instructions inlined from the TOML. **The TOML content is written once either way — not wasted.**

Plus: confirm the exact **model id** (`gpt-5-codex` vs other current id) and the **`model_reasoning_effort` enum** (`low|medium|high` vs including `minimal|xhigh`) against your Codex version, and bulk-fix the 10 TOMLs if needed.
