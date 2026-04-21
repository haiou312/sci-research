---
name: reputation-track
description: "Monitor reputational risk for a company across news and social media. Given a company name or stock ticker + optional date, the skill resolves the entity and executive list, scans News + Reddit + X (Twitter), classifies negative items by category and severity, and — only if negative findings exist — renders an HTML email body and delivers via Gmail SMTP. Silent exit when nothing negative is found. Use when: 'reputation track', 'reputation monitor', 'adverse monitoring', 'company risk scan', '声誉监控', '声誉追踪', 'レピュテーション'."
origin: sci-research-plugin
---

# Reputation Track (Single Company)

Scans News + Reddit + X for adverse content about a single company and its top executives, classifies severity, and sends an HTML email only when negative items are found. Silent when clean.

## Quick Reference (Orchestrator Checklist)

```
1. Validate params → compute derived fields → expand ~ → mkdir
2. Launch Resolver agent → capture Resolver Output Schema
3. IF resolution_confidence=low → STOP with clarification message
4. Launch 3 Scanner agents IN PARALLEL (news, reddit, x) → capture 3 Scanner outputs
5. Launch Classifier agent (all 3 Scanner outputs in prompt) → capture Classifier Output Schema
6. IF total_items_kept == 0 → print "Clean scan" and EXIT 0 (no email, no HTML file)
7. Launch Writer agent (Classifier kept_items + params) → Writer calls Write on out_html
8. IF --email → invoke send-report-email.py with --body-html-file
9. Print summary (items kept, severity breakdown, email status)
```

## Operating Principle

- **Silent when clean.** No email on a clean scan. Log line only. Prevents recipient fatigue.
- **Verbatim or drop.** Every surfaced item is backed by a verbatim quote from the source URL. No paraphrase, no synthesis.
- **Noise protection over recall.** Low-credibility claims without corroboration are dropped, not downgraded. Missing a marginal signal is preferable to crying wolf.
- **Honest coverage disclosure.** The HTML footer states which platforms were scanned and which (Facebook, Threads) were excluded.

## Input Parameters

| Parameter | Required | Default | Description |
|---|---|---|---|
| `company` | Yes | — | Company official name OR stock ticker (e.g. `Apple Inc.`, `AAPL`, `005930.KS`) |
| `date` | No | today | Target date ISO `YYYY-MM-DD` |
| `lang` | No | `zh` | HTML output language: `zh` or `en` |
| `sources` | No | `news,reddit,x` | Comma-separated subset. MVP only supports these three |
| `severity_min` | No | `medium` | Drop items below this severity: `low` \| `medium` \| `high` |
| `out_dir` | No | `~/Desktop/reputation-reports/{date}/` | Output directory. `{date}` is replaced with the ISO date. `~` is expanded at runtime. Auto-created in Step 1. |
| `email` | No | empty | Comma-separated recipient email addresses. When non-empty and `total_items_kept > 0`, Step 8 emails the HTML body via Gmail SMTP. |
| `email_subject` | No | auto | Email subject line override. Default: see `references/email-spec.md`. |
| `email_dry_run` | No | `false` | When `true`, Step 8 prints a preview and exits without connecting to SMTP. |

Email delivery reads Gmail SMTP credentials from the same environment variables as Pipelines C and D (`GOOGLE_EMAIL_USERNAME`, `GOOGLE_EMAIL_APP_PASSWORD`, etc.). See `.env.example` at the repo root and `references/email-spec.md`.

## Derived Fields (computed in Step 1)

- `date_display` — date in `lang`, e.g. `2026年4月21日` for zh, `April 21, 2026` for en
- `company_display` — from Resolver's `official_name` (not available until after Step 2; Step 1 uses the raw `--company` as a placeholder for path construction, then updates after Step 2)
- `out_html` = `{out_dir}{safe_slug(company_display)}-reputation-{date}.html`
  - `safe_slug(...)`: keep CJK characters intact; replace spaces and slashes with `-`; lowercase ASCII letters; strip punctuation except `-._`
  - Example: `Apple Inc.` → `apple-inc-reputation-2026-04-21.html`
  - Example: `腾讯控股` → `腾讯控股-reputation-2026-04-21.html`

**Required derivation print** (same pattern as Pipeline C Step 1 to prevent silent slug mistakes):

```
DERIVED: company_display=<value>  date_display=<value>  out_html=<absolute path>  sources=<comma list>  severity_min=<level>
```

Self-check: the `company_display` in `out_html` must be the Resolver's `official_name` (or its safe_slug form), **never** the raw `--company` input if that input was a ticker. If `lang=zh` and `company_display` is ASCII-only for a Chinese-listed company, regenerate.

## Data Handoff Between Stages

Each stage runs as a subagent. The orchestrator passes data via the subagent prompt text — not files, not environment variables.

- **Resolver → Scanner (×3)**: Include the full Resolver Output Schema verbatim in each Scanner prompt, along with `source`, `date`, `date_en`.
- **Scanner → Classifier**: Include all three Scanner Output Schemas verbatim, plus `severity_min` and the Resolver's `executives`.
- **Classifier → Writer**: Include only `kept_items` from the Classifier output, plus `company_display`, `date_display`, `lang`, `sources`, `out_html`.

## Workflow

1. **Validate scope.** Default `date` to today. Expand `~` and substitute `{date}` in `out_dir`:
   ```bash
   OUT_DIR="${out_dir/#\~/$HOME}"
   OUT_DIR="${OUT_DIR//\{date\}/$DATE}"
   mkdir -p "$OUT_DIR"
   ```

2. **Resolve entity.** Launch `reputation-resolver` with `--company` verbatim. Capture the Resolver Output Schema. Update `company_display = official_name` and recompute `out_html` with the canonical name.
   - If `resolution_confidence=low`, halt with: `Company resolution ambiguous: {resolution_notes}. Please clarify or pass the formal name / ticker explicitly.`

3. **Scan sources in parallel.** Launch three `reputation-scanner` instances in a **single orchestrator message** (three tool calls in parallel). Pass each instance its `source` (one of `news`, `reddit`, `x`) plus the Resolver output, `date`, `date_en`.
   - Respect `--sources` if the user narrowed the set (e.g. only `news,reddit`).

4. **Classify.** Launch `reputation-classifier` with all three Scanner Outputs verbatim + `severity_min` + Resolver's `executives`. Capture the Classifier Output Schema.

5. **Branch on findings.**
   - If `total_items_kept == 0`:
     - Print: `Clean scan: {company_display} / {date} — no negative findings at or above severity:{severity_min}. Sources scanned: {sources}.`
     - Exit 0. Do NOT write `out_html`. Do NOT call the email script.
   - Else: proceed to Step 6.

6. **Compose HTML.** Launch `reputation-writer` with Classifier `kept_items` + `company_display`, `date_display`, `lang`, `sources`, `out_html`. Writer calls `Write` on `out_html`.

7. **Verify HTML integrity** (orchestrator). Read the first 200 chars of `out_html`; confirm it starts with `<!DOCTYPE html>` and contains `{company_display}` in the header area. If malformed, re-invoke the Writer once, then halt with an error rather than sending a broken email.

8. **Send email** (only if `email` is non-empty). Compose subject per `references/email-spec.md`:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/send-report-email.py" \
     --to "$email" \
     --subject "$subject" \
     --body-html-file "$out_html" \
     ${email_dry_run:+--dry-run}
   ```
   Handle the script's non-zero exit codes per `references/email-spec.md` § Exit Code Handling. **Email failure must never delete `out_html`.**

9. **Print summary.**
   ```
   ✅ reputation-track complete
   company: {company_display} ({ticker})
   date: {date}
   items_kept: {N} ({critical=X, high=Y, medium=Z, low=W})
   sources: {news=A, reddit=B, x=C}
   out_html: {absolute path}
   email: sent|dry-run|skipped|error
   ```

## Stage → Agent → Reference Map

| Stage | Recommended Agent | Required References |
|---|---|---|
| Resolver | `sci-research:reputation-resolver` (opus) | `references/entity-resolution.md`, `references/schemas.md` |
| Scanner (×3 parallel) | `sci-research:reputation-scanner` (sonnet) | `references/source-matrix.md`, `references/schemas.md`, `rules/research/news-source.md` |
| Classifier | `sci-research:reputation-classifier` (sonnet) | `references/negativity-rubric.md`, `references/schemas.md` |
| Writer | `sci-research:reputation-writer` (opus) | `references/html-template.md`, `references/schemas.md` |
| Email (Step 8) | — (Bash + `scripts/send-report-email.py`) | `references/email-spec.md` |

## References

| File | Contents | Consumed by |
|---|---|---|
| `references/entity-resolution.md` | Ticker/name disambiguation, executive list sourcing, halt conditions | Resolver |
| `references/source-matrix.md` | Per-source search patterns, date verification methods, credibility signals | Scanner |
| `references/negativity-rubric.md` | Category taxonomy, severity levels, credibility weighting, hard rules | Classifier |
| `references/schemas.md` | Resolver / Scanner / Classifier output schemas | All agents |
| `references/html-template.md` | HTML skeleton, severity colors, localised labels, footer disclaimer | Writer |
| `references/email-spec.md` | Subject template, invocation, exit code handling | Orchestrator (Step 8 only when `email` is set) |

## Invocation Examples

```
/reputation-track --company "Apple Inc."
/reputation-track --company "AAPL" --date 2026-04-21
/reputation-track --company "Tesla" --lang en --severity-min high
/reputation-track --company "腾讯控股" --email you@gmail.com
/reputation-track --company "TSLA" --email "ceo@foo.com,risk@foo.com" --email-dry-run
/reputation-track --company "Meta" --sources news,reddit  # skip X for this run
```

## Design Limits (disclosed in the HTML footer)

- **X (Twitter)**: only Google-indexed public posts; long-tail user content not reached; 1-24h indexing lag
- **Facebook + Threads**: intentionally not covered in v1 — public-post discoverability via Google is too sparse to be trustworthy
- **Single-day window**: not a streaming monitor; misses content posted after the scan completes
- **English-source bias**: Scanner queries are primarily English; non-English regional press may be under-represented (v2 can add per-language source matrices)
- **"Negative" is a judgment call**: every flagged item includes a verbatim quote + URL so recipients can verify and disagree
