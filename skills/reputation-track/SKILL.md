---
name: reputation-track
description: "Monitor reputational risk for a company across news and social media. Given a company name or stock ticker + optional date, the skill resolves the entity and executive list, scans News + Reddit + X (Twitter), classifies negative items by category and severity, and — only if negative findings exist — renders an HTML email body and delivers via Gmail SMTP. Silent exit when nothing negative is found. Use when: 'reputation track', 'reputation monitor', 'adverse monitoring', 'company risk scan', '声誉监控', '声誉追踪', 'レピュテーション'."
---

# Reputation Track (Single Company)

Scans News + Reddit + X for adverse content about a single company and its top executives, classifies severity, and sends an HTML email only when negative items are found. Silent when clean.

## Quick Reference (Orchestrator Checklist)

```
1. Validate params → compute derived fields → expand ~ → mkdir
2. Launch Resolver agent → capture Resolver Output Schema
3. IF resolution_confidence=low → STOP with clarification message
4. Launch one Scanner agent per requested source IN PARALLEL → capture Scanner outputs
5. Launch Classifier agent (all requested-source outputs in prompt) → capture Classifier Output Schema
6. IF total_items_kept == 0 → EXIT 0 silently (no email, no HTML file)
7. Launch Writer agent (Classifier kept_items + params) → Writer creates or overwrites out_html with one `apply_patch` operation
8. IF --email → invoke send-report-email.py with --body-html-file
9. Print summary (items kept, severity breakdown, email status)
```

## Operating Principle

- **Silent when clean.** A clean scan emits no terminal output, writes no HTML, and sends no email. Do not relay upstream agent output or print a summary.
- **Verbatim or drop.** Every surfaced item is backed by a verbatim quote from the source URL. No paraphrase, no synthesis.
- **Noise protection over recall.** Low-credibility claims without corroboration are dropped, not downgraded. Missing a marginal signal is preferable to crying wolf.
- **Honest coverage disclosure.** The HTML footer states which platforms were scanned and which (Facebook, Threads) were excluded.
- **Search-indexed social coverage.** Reddit and X use WebSearch `search` for discovery and `open_page` for source/date verification; no API, MCP, direct scraper, or browser automation is used. Content that is not search-indexed, cannot be opened, or lacks a retrievable timestamp is recorded as a coverage gap rather than inferred.

## Input Parameters

| Parameter | Required | Default | Description |
|---|---|---|---|
| `company` | Yes | — | Company official name OR stock ticker (e.g. `Apple Inc.`, `AAPL`, `005930.KS`) |
| `date` | No | today | Target date ISO `YYYY-MM-DD` |
| `lang` | No | `zh` | HTML output language: `zh` or `en` |
| `sources` | No | `news,reddit,x` | Comma-separated subset. MVP only supports these three |
| `severity_min` | No | `medium` | Drop items below this severity: `low` \| `medium` \| `high` |
| `out_dir` | No | `~/.sci-research/reports/reputation/{date}/` | Output directory. `{date}` is replaced with the ISO date. `~` is expanded at runtime. Auto-created in Step 1. |
| `email` | No | empty | Comma-separated recipient email addresses. When non-empty and `total_items_kept > 0`, Step 8 emails the HTML body via Gmail SMTP. |
| `email_subject` | No | auto | Email subject line override. Default: see `references/email-spec.md`. |
| `email_dry_run` | No | `false` | When `true`, Step 8 prints a preview and exits without connecting to SMTP. |

Email delivery reads Gmail SMTP credentials from the same environment variables as Pipelines C and D (`GOOGLE_EMAIL_USERNAME`, `GOOGLE_EMAIL_APP_PASSWORD`, etc.). See `.env.example` at the repo root and `references/email-spec.md`.

## Runtime Paths

Before running the workflow, set `SKILL_DIR` to the absolute directory containing this `SKILL.md`, then derive the plugin root once:

```bash
SKILL_DIR=<absolute path to skills/reputation-track>
PLUGIN_ROOT="$(cd "$SKILL_DIR/../.." && pwd)"
RUNTIME_SYNC="$PLUGIN_ROOT/skills/setup-sci-research-runtime/scripts/sync_runtime.py"
```

Use these absolute paths for every bundled script. Do not rely on the current working directory or on Claude-specific environment variables. Before Step 1, run `python3 "$RUNTIME_SYNC" --project-root "$PWD" --check`. If it fails, stop and tell the user to run `$sci-research:setup-sci-research-runtime` in this workspace, then start a new Codex task.

## Derived Fields (computed in Step 1)

- `date_display` — date in `lang`, e.g. `2026年4月21日` for zh, `April 21, 2026` for en
- `company_display` — from Resolver's `official_name` (not available until after Step 2; Step 1 uses the raw `--company` as a placeholder for path construction, then updates after Step 2)
- `out_html` = `{out_dir}{safe_slug(company_display)}-reputation-{date}.html`
  - `safe_slug(...)`: keep CJK characters intact; replace spaces and slashes with `-`; lowercase ASCII letters; strip punctuation except `-._`
  - Example: `Apple Inc.` → `apple-inc-reputation-2026-04-21.html`
  - Example: `腾讯控股` → `腾讯控股-reputation-2026-04-21.html`

**Deferred derivation print** (same pattern as Pipeline C Step 1 to prevent silent slug mistakes):

```
DERIVED: company_display=<value>  date_display=<value>  out_html=<absolute path>  sources=<comma list>  severity_min=<level>
```

Do not emit this line before Step 5. If `total_items_kept == 0`, exit silently without printing it. Self-check: the `company_display` in `out_html` must be the Resolver's `official_name` (or its safe_slug form), **never** the raw `--company` input if that input was a ticker. If `lang=zh` and `company_display` is ASCII-only for a Chinese-listed company, regenerate.

## Data Handoff Between Stages

### Subagent Dispatch Rule (READ FIRST — applies to every stage below)

Every stage runs as a **native Codex custom agent** installed by `$sci-research:setup-sci-research-runtime`. For each stage the orchestrator MUST:

1. Select the exact role through the spawn tool's agent-type/role selector: `sci-research-reputation-resolver`, `sci-research-reputation-scanner`, `sci-research-reputation-classifier`, or `sci-research-reputation-writer`. `task_name` is only a thread label and MUST NOT be used as the role selector.
2. Set `fork_turns="none"`; do not pass model or reasoning overrides.
3. Start every spawn prompt with absolute `plugin_root: {PLUGIN_ROOT}` and `skill_root: {SKILL_DIR}`, then pass that stage's injected parameters + the verbatim upstream output.
4. Wait for the subagent's result, then feed it into the next stage.

If the active Codex surface exposes no custom-agent selector, rejects the role as unknown, or cannot start it with `fork_turns="none"`, halt. Do not fall back to a generic agent or embed the TOML instructions in the prompt.

Model tiering is set per-agent in the TOML: Resolver = `gpt-5.6-terra / high`; Scanner = `gpt-5.6-luna / medium`; Classifier = `gpt-5.6-terra / high`; Writer = `gpt-5.6-terra / medium`. Do NOT pass a model argument. Native Codex subagents receive their tools directly (no embed workaround).

The orchestrator passes data between stages via the subagent **prompt text** — not environment variables. Every prompt includes the runtime-path header above. Specifically:

- **Resolver → Scanner (× requested sources)**: Include the full Resolver Output Schema verbatim in each Scanner prompt, along with `source`, `date`, `date_en`.
- **Scanner → Classifier**: Include every requested-source Scanner Output Schema verbatim, plus `severity_min` and the Resolver's `executives`.
- **Classifier → Writer**: Include only `kept_items` from the Classifier output, plus `company_display`, `date_display`, `lang`, `sources`, `out_html`.

## Workflow

1. **Validate scope.** Default `date` to today. Expand `~` and substitute `{date}` in `out_dir`:
   ```bash
   OUT_DIR="${out_dir/#\~/$HOME}"
   OUT_DIR="${OUT_DIR//\{date\}/$DATE}"
   mkdir -p "$OUT_DIR"
   ```

2. **Resolve entity.** Spawn `sci-research-reputation-resolver` (`.codex/agents/sci-research-reputation-resolver.toml`) per § Subagent Dispatch Rule with `--company` verbatim. Capture the Resolver Output Schema. Update `company_display = official_name` and recompute `out_html` with the canonical name.
   - If `resolution_confidence=low`, halt with: `Company resolution ambiguous: {resolution_notes}. Please clarify or pass the formal name / ticker explicitly.`

3. **Scan sources in parallel.** Parse and validate `--sources` as a non-empty, de-duplicated subset of `news,reddit,x`. Launch one Scanner instance per requested source in a **single orchestrator message**. Pass each instance its `source` plus the Resolver output, `date`, `date_en`.

4. **Classify.** Spawn `sci-research-reputation-classifier` (`.codex/agents/sci-research-reputation-classifier.toml`) per § Subagent Dispatch Rule with one Scanner Output for every requested source, plus `severity_min` and the Resolver's `executives`. For sources excluded by `--sources`, do not spawn a Scanner and do not fabricate an empty output. Capture the Classifier Output Schema.

5. **Branch on findings.**
   - If `total_items_kept == 0`:
     - Exit 0 with **no terminal output**. Do NOT relay upstream output, write `out_html`, or call the email script.
   - Else: emit the deferred `DERIVED` line above, then proceed to Step 6.

6. **Compose HTML.** Spawn `sci-research-reputation-writer` (`.codex/agents/sci-research-reputation-writer.toml`) per § Subagent Dispatch Rule with Classifier `kept_items` + `company_display`, `date_display`, `lang`, `sources`, `out_html`. Writer uses one `apply_patch` operation to create or overwrite `out_html`.

7. **Verify HTML integrity** (orchestrator). Read the first 200 chars of `out_html`; confirm it starts with `<!DOCTYPE html>` and contains `{company_display}` in the header area. If malformed, re-invoke the Writer once, then halt with an error rather than sending a broken email.

8. **Send email** (only if `email` is non-empty). Compose subject per `references/email-spec.md`:
   ```bash
   python3 "$PLUGIN_ROOT/scripts/send-report-email.py" \
     --to "$email" \
     --subject "$subject" \
     --body-html-file "$out_html" \
     ${email_dry_run:+--dry-run}
   ```
   Handle the script's non-zero exit codes per `references/email-spec.md` § Exit Code Handling. **Email failure must never delete `out_html`.**

   **⚠️ Hard rule — sanctioned script only.** The orchestrator MUST invoke `scripts/send-report-email.py` via the Bash subprocess above. **Do NOT** implement email delivery inline using `smtplib`, `email.message`, `email.mime`, `MIMEMultipart`, `MIMEText`, `EmailMessage`, or by shelling out to `sendmail` / `mail -s`. For HTML-body sends, the sanctioned script automatically wraps the HTML as `multipart/alternative` with a text/plain fallback. A PreToolUse hook (`scripts/hooks/email-send-guard.js`) rejects Bash commands matching inline SMTP patterns. On non-zero script exit, halt and report — do NOT fall back to inline SMTP.

9. **Print summary.**
   ```
   ✅ reputation-track complete
   company: {company_display} ({ticker})
   date: {date}
   items_kept: {N} ({critical=X, high=Y, medium=Z, low=W})
   sources: {one count per requested source}
   out_html: {absolute path}
   email: sent|dry-run|skipped|error
   ```

## Stage → Agent → Reference Map

| Stage | Dispatch (see § Subagent Dispatch Rule) | Required References |
|---|---|---|
| Resolver | `sci-research-reputation-resolver` (`.codex/agents/sci-research-reputation-resolver.toml`) | `references/entity-resolution.md`, `references/schemas.md` |
| Scanner (× requested sources, parallel) | `sci-research-reputation-scanner` (`.codex/agents/sci-research-reputation-scanner.toml`) | `references/source-matrix.md`, `references/schemas.md`, `references/news-source.md` for `news` |
| Classifier | `sci-research-reputation-classifier` (`.codex/agents/sci-research-reputation-classifier.toml`) | `references/negativity-rubric.md`, `references/schemas.md` |
| Writer | `sci-research-reputation-writer` (`.codex/agents/sci-research-reputation-writer.toml`) | `references/html-template.md`, `references/schemas.md` |
| Email (Step 8) | — (Bash + `scripts/send-report-email.py`) | `references/email-spec.md` |

## References

| File | Contents | Consumed by |
|---|---|---|
| `references/entity-resolution.md` | Ticker/name disambiguation, executive list sourcing, halt conditions | Resolver |
| `references/source-matrix.md` | Per-source search patterns, date verification methods, credibility signals | Scanner |
| `references/news-source.md` | T1-T4 news-source hierarchy and exclusions | Scanner (`source=news`) |
| `references/negativity-rubric.md` | Category taxonomy, severity levels, credibility weighting, hard rules | Classifier |
| `references/schemas.md` | Resolver / Scanner / Classifier output schemas | All agents |
| `references/html-template.md` | HTML skeleton, severity colors, localised labels, footer disclaimer | Writer |
| `references/email-spec.md` | Subject template, invocation, exit code handling | Orchestrator (Step 8 only when `email` is set) |

## Invocation Examples

```
$sci-research:reputation-track --company "Apple Inc."
$sci-research:reputation-track --company "AAPL" --date 2026-04-21
$sci-research:reputation-track --company "Tesla" --lang en --severity-min high
$sci-research:reputation-track --company "腾讯控股" --email you@gmail.com
$sci-research:reputation-track --company "TSLA" --email "ceo@foo.com,risk@foo.com" --email-dry-run
$sci-research:reputation-track --company "Meta" --sources news,reddit  # skip X for this run
```

## Design Limits (disclosed in the HTML footer)

- **Reddit + X (Twitter)**: only public posts/threads that are search-indexed and openable; long-tail content is not reached, and search indexing can lag by 1-24 hours or more
- **Facebook + Threads**: intentionally not covered in v1 — public-post discoverability via Google is too sparse to be trustworthy
- **Single-day window**: not a streaming monitor; misses content posted after the scan completes
- **English-source bias**: Scanner queries are primarily English; non-English regional press may be under-represented (v2 can add per-language source matrices)
- **"Negative" is a judgment call**: every flagged item includes a verbatim quote + URL so recipients can verify and disagree
