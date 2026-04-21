---
name: daily-news-intelligence
description: "Generate a dated single-country daily news briefing (daily news, news intelligence, daily briefing, country news report, 每日新闻, 每日情报, デイリーニュース). Three-stage Scanner → Verifier → Writer pipeline: English WebSearch with per-URL date verification against T1-T4 sources, editorial second-pass filter, then target-language Markdown + docx report with APA 7th references. Supports scheduled/automated execution."
origin: sci-research-plugin
---

# Daily News Intelligence (Single Country)

Generate a professional dated daily report for institutional readers covering a single country or region. Designed for both interactive and **scheduled/automated** execution. Evidence collection is always performed in English against verified live web sources; the final report is translated into the requested target language at the end.

## Quick Reference (Orchestrator Checklist)

```
1. Validate params → compute derived fields → expand ~
2. Launch Scanner agent → capture Scanner Output Schema
3. IF zero candidates → STOP with message
4. Launch Verifier agent (Scanner output in prompt) → capture Verifier Output Schema
5. Launch Writer agent (Verifier output + params in prompt) → Writer calls Write tool
6. mkdir -p → pandoc export (skip if pandoc missing)
7. IF --email → send via Python script (dry-run or real)
8. Verify: ls both files, grep H2/H3 counts
```

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
| `out_dir` | No | `~/Desktop/daily-news-reports/{date}/` | Output directory. `{date}` is replaced with the ISO date (e.g. `2026-04-16`). `~` is expanded at runtime. The directory is auto-created if missing (Workflow Step 8). |
| `min_per_category` | No | `2` | Minimum stories per category |
| `email` | No | empty | Comma-separated recipient email addresses. When non-empty, Step 10 emails the report via Gmail SMTP. |
| `email_subject` | No | auto | Email subject line. Default is `{country_display} {title_label} — {date_display}` in `lang`. |
| `email_body` | No | auto | Plain-text email body. Default template in `references/email-spec.md` filled with Verifier coverage counts. |
| `email_attach` | No | `both` | Attachment selection: `both` (md + docx), `docx`, `md`, or `none`. |
| `email_dry_run` | No | `false` | When `true`, Step 10 prints a preview and exits without connecting to SMTP. |

Derived fields (`date_en`, `date_display`, `country_display`, `out_md`, `out_docx`) are computed per `lang` — see `references/language-spec.md`.

Email delivery reads Gmail SMTP credentials from environment variables (`GOOGLE_EMAIL_USERNAME`, `GOOGLE_EMAIL_APP_PASSWORD`, `GOOGLE_EMAIL_FROM_NAME`, `GOOGLE_EMAIL_HOST`, `GOOGLE_EMAIL_PORT`, `GOOGLE_EMAIL_START_TLS`). See `.env.example` at the repo root and `references/email-spec.md` for the full spec.

## Data Handoff Between Stages

Each stage runs as a subagent. The orchestrator passes data between stages via the subagent **prompt text** — not files, not environment variables. Specifically:

- **Scanner → Verifier**: The orchestrator includes the Scanner's full output (Scanner Output Schema from `references/schemas.md`) verbatim in the Verifier agent's prompt.
- **Verifier → Writer**: The orchestrator includes the Verifier's full output (Verifier Output Schema) plus runtime parameters (`country`, `date`, `lang`, `out_md`, `min_per_category`) in the Writer agent's prompt.

The orchestrator must not summarise, truncate, or reformat the upstream output — pass it verbatim so downstream agents can parse the expected schema.

## Workflow

1. **Validate scope.** Normalize `country` for English search and target-language rendering. Default `date` to today (`date +%Y-%m-%d`). Build all derived fields per `references/language-spec.md`:
   - `date_en` — e.g. `April 16, 2026`
   - `date_display` — per `lang` (e.g. `2026年4月16日` for zh/ja)
   - `country_display` — country name in `lang` (e.g. `China`→`中国`/`中国`, `South Korea`→`韩国`/`韓国`, `Germany`→`德国`/`ドイツ`)
   - `out_md` / `out_docx` — per filename pattern in `references/language-spec.md`

   **Print the resolved values before Step 2.** Emit one visible line so the translation step cannot be silently skipped:
   ```
   DERIVED: country_display=<value>  date_display=<value>  out_md=<absolute path>  out_docx=<absolute path>
   ```
   Self-check: when `lang=zh` or `lang=ja`, the country segment of `out_md`/`out_docx` **must** be the translated `country_display`, not the raw `--country` input. If the filename contains only ASCII letters in the country segment for a non-English `lang` (e.g. `china-2026-04-21.md` for `lang=zh`), abort and regenerate — you skipped the translation.

   Expand `~` and substitute `{date}` in `out_dir`:
   ```bash
   OUT_DIR="${out_dir/#\~/$HOME}"
   OUT_DIR="${OUT_DIR//\{date\}/$DATE}"
   ```
   Use `OUT_DIR` (expanded) in all subsequent bash commands. The default resolves to e.g. `~/Desktop/daily-news-reports/2026-04-16/`.

2. **Scan candidates** (Scanner stage, English only). Generate at least three distinct query patterns per category using this template structure:

   | Category | Example queries (substitute `{country}` and `{date_en}`) |
   |----------|----------------------------------------------------------|
   | Economy | `{country} economy GDP trade {date_en}`, `{country} central bank interest rate {date_en}`, `{country} stock market {date_en}` |
   | Politics | `{country} politics legislation parliament {date_en}`, `{country} diplomacy foreign policy {date_en}`, `{country} election regulation {date_en}` |
   | Technology | `{country} technology AI semiconductor {date_en}`, `{country} tech industry startup {date_en}`, `{country} digital infrastructure {date_en}` |
   | Society | `{country} society health education {date_en}`, `{country} demographics labor {date_en}`, `{country} environment climate {date_en}` |
   | Other | `{country} news today {date_en}`, `{country} major events {date_en}`, `{country} breaking news {date_en}` |

   Collect 20-30 candidate URLs across the five fixed categories. Prioritise breadth over depth. If Scanner returns zero candidates across all categories, stop and report: "No news candidates found for {country} on {date}. The date may be a future date, a holiday, or WebSearch may be temporarily unavailable." Do not proceed to the Verifier.

3. **Verify each candidate.** For every candidate URL, call `web_fetch` and extract the publication date. Apply the rules in `references/rubric.md` § Date Verification Rules — keep only stories where publication date equals `date` (local or UTC match).

4. **Apply tier filter.** Keep only T1-T4 sources per `references/rubric.md` § Source Tier Rules.

5. **Enforce category coverage.** If any category has fewer than `min_per_category`, run a second search pass scoped to that category. If still insufficient, record the gap — do not substitute low-tier sources.

6. **Compose the Scanner output.** The Scanner agent returns a single English data bundle matching `references/schemas.md` § Scanner Output Schema. The orchestrator captures this output for the next step.

7. **Second-pass filter** (Verifier stage). Launch a Verifier agent with the Scanner's full output included verbatim in its prompt. The Verifier applies the four-check rubric in `references/rubric.md` § Authority & Impact Rubric (originality, authority, impact, dedup). Applies the two-step fallback if any category drops below `min_per_category`. Emits the Verifier Output Schema from `references/schemas.md`. The orchestrator captures this output for the Writer.

8. **Translate and write the report** (Writer stage). Ensure the output directory exists:
   ```bash
   mkdir -p "$OUT_DIR"
   ```
   If `mkdir -p` fails (permissions, read-only filesystem), stop and report the error — do not silently write to a fallback location. Consume the Verifier's KEEP set only. Translate narrative into `lang` per `references/language-spec.md`. **When `lang=zh`, the Writer must also comply with `references/language-spec.md` § Language-Specific Rules (quote marks `「」`, official titles, country prefixes, time anchors, terminology, foreign media naming).** Produce Markdown obeying `references/output-spec.md`. Use the `Write` tool to overwrite `out_md`.

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
| `references/language-spec.md` | Localisation Table, Derived Display Fields, Filename Pattern, Language Rules, Title Length Rules, Writing Standard, **Language-Specific Rules — `lang=zh` only** (quote marks, official titles, country prefixes, time anchors, terminology precision, foreign media naming) | Writer |
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
