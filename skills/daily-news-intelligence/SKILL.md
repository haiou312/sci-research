---
name: daily-news-intelligence
description: "Generate a dated single-country daily news briefing (daily news, news intelligence, daily briefing, country news report, 每日新闻, 每日情报, デイリーニュース). Five-stage category-parallel capped Scanner → deduplication-and-selection Verifier → Fact Extractor → Writer → Editor pipeline: Google News MCP discovery and article retrieval, target-language Markdown, final fact/style checks, and optional docx/email delivery. Supports scheduled/automated execution."
---

# Daily News Intelligence (Single Country)

Generate a professional dated daily report for institutional readers covering a single country or region. Designed for both interactive and **scheduled/automated** execution. Scanner and Verifier output is English, but search may use any language that improves discovery; the final report is written in the requested target language.

## Flow

Run exact custom agents with `fork_turns="none"`:

`Scanner × category → Verifier → Fact Extractor → Writer × language → Editor × language → pandoc → optional email`

- Scanner uses `google_news.search_news` only, makes at most two calls, favors distinct events, and returns up to 10 results per category. Ten is not a quota.
- Verifier uses no web, deduplicates, and keeps 3-6 events per category. The default minimum is 3; the fixed maximum is 6.
- Writer and Editor use `google_news.search_news` and `google_news.get_news_article`. Bilingual Writer and Editor stages run in parallel by language.
- Preserve usable content. Normalize partial Scanner output, use documented Verifier/Manifest fallbacks, and treat format defects as warnings. Stop only when no content or required infrastructure exists.
- China uses foreign media only. Europe means Europe-ex-UK; UK outlets may report eligible non-UK news.

## Input Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `country` | Yes | — | Single country or region, e.g. `United Kingdom`, `Europe`, `Japan`, `China`, `Germany`. `Europe` uses the Europe-ex-UK scope defined in `references/rubric.md`. |
| `date` | No | today | Target publication date in ISO `YYYY-MM-DD` |
| `lang` | No | `zh` | Output language for the final report. Single: `zh` / `en` / `ja`. **Bilingual (1.18.0+)**: any two of `zh / en / ja` joined by `+` (`zh+en`, `en+zh`, `zh+ja`, `ja+zh`, `en+ja`, `ja+en`). The first token is the **primary language** (drives email subject + body lead section). 3-language combos are not supported in 1.18.0. |
| `out_dir` | No | `~/.sci-research/reports/daily-news/{date}/` | Output directory. `{date}` is replaced with the ISO date and `~` is expanded at runtime. |
| `min_per_category` | No | `3` | Desired minimum retained-event count per category; integer `1-6`. When fewer than this many unique qualifying events exist, retain all available events and show a category gap note; never add filler. The fixed final maximum is 6 per category. |
| `email` | No | empty | Comma-separated recipient email addresses. When non-empty, Step 8 sends the report. |
| `email_subject` | No | auto | Email subject line. Default is `{country_display} {title_label} — {date_display}` in `lang`. |
| `email_body` | No | auto | Plain-text email body. Default template in `references/email-spec.md` filled with Verifier coverage counts. |
| `email_attach` | No | `both` | Attachment selection: `both` (md + docx), `docx`, `md`, or `none`. |
| `email_dry_run` | No | `false` | When `true`, Step 8 previews without connecting to SMTP. |

Derived fields (`date_en`, `date_display`, `country_display`, `out_md`, `out_docx`) are computed per `lang` — see `references/language-spec.md`. **Bilingual mode (1.18.0+)** computes one set per token in `langs = lang.split('+')` — i.e. `out_md_zh` + `out_md_en`, `country_display_zh` + `country_display_en`, etc. See `references/language-spec.md` § Bilingual Mode.

Email credentials and delivery rules are in `references/email-spec.md`.

## Runtime Paths

Before running the workflow, set `SKILL_DIR` to the absolute directory containing this `SKILL.md`, then derive the plugin root once:

```bash
SKILL_DIR=<absolute path to skills/daily-news-intelligence>
PLUGIN_ROOT="$(cd "$SKILL_DIR/../.." && pwd)"
RUNTIME_SYNC="$PLUGIN_ROOT/skills/setup-sci-research-runtime/scripts/sync_runtime.py"
```

Use these absolute paths for every bundled script. Do not rely on the current working directory or on Claude-specific environment variables. Before Step 1, run `python3 "$RUNTIME_SYNC" --project-root "$PWD" --check`. If it fails, stop and tell the user to run `$sci-research:setup-sci-research-runtime` in this workspace, then start a new Codex task.

Pipeline C requires a globally configured MCP server named `google_news` and a newly started task that exposes both `mcp__google_news__search_news` and `mcp__google_news__get_news_article`. Before Step 1, inspect the current task's available tools. If either tool is absent, stop and report: "google_news MCP is configured but not loaded in this task; verify `codex mcp get google_news`, then start a new Codex task." Do not fall back to Codex native WebSearch. The project-scoped `web_search = "live"` setting remains a plugin-wide runtime requirement for Pipelines E/F, but Pipeline C does not use it.

## Agent Dispatch

Use each exact installed `sci-research-*` role with `fork_turns="none"`; do not pass a model or substitute a generic agent. Start every prompt with:

```text
plugin_root: {PLUGIN_ROOT}
skill_root: {SKILL_DIR}
```

Pass the stage parameters and upstream artifact in the prompt. Persist or normalize the result, then close the child before starting the dependent stage. Close every child in a completed parallel group. If role selection or child closure is unavailable, report a runtime error.

Models come from TOML: Scanner and Verifier = `gpt-5.6-terra / high`; Fact Extractor = `gpt-5.6-luna / medium`; Writer and Editor = `gpt-5.6-sol / high`.

Launch one Scanner per active category in parallel. After the path header, pass exactly one sentence:

- Default: `Use google_news.search_news for news published on {date} about {country} for category {category}: {category_direction}`
- China: `Use google_news.search_news on foreign media only for news published on {date} about China for category {category}: {category_direction}`
- Europe: `Use google_news.search_news for news published on {date} about Europe for category {category}, excluding results focused primarily or solely on the United Kingdom: {category_direction}`

Pass downstream artifacts verbatim except for the explicit Scanner, Verifier, and Manifest fallbacks in Workflow.

## Workflow

1. **Resolve parameters.** Default `date` to today. Accept one or two distinct languages from `zh`, `en`, and `ja`. Require `1 <= min_per_category <= 6`; default to 3.

   Set `geography_scope` to `Europe-ex-UK` only for Europe. Set `active_categories` to `econ, politics, tech, society, ipo_ma, other`; insert `china_nexus` before `ipo_ma` only for China.

   Derive localized names, dates, and output paths for each language from `references/language-spec.md`. Print one `DERIVED[lang]` line with `country_display`, `date_display`, `out_md`, and `out_docx`.

   Pass only the matching one-line direction to each Scanner:

   | Category | `category_direction` |
   |---|---|
   | `econ` | Economy, finance, markets, trade, and business involving the target country. |
   | `politics` | Government, policy, law, diplomacy, and politics involving the target country. |
   | `tech` | Technology, AI, industry, telecoms, and innovation involving the target country. |
   | `society` | Employment, education, health, environment, population, and society involving the target country. |
   | `china_nexus` | Foreign-media coverage of China's economic, financial, trade, investment, and global business activity. |
   | `ipo_ma` | IPOs, listings, mergers, acquisitions, takeovers, and equity transactions involving the target country. |
   | `other` | Material target-country news not broadly covered by the preceding categories. |

   Expand `~` and substitute `{date}` in `out_dir`:
   ```bash
   OUT_DIR="${out_dir/#\~/$HOME}"
   OUT_DIR="${OUT_DIR//\{date\}/$DATE}"
   ```
   Use `OUT_DIR` (expanded) in all subsequent bash commands. The default resolves to e.g. `~/.sci-research/reports/daily-news/2026-04-16/`.

   Derive `country_slug` once from normalized English `country` (lowercase ASCII, spaces and punctuation collapsed to `-`). Then set:

   ```bash
   AUDIT_DIR="$OUT_DIR/audit"
   SCANNER_AUDIT="$AUDIT_DIR/scanner-bundle-${country_slug}-${DATE}.txt"
   VERIFIER_AUDIT="$AUDIT_DIR/verifier-report-${country_slug}-${DATE}.txt"
   mkdir -p "$AUDIT_DIR"
   ```

   Keep audits as `.txt`. Stop only if the directory cannot be created. Delete stale audits for this country/date with `apply_patch` before scanning.

2. **Scan.** Launch one `sci-research-daily-news-scanner` per active category in parallel with the exact one-sentence prompt above.

   Normalize each result per `references/schemas.md`: preserve parseable stories, cap at 10, repair IDs/counts, and use `Not shown` for missing fields. A failed or empty Scanner becomes an `unavailable` zero-candidate block. Do not retry or stop for schema, URL, access, or quality problems.

   Assemble the Scanner Batch in category order, save it to `SCANNER_AUDIT` with `apply_patch`, then close all Scanner children. Stop only if the whole Batch has zero candidates.

3. **Verify.** Spawn `sci-research-news-verifier` with the Scanner Batch, `country`, `geography_scope`, `min_per_category`, and `max_per_category=6`.

   Save usable output to `VERIFIER_AUDIT`. Otherwise create `Mode: mechanical-fallback` exactly as defined in `references/schemas.md`. Never retry or stop for Verifier schema defects. Close the Verifier.

4. **Extract facts.** Spawn `sci-research-daily-fact-extractor` with the Verifier output, `country`, `date`, `lang`, and `${OUT_DIR}/fact-manifest-{country_slug}-{date}.yaml`.

   If the Manifest is missing or malformed, create an `evidence_basis: search-results` fallback with one entry per KEEP story and empty `hard_facts`/`quotes`. Close the Fact Extractor.

5. **Write.** Create `OUT_DIR`. Spawn one `sci-research-daily-news-writer` per language in parallel. Pass the Verifier output, Manifest, `country`, `date`, one `lang` token, `min_per_category`, and that language's `out_md` path.

   The Writer owns research and output rules through `references/language-spec.md`, `references/output-spec.md`, and `references/verification.md`.

   Close all Writers and keep every readable Markdown file. A missing language never blocks another.

6. **Edit.** For each readable Markdown file, spawn one `sci-research-daily-editor` in parallel with `writer_md_path`, `manifest_path`, Verifier output, `lang`, `date`, and `country`. Close all Editors. An Editor failure leaves the Writer Markdown available for export.

7. **Export.** Run the advisory format check for each Markdown file:
   ```bash
   FORMAT_CHECK="$PLUGIN_ROOT/scripts/hooks/daily-news-format-check.js"
   for L in "${LANGS[@]}"; do
     MD_PATH="$(eval echo "\$out_md_$L")"
     if ! node "$FORMAT_CHECK" --file "$MD_PATH"; then
       echo "FORMAT_WARNING[$L]: exporting best-effort Markdown despite reported format issues" >&2
     fi
   done

   command -v pandoc >/dev/null 2>&1
   ```
   A non-zero check records `FORMAT_WARNING` but does not block export. If pandoc is absent, keep Markdown and report that docx was skipped. Otherwise export each language:
   ```bash
   for L in "${LANGS[@]}"; do
     MD_BASENAME="$(basename "$(eval echo \"\$out_md_$L\")")"
     DOCX_BASENAME="$(basename "$(eval echo \"\$out_docx_$L\")")"
     cd "$OUT_DIR" && pandoc --extract-media=./media "$MD_BASENAME" -o "$DOCX_BASENAME"
   done
   ```
   Report per-language pandoc failures; never delete Markdown or block another language.

8. **Email (optional).** Build subject, body, and attachments per `references/email-spec.md`, then invoke only the sanctioned sender:
    ```bash
    python3 "$PLUGIN_ROOT/scripts/send-report-email.py" \
      --to "{email}" \
      --subject "{email_subject}" \
      --body-file "{tmp_body_file}" \
      {optional --attach paths} \
      [--dry-run if email_dry_run=true]
    ```
    Omit `--attach` for body-only email. Never use inline SMTP. Report send failures without modifying local outputs.

9. **Verify.** Apply `references/verification.md` § End-to-End Verification.

## Degradation

Report every degradation and preserve usable output.

| Condition | Continue as |
|---|---|
| One Scanner is weak or fails | Normalize it or insert an `unavailable` block. |
| All Scanner categories are empty | Stop: there is no content. |
| Verifier is unusable | Use `mechanical-fallback`. |
| Fact Manifest is unusable | Use the empty-facts fallback. |
| One language or Editor fails | Continue every readable Markdown output. |
| Format or pandoc fails | Keep Markdown; warn and continue. |
| Email fails | Report it; keep local files unchanged. |
| Required role/tool is absent, child closure fails, or output path is unwritable | Stop the affected run. |

## References

| File | Contents | Consumed by |
|------|----------|-------------|
| `references/schemas.md` | Category Scanner Output Schema, mechanical Scanner Batch Schema, Verifier Output Schema | Scanner, Orchestrator, Verifier |
| `references/rubric.md` | Search and geography scope | Scanner, Orchestrator |
| `references/output-spec.md` | Markdown structure and references | Writer |
| `references/language-spec.md` | Localization, filenames, length, and style | Writer, Editor |
| `references/verification.md` | Writer self-check and delivery verification | Writer, Orchestrator |
| `references/email-spec.md` | Subject, body, credentials, attachments, and exit codes | Orchestrator when `email` is set |

## Invocation Examples

```
$sci-research:daily-news-intelligence --country "Japan" --date 2026-04-14 --lang zh
$sci-research:daily-news-intelligence --country "China"
$sci-research:daily-news-intelligence --country "Japan" --lang zh+en --email "you@gmail.com" --email-dry-run
```
