---
name: daily-news-intelligence
description: Generate a dated single-country daily news briefing in the requested target language using a three-stage Scanner → Verifier → Writer pipeline. Scanner performs English WebSearch + per-URL WebFetch date verification against T1-T4 sources under five fixed categories. Verifier enforces a second-pass filter on originality, authority, impact, and dedup — keeping only influential wire-grade reporting. Writer compiles the final report in the target language with strict heading syntax and APA 7th references, then pandoc exports to .docx.
origin: sci-research-plugin
---

# Daily News Intelligence (Single Country)

Generate a professional dated daily report for institutional readers covering a single country or region. Evidence collection is always performed in English against verified live web sources; the final report is translated into the requested target language at the end.

## Operating Principle

Evidence priority order:

1. Articles whose publication date matches `date` exactly, verified by `web_fetch` on the canonical URL (primary truth).
2. `web_search` is only used to surface candidate URLs — never standalone evidence.
3. Model inference is permitted only when directly supported by the fetched article text.

Apply a two-pass filter before anything reaches the Writer:

- **Pass 1 (Scanner)**: date verification + T1-T4 tier filter + five-category coverage.
- **Pass 2 (Verifier)**: originality + authority + impact + dedup, per the Authority & Impact Rubric.

Hard rules:

- Do not admit a candidate without passing the date-verification gate.
- Do not pad a category with low-tier sources to meet the minimum.
- Do not merge unrelated events into one synthetic story.
- The Writer must read the Verifier's KEEP set, never the Scanner bundle directly.

## Input Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `country` | Yes | — | Single country or region, e.g. `United Kingdom`, `Japan`, `China`, `Germany` |
| `date` | No | today | Target publication date in ISO `YYYY-MM-DD` |
| `lang` | No | `zh` | Output language for the final report: `zh`, `en`, `ja` |
| `out_dir` | No | `~/Desktop/daily-news-reports/` | Output directory with trailing slash. `~` is expanded to the user's home directory at runtime. The directory is auto-created if missing (Workflow Step 8). |
| `min_per_category` | No | `2` | Minimum stories per category |
| `email` | No | empty | Comma-separated recipient email addresses. When non-empty, Step 10 emails the report via Gmail SMTP. |
| `email_subject` | No | auto | Email subject line. Default is `{country_display} {title_label} — {date_display}` in `lang`. |
| `email_body` | No | auto | Plain-text email body. Default template in `references/email-spec.md` filled with Verifier coverage counts. |
| `email_attach` | No | `both` | Attachment selection: `both` (md + docx), `docx`, `md`, or `none`. |
| `email_dry_run` | No | `false` | When `true`, Step 10 prints a preview and exits without connecting to SMTP. |

Derived fields (`date_en`, `date_display`, `country_display`, `out_md`, `out_docx`) are computed per `lang` — see `references/language-spec.md`.

Email delivery reads Gmail SMTP credentials from environment variables (`GOOGLE_EMAIL_USERNAME`, `GOOGLE_EMAIL_APP_PASSWORD`, `GOOGLE_EMAIL_FROM_NAME`, `GOOGLE_EMAIL_HOST`, `GOOGLE_EMAIL_PORT`, `GOOGLE_EMAIL_START_TLS`). See `.env.example` at the repo root and `references/email-spec.md` for the full spec.

## Workflow

1. **Validate scope.** Normalize `country` for English search and target-language rendering. Default `date` to today if omitted. Build all derived fields via `references/language-spec.md`. Expand `~` in `out_dir` immediately:
   ```bash
   OUT_DIR="${out_dir/#\~/$HOME}"
   ```
   Use `OUT_DIR` (expanded) in all subsequent bash commands.

2. **Scan candidates** (Scanner stage, English only). Generate at least three distinct query patterns per category. Collect 20-30 candidate URLs across the five fixed categories. Prioritise breadth over depth. If Scanner returns zero candidates across all categories, stop and report: "No news candidates found for {country} on {date}. The date may be a future date, a holiday, or WebSearch may be temporarily unavailable." Do not proceed to the Verifier.

3. **Verify each candidate.** For every candidate URL, call `web_fetch` and extract the publication date. Apply the rules in `references/rubric.md` § Date Verification Rules — keep only stories where publication date equals `date` (local or UTC match).

4. **Apply tier filter.** Keep only T1-T4 sources per `references/rubric.md` § Source Tier Rules.

5. **Enforce category coverage.** If any category has fewer than `min_per_category`, run a second search pass scoped to that category. If still insufficient, record the gap — do not substitute low-tier sources.

6. **Compose the Scanner output.** Return a single English data bundle matching `references/schemas.md` § Scanner Output Schema.

7. **Second-pass filter** (Verifier stage). Consume the Scanner bundle and apply the four-check rubric in `references/rubric.md` § Authority & Impact Rubric (originality, authority, impact, dedup). Apply the two-step fallback if any category drops below `min_per_category`. Emit the Verifier Output Schema from `references/schemas.md`.

8. **Translate and write the report** (Writer stage). Ensure the output directory exists:
   ```bash
   mkdir -p "$OUT_DIR"
   ```
   If `mkdir -p` fails (permissions, read-only filesystem), stop and report the error — do not silently write to a fallback location. Consume the Verifier's KEEP set only. Translate narrative into `lang` per `references/language-spec.md`. Produce Markdown obeying `references/output-spec.md`. Use the `Write` tool to overwrite `out_md`.

9. **Export to Word.** First verify pandoc is available:
   ```bash
   command -v pandoc >/dev/null 2>&1
   ```
   If pandoc is not installed, skip docx export and report: "pandoc not found — .docx export skipped. Install pandoc to enable Word export." The Markdown file is still valid output. If pandoc is available, run:
   ```bash
   cd "$OUT_DIR" && pandoc --extract-media=./media "$(basename "$out_md")" -o "$(basename "$out_docx")"
   ```
   If pandoc exits non-zero, report the error but do not delete the Markdown file.

10. **Send email** (optional — only if `email` parameter is non-empty). Build the subject and body per `references/email-spec.md`, write the body to a temp file, and invoke:
    ```bash
    python3 "${CLAUDE_PLUGIN_ROOT}/scripts/send-report-email.py" \
      --to "{email}" \
      --subject "{email_subject}" \
      --body-file "{tmp_body_file}" \
      --attach {attach_files} \
      [--dry-run if email_dry_run=true]
    ```
    Where `{attach_files}` depends on `email_attach` (`both` → both files, `docx` → only `.docx`, `md` → only `.md`, `none` → omit `--attach`). Handle the script's non-zero exit codes per `references/email-spec.md` § Exit Code Handling. **Email failure must never delete or modify the local `.md` or `.docx` files** — they were already delivered in Step 8-9.

11. **Verify delivery.** Apply the checks in `references/verification.md` § End-to-End Verification.

## Stage → Agent → Reference Map

| Stage | Recommended Agent | Required References |
|-------|-------------------|---------------------|
| Scanner | `sci-research:news-scanner` (sonnet) | `references/rubric.md`, `references/schemas.md` |
| Verifier | `sci-research:news-verifier` (sonnet) | `references/rubric.md`, `references/schemas.md` |
| Writer | `sci-research:daily-news-writer` (opus) | `references/language-spec.md`, `references/output-spec.md`, `references/verification.md` |
| Email sender (Step 10) | — (Bash + `scripts/send-report-email.py`) | `references/email-spec.md` |
| Orchestrator delivery check | — | `references/verification.md` |

See `references/verification.md` § Recommended Agent Assignment for substitution rules and caveats.

## References

| File | Contents | Consumed by |
|------|----------|-------------|
| `references/schemas.md` | Scanner Output Schema, Verifier Output Schema | Scanner, Verifier |
| `references/rubric.md` | Source Tier Rules, Authority & Impact Rubric, Two-Step Fallback, Date Verification Rules, Category Coverage Rules | Scanner, Verifier |
| `references/output-spec.md` | Required Markdown Output, Markdown Syntax Contract, Invalid + Valid examples (`lang=en`, `lang=zh`), APA 7th Reference Format | Writer |
| `references/language-spec.md` | Localisation Table, Derived Display Fields, Filename Pattern, Language Rules, Title Length Rules, Writing Standard | Writer |
| `references/verification.md` | Output Rules, Writer Self-Check, End-to-End Verification, Flow Diagram, Recommended Agent Assignment, Invocation Examples | Writer (self-check), Orchestrator (delivery check) |
| `references/email-spec.md` | Email subject / body templates, env var contract, attachment selection, exit-code handling, security | Orchestrator (Step 10 only when `email` is set) |

## Invocation Examples

```
/daily-news-intelligence --country "Japan" --date 2026-04-14 --lang zh
/daily-news-intelligence --country "United Kingdom" --date 2026-04-14 --lang en --min-per-category 3
/daily-news-intelligence --country "Germany" --lang ja
/daily-news-intelligence --country "China"

# With email delivery
/daily-news-intelligence --country "China" --email "you@gmail.com"
/daily-news-intelligence --country "Japan" --email "a@x.com,b@y.com" --email-attach docx
/daily-news-intelligence --country "UK" --lang en --email "you@gmail.com" --email-dry-run
```
