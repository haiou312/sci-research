---
name: daily-news-intelligence
description: "Generate a dated single-country daily news briefing (daily news, news intelligence, daily briefing, country news report, 每日新闻, 每日情报, デイリーニュース). Three-stage Scanner → Verifier → Writer pipeline: English WebSearch with per-URL date verification against T1-T4 sources, editorial second-pass filter, then target-language Markdown + docx report with APA 7th references. Supports scheduled/automated execution."
origin: sci-research-plugin
---

# Daily News Intelligence (Single Country)

Generate a professional dated daily report for institutional readers covering a single country or region. Designed for both interactive and **scheduled/automated** execution. Evidence collection is always performed in English against verified live web sources; the final report is translated into the requested target language at the end.

## Quick Reference (Orchestrator Checklist)

**Rule (every stage):** spawn as `general-purpose` + embedded `agents/<name>.md` body + explicit `model` arg (see § Subagent Dispatch Rule below).

**Pipeline flow** (high-level — Workflow below has the numbered procedure with bash commands):

- Validate params → expand `~` → compute derived fields (incl. `active_categories`)
- Fan out ONE Scanner per active category IN PARALLEL (6 or 7); each bundle may carry a `## Reserve Pool` (held conditional-accept-below-T2 + ipo_ma-soft-band)
- IF every bundle empty (main pool AND reserve pool) → STOP with message
- Merger (N bundles + `active_categories`) → unified Merged Bundle (Reserve Pool passed through, same dedup discipline)
- Verifier (Merged Bundle in prompt) → Three-Step Fallback (1 impact / 1.5 reserve-pool promote / 2 gap) → Verifier Output Schema
- Fact-Extractor (Verifier output + params) → fact-manifest YAML
- Writer (Verifier output + manifest path + params) → `Write` Markdown
- Editor (`writer_md` + manifest + `verifier_bundle` + lang/date/country) → in-place `Edit` across 5 passes (1 fact / 2 search-backing / 3 quote / 4 quote-mark / 5 local fluency)
- mkdir `-p` → pandoc export (skip if pandoc missing)
- IF `--email` → send via `scripts/send-report-email.py` (dry-run or real)
- Verify: `ls` both files, grep H2/H3 counts

## Operating Principle

Evidence priority order:

1. Articles whose publication date matches `date` exactly, verified by `web_fetch` on the canonical URL (primary truth).
2. `web_search` is only used to surface candidate URLs — never standalone evidence.
3. Model inference is permitted only when directly supported by the fetched article text.

Apply a three-stage filter before anything reaches the Writer:

- **Stage 1 (Scanner ×N, parallel)**: one Scanner per active category. Pass A (Source Matrix tier ladder) + Pass B (free discovery under § Source Legitimacy) + per-URL date verification. Each emits a single-category bundle tagged `Discovery: A|B` and `Source legitimacy:`. Active set = 6 categories for a non-China report, 7 for a China report (see `references/language-spec.md` § Category Catalog & Selection).
- **Stage 2 (Merger)**: cross-category dedup + `china_nexus`↔`ipo_ma` routing tie-break → one unified Merged Bundle. No quality judgement here.
- **Stage 3 (Verifier)**: originality + authority + impact + **source legitimacy** + dedup-validation, per the Authority & Impact Rubric and § Source Legitimacy.

Hard rules:

- Do not admit a candidate without passing the date-verification gate.
- Do not pad a category with low-tier sources to meet the minimum.
- Do not merge unrelated events into one synthetic story.
- Each Scanner sees only its one category; cross-category dedup and routing happen at the Merger, never at the Scanner.
- The Writer must read the Verifier's KEEP set, never the Scanner or Merged bundle directly.

## Input Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `country` | Yes | — | Single country or region, e.g. `United Kingdom`, `Japan`, `China`, `Germany` |
| `date` | No | today | Target publication date in ISO `YYYY-MM-DD` |
| `lang` | No | `zh` | Output language for the final report: `zh`, `en`, `ja` |
| `out_dir` | No | `~/Desktop/github/daily-news-reports/{date}/` | Output directory. `{date}` is replaced with the ISO date (e.g. `2026-04-16`). `~` is expanded at runtime. The directory is auto-created if missing (Workflow Step 8). Default writes directly into the GitHub Pages publishing repo so reports can be published with one `git push`. |
| `min_per_category` | No | `2` | Minimum stories per category |
| `email` | No | empty | Comma-separated recipient email addresses. When non-empty, Step 10 emails the report via Gmail SMTP. |
| `email_subject` | No | auto | Email subject line. Default is `{country_display} {title_label} — {date_display}` in `lang`. |
| `email_body` | No | auto | Plain-text email body. Default template in `references/email-spec.md` filled with Verifier coverage counts. |
| `email_attach` | No | `both` | Attachment selection: `both` (md + docx), `docx`, `md`, or `none`. |
| `email_dry_run` | No | `false` | When `true`, Step 10 prints a preview and exits without connecting to SMTP. |

Derived fields (`date_en`, `date_display`, `country_display`, `out_md`, `out_docx`) are computed per `lang` — see `references/language-spec.md`.

Email delivery reads Gmail SMTP credentials from environment variables (`GOOGLE_EMAIL_USERNAME`, `GOOGLE_EMAIL_APP_PASSWORD`, `GOOGLE_EMAIL_FROM_NAME`, `GOOGLE_EMAIL_HOST`, `GOOGLE_EMAIL_PORT`, `GOOGLE_EMAIL_START_TLS`). See `.env.example` at the repo root and `references/email-spec.md` for the full spec.

## Data Handoff Between Stages

### Subagent Dispatch Rule (READ FIRST — applies to every stage below)

Every stage spawns as the built-in **`general-purpose`** agent type with the agent body embedded as the prompt. For each stage the orchestrator MUST:

1. `Read` `${CLAUDE_PLUGIN_ROOT}/skills/daily-news-intelligence/agents/<name>.md`.
2. Strip the YAML frontmatter; use the **body** as the subagent's instruction prompt.
3. Append that stage's injected parameters + verbatim upstream data (per the handoff list below).
4. Spawn with `subagent_type: general-purpose` and an **explicit `model` argument** — `general-purpose` ignores frontmatter `model:`, so pass it yourself: **`sonnet`** for Scanner / Merger / Verifier / Fact-Extractor, **`opus`** for Writer / Editor.

Rationale (why we embed bodies rather than register `sci-research:*` subagents — anthropics/claude-code#21318 history, corroborated by #25200 / #52055 / #46250 / #31002): see `CLAUDE.md` § 项目定位 point 6.

The orchestrator passes data between stages via the subagent **prompt text** — not files, not environment variables. Specifically:

- **Orchestrator → Scanner ×N (fan-out, parallel)**: the orchestrator launches one Scanner subagent per active category in a single batch (parallel). Each Scanner prompt carries the **one** assigned `category` plus `country`, `date`, `min_per_category`. Each returns a single-category bundle (Scanner Output Schema from `references/schemas.md`).
- **Scanner ×N → Merger**: the orchestrator includes **all N single-category bundles verbatim** plus `country`, `date`, `lang`, and `active_categories` (the ordered list) in the Merger agent's prompt. The Merger returns one unified Merged Bundle (`references/schemas.md` § Merged Bundle).
- **Merger → Verifier**: the orchestrator includes the Merger's full Merged Bundle verbatim in the Verifier agent's prompt.
- **Verifier → Fact-Extractor**: The orchestrator includes the Verifier's full output verbatim plus runtime parameters (`country`, `date`, `lang`) and `out_manifest` (target YAML path, e.g. `${OUT_DIR}/fact-manifest-{country_slug}-{date}.yaml`) in the Fact-Extractor agent's prompt. The Fact-Extractor writes the manifest to `out_manifest` and returns confirmation.
- **Verifier + Fact-Extractor → Writer**: The orchestrator includes the Verifier's full output, the Fact Manifest content (read from `out_manifest`) or its absolute path, plus runtime parameters (`country`, `date`, `lang`, `out_md`, `min_per_category`) in the Writer agent's prompt.
- **Writer + Fact-Extractor + Verifier → Editor**: The orchestrator includes `writer_md_path` (the path Writer just wrote to), `manifest_path` (from Step 7.5), `verifier_bundle` (the same Verifier output passed verbatim, inline), plus runtime parameters (`lang`, `date`, `country`) in the Editor agent's prompt. The Editor makes in-place `Edit` calls on `writer_md_path` and prints a structured stdout report. The format-check hook fires on every Edit and on the final state.

The orchestrator must not summarise, truncate, or reformat the upstream output — pass it verbatim so downstream agents can parse the expected schema.

## Workflow

1. **Validate scope.** Normalize `country` for English search and target-language rendering. Default `date` to today (`date +%Y-%m-%d`). Build all derived fields per `references/language-spec.md`:
   - `date_en` — e.g. `April 16, 2026`
   - `date_display` — per `lang` (e.g. `2026年4月16日` for zh/ja)
   - `country_display` — country name in `lang` (e.g. `China`→`中国`/`中国`, `South Korea`→`韩国`/`韓国`, `Germany`→`德国`/`ドイツ`)
   - `active_categories` — the ordered category set for this report, per `references/language-spec.md` § Category Catalog & Selection: `[econ, politics, tech, society]` ++ (`country == China` ? `[china_nexus]` : `[]`) ++ `[ipo_ma, other]`. 6 categories for a non-China report, 7 for a China report. The H2 number is the 1-based position in this list.
   - `out_md` / `out_docx` — per filename pattern in `references/language-spec.md`

   **Active categories at a glance:**

   | Country | Active categories (ordered, by H2 position) | Count |
   |---------|----------------------------------------------|-------|
   | `China` | econ → politics → tech → society → **china_nexus** → ipo_ma → other | 7 |
   | (other) | econ → politics → tech → society → ipo_ma → other | 6 |

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
   Use `OUT_DIR` (expanded) in all subsequent bash commands. The default resolves to e.g. `~/Desktop/github/daily-news-reports/2026-04-16/`.

2. **Scan candidates** (Scanner stage, English only — FAN-OUT). Launch **one Scanner subagent per active category, all in parallel in a single batch** (6 for a non-China report, 7 for a China report). **Each Scanner is a `general-purpose` subagent with the `skills/daily-news-intelligence/agents/daily-news-scanner.md` body embedded and model `sonnet` passed explicitly — never `subagent_type: sci-research:daily-news-scanner` (see § Subagent Dispatch Rule).** Each Scanner prompt carries exactly **one** `category` plus `country`, `date`, `min_per_category`; it runs Pass A (Source Matrix ladder) + Pass B (free discovery per `references/rubric.md` § Source Legitimacy) and returns a single-category bundle. Query construction is **per-term, never `OR`-joined**: each Scanner builds queries from its category's **search-term set** in `skills/daily-news-intelligence/agents/daily-news-scanner.md` § Step 1 — the **single source of truth** (do not duplicate the term lists here; an earlier copy in this file drifted out of sync, hence the pointer). One `site:{domain} {country} "{term}" {date_en}` query per term, walking the tier ladder; the full term set runs at T4-official / T1-wire / T1-flagship **regardless of `min_per_category`** (that floor only gates T2/T3 descent).

   Rows run in `active_categories` order. **Per-category specifics:**
   - **Corporate IPO & M&A** — runs in every report; country-anchored. Primary-filing queries (SEC EDGAR / LSE RNS / exchange disclosure) and T3 Finance & Trade/Legal verticals are **always-first-class** — run first regardless of `min_per_category`.
   - **China-Nexus** — runs **only in a China report**; **not** `{country}`-anchored (region-unbounded global topical sweep); leads with the external-T4 + global-wire sweep.

   Authoritative rules (eligibility, China-aid exclusion + key-industry carve-out, materiality floor, `china_nexus`↔`ipo_ma` routing) live in `references/rubric.md` § Conditional & Topical Categories.

Collectively the Scanners gather 20-30 candidate URLs across the active category set (each owns its one category; breadth over depth). If **every** category bundle is empty, stop and report: "No news candidates found for {country} on {date}. The date may be a future date, a holiday, or WebSearch may be temporarily unavailable." Do not proceed to the Merger.

3. **Verify each candidate.** For every candidate URL, call `web_fetch` and extract the publication date. Apply the rules in `references/rubric.md` § Date Verification Rules — keep only stories where publication date equals `date` (local or UTC match).

4. **Apply tier filter.** Keep only T1-T4 sources per `references/rubric.md` § Source Tier Rules.

5. **Enforce category coverage.** If any category has fewer than `min_per_category`, run a second search pass scoped to that category. If still insufficient, record the gap — do not substitute low-tier sources.

6. **Compose the per-category Scanner outputs.** Each Scanner agent returns one single-category English bundle matching `references/schemas.md` § Scanner Output Schema (single category), tagged `Discovery: A|B` and `Source legitimacy:`. The orchestrator captures all N bundles.

6.5. **Merge & route** (Merger stage). Spawn per § Subagent Dispatch Rule (`general-purpose` + `skills/daily-news-intelligence/agents/daily-news-merger.md` body, model `sonnet`) with all N single-category bundles verbatim plus `country`, `date`, `lang`, `active_categories`. It performs cross-category deduplication, the `china_nexus`↔`ipo_ma` routing tie-break, AND carries the pooled `## Reserve Pool` through (same dedup discipline — no quality judgement), emitting one unified Merged Bundle (`references/schemas.md` § Merged Bundle). The orchestrator captures it for the Verifier.

7. **Quality filter** (Verifier stage). Spawn per § Subagent Dispatch Rule (`general-purpose` + `skills/daily-news-intelligence/agents/news-verifier.md` body, model `sonnet`) with the **Merged Bundle** included verbatim in its prompt. The Verifier applies the five-check rubric in `references/rubric.md` (originality, authority, impact, **source legitimacy**, dedup-validation) plus § Source Legitimacy for Pass-B sources. Applies the **Three-Step Coverage Fallback** if any category drops below `min_per_category`: Fallback 1 relaxes impact tier (→ `Regional-structural`); Fallback 1.5 promotes from the Merged Bundle's `## Reserve Pool` (held `below-authority-cap` candidates become `T3-extended` Leads; held `below-ipo-ma-floor` soft-band deals become Leads at their real tier) — revalidating Source Legitimacy on every promotion, never relaxing date / China red-line / hard-paywall-Lead / originality; Fallback 2 records the gap. Emits the Verifier Output Schema from `references/schemas.md`. The orchestrator captures this output for the next two stages (Fact-Extractor and Writer).

7.5. **Extract Fact Manifest** (Fact-Extractor stage). Spawn per § Subagent Dispatch Rule (`general-purpose` + `skills/daily-news-intelligence/agents/daily-fact-extractor.md` body, model `sonnet`) with the Verifier's full output included verbatim in its prompt plus `country`, `date`, `lang`, and `out_manifest`. Resolve `out_manifest` to `${OUT_DIR}/fact-manifest-{country_slug}-{date}.yaml` where `{country_slug}` is the lowercase ASCII slug of `country` (e.g. `japan`, `united-kingdom`, `china`). The agent emits a YAML Fact Manifest — one entry per KEPT story listing every number, date, named person, institution, product, and direct quote in the Verifier's `factual_excerpt`, each anchored to its source URL with a verbatim excerpt (see `skills/daily-news-intelligence/agents/daily-fact-extractor.md` for the full schema). The Fact-Extractor calls `Write` once and returns confirmation. The orchestrator captures the manifest path for downstream stages (Writer in Step 8; Editor in the future Step 8.5).

8. **Translate and write the report** (Writer stage). Spawn per § Subagent Dispatch Rule (`general-purpose` + `skills/daily-news-intelligence/agents/daily-news-writer.md` body, model `opus`). Ensure the output directory exists:
   ```bash
   mkdir -p "$OUT_DIR"
   ```
   If `mkdir -p` fails (permissions, read-only filesystem), stop and report the error — do not silently write to a fallback location. The Verifier's KEEP set is the **spine of which stories run**. The Fact Manifest (Step 7.5) is the **locked-fact contract** — Verifier-sourced numbers / names / dates / quotes that Writer must not drift on. Writer **runs 1-3 supplemental `WebSearch` / `WebFetch` calls per story by default** to enrich body prose with background context — what came before, broader pattern, prior policy. **References = Verifier KEEP URLs ∪ {search URLs that supplied a fact in body}** — every search URL whose content backed a body fact MUST be cited with proper APA and continuous `[N]` (see `references/output-spec.md` § Cited Search URLs). Compose narrative in `lang` per `references/language-spec.md`. Structure is `### title → body → **References**` per story — **no `**摘要**` / `**Summary**` / `**要約**` / `**分析**` / `**Analysis**` markers anywhere**. **Quote marks follow `references/language-spec.md` § Canonical Quote Marks** (en ASCII `""` / zh curly `""` / ja corner `「」` — the format-check hook blocks Write on any non-canonical char). When `lang=zh`, also comply with `references/language-spec.md` § Language-Specific Rules (official titles, country prefixes, time anchors, terminology, foreign media naming). Produce Markdown obeying `references/output-spec.md`. Use the `Write` tool to overwrite `out_md`.

8.5. **Fact-check + local-fluency editor pass** (Editor stage). Spawn per § Subagent Dispatch Rule (`general-purpose` + `skills/daily-news-intelligence/agents/daily-editor.md` body, model `opus`) with `writer_md_path` (= `out_md`), `manifest_path` (from Step 7.5), `verifier_bundle` (the same Verifier output, inline), and runtime params `lang` / `date` / `country` in its prompt. The Editor patches the MD in place using `Edit` (never `Write`) across **five sequential passes**:

   | Pass | Purpose |
   |------|---------|
   | 1 | Verifier-locked fact verification (drift back to manifest values) |
   | 2 | Writer-search fact backing (may add new search URLs to References + renumber `[N]`) |
   | 3 | Quote verbatim check (degrade to indirect speech if source disagrees) |
   | 4 | Quote-mark normalization (canonical per `references/language-spec.md`) |
   | 5 | Local-fluency / logic-gap repair under closed five-class defect whitelist: `pass2-cut-gap` · `foreign-residue` · `inconsistent-name` · `filler-marker` · `awkward-connector` |

   **Budgets.** Pass 2 + Pass 3 combined ≤ 2 WebSearch + 4 WebFetch per story. Pass 5 is style-only (zero WebSearch / WebFetch) and is capped at **3 Edits / story** and **`2 × story_count` Edits / document**.

   **Pass 5 rollback.** Any Pass-5 Edit that violates its six invariants is reverted: manifest facts preserved · References byte-identical · paragraph count preserved · `### title` preserved · quote-mark pairs balanced · no prohibited marker introduced. On unrecoverable failure, Pass 5 aborts gracefully and the pipeline continues with Passes 1-4's changes only.

   **Reporting.** The Editor prints a structured stdout report (drift counts, refs added, claims cut / weakened, quote-mark fixes, per-class Pass-5 totals); the orchestrator logs it but does not gate on it. The format-check hook fires on every `Edit` and validates the post-edit state — if any Edit produces a malformed file, the hook blocks and the orchestrator surfaces the violation.

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

    **⚠️ Hard rule — sanctioned script only.** The orchestrator MUST invoke `scripts/send-report-email.py` via the Bash subprocess above. **Do NOT** implement email delivery inline by importing `smtplib`, `email.message`, `email.mime`, `MIMEMultipart`, `MIMEText`, `EmailMessage`, or by shelling out to `sendmail` / `mail -s`. Inline implementations invariably skip the dual `Content-Disposition` filename encoding (RFC 2047 `filename=` + RFC 2231 `filename*=`) the sanctioned script applies — without both forms, recipients on corporate Exchange / Outlook see attachments as `noname`. A PreToolUse hook (`scripts/hooks/email-send-guard.js`) rejects Bash commands matching these inline patterns. If the script exits non-zero (codes 1-9), halt and report per the exit-code table — do NOT fall back to an inline implementation.

11. **Verify delivery.** Apply the checks in `references/verification.md` § End-to-End Verification.

12. **Publish to GitHub Pages.** When the default `out_dir` is used, the report lands in `~/Desktop/github/daily-news-reports/{date}/` — the working tree of the publishing repo. Hand off to the sanctioned publish script which stages, commits, and pushes:
    ```bash
    bash "${PLUGIN_ROOT}/scripts/publish-reports.sh"
    ```
    where `PLUGIN_ROOT` is the sci-research plugin root (typically `~/Desktop/sci-research`).

    The script is idempotent — `nothing to publish` (exit 0) is fine. Push failures must be reported but **never** stop the run from being considered successful: the docx already exists on disk and the user can `git push` manually. The remote `update-index.yml` GitHub Actions workflow refreshes `index.json` server-side, so this skill never writes `index.json`.

    **Skip this step** when `out_dir` was overridden to a path that is not a git working tree (best-effort detection: missing `${OUT_DIR%/*}/.git` or its parent — climb up at most three levels looking for a `.git` directory before deciding to skip).

## Stage → Agent → Reference Map

| Stage | Recommended Agent | Required References |
|-------|-------------------|---------------------|
| Scanner ×N (Step 2, parallel — one per active category) | `general-purpose` + embed `skills/daily-news-intelligence/agents/daily-news-scanner.md` body, model `sonnet` (see § Subagent Dispatch Rule) | `references/rubric.md`, `references/schemas.md` |
| Merger (Step 6.5) | `general-purpose` + embed `skills/daily-news-intelligence/agents/daily-news-merger.md` body, model `sonnet` | `references/rubric.md` § Conditional & Topical Categories, `references/schemas.md` § Merged Bundle |
| Verifier (Step 7) | `general-purpose` + embed `skills/daily-news-intelligence/agents/news-verifier.md` body, model `sonnet` | `references/rubric.md`, `references/schemas.md` |
| Fact-Extractor (Step 7.5) | `general-purpose` + embed `skills/daily-news-intelligence/agents/daily-fact-extractor.md` body, model `sonnet` | (Verifier output only — agent prompt has full schema) |
| Writer | `general-purpose` + embed `skills/daily-news-intelligence/agents/daily-news-writer.md` body, model `opus` | `references/language-spec.md`, `references/output-spec.md`, `references/verification.md`, Fact Manifest from Step 7.5 |
| Editor (Step 8.5) | `general-purpose` + embed `skills/daily-news-intelligence/agents/daily-editor.md` body, model `opus` | Writer's MD, Fact Manifest, Verifier bundle (verbatim), `references/language-spec.md` § Canonical Quote Marks (Pass 4) + § Language Rules (Pass 5 foreign-residue / inconsistent-name detection) |
| Email sender (Step 10) | — (Bash + `scripts/send-report-email.py`) | `references/email-spec.md` |
| Orchestrator delivery check | — | `references/verification.md` |

See `references/verification.md` § Recommended Agent Assignment for substitution rules and caveats. **The § Subagent Dispatch Rule above overrides any `sci-research:*` agent name appearing in that section or elsewhere — execution is always `general-purpose` + embedded body.**

## Failure Modes

Scattered through the Workflow above; consolidated here for quick scanning. **None of these may silently swallow errors — always report what failed and why.**

| Condition | Handling |
|-----------|----------|
| All Scanner bundles empty (main + reserve) | STOP. Report: "No news candidates found for {country} on {date}. The date may be a future date, a holiday, or WebSearch may be temporarily unavailable." Do not proceed to Merger. |
| `mkdir -p "$OUT_DIR"` fails (permissions / read-only FS) | STOP. Report the OS error. Do not silently fall back to a different path. |
| Editor Pass 5 unrecoverable failure | Abort Pass 5 only. Pipeline continues with Passes 1-4's changes. Log it; do not gate the run. |
| `pandoc` not installed | Skip docx export. Markdown remains a valid output. Report: "pandoc not found — .docx export skipped." |
| `pandoc` exits non-zero | Report the error. Do NOT delete the Markdown file. |
| Email script exits non-zero (codes 1-9) | Halt and report per `references/email-spec.md` § Exit Code Handling. **Never** delete or modify the local `.md` / `.docx`. **Never** fall back to inline SMTP — the PreToolUse hook will reject it anyway. |
| `out_dir` is not a git working tree | Skip Step 12 (publish). Best-effort detection: walk up at most three levels looking for `.git`. |
| `git push` fails in Step 12 | Report but do not fail the run — the docx already exists on disk; the user can push manually. |

## References

| File | Contents | Consumed by |
|------|----------|-------------|
| `references/schemas.md` | Scanner Output Schema (single category), Merged Bundle Schema, Verifier Output Schema | Scanner ×N, Merger, Verifier |
| `references/rubric.md` | Source Tier Rules, Source Discovery Model (with Reserve Pool), Source Legitimacy Rubric, Authority & Impact Rubric, Three-Step Coverage Fallback (1 impact / 1.5 reserve-pool promote / 2 gap), Date Verification Rules, Category Coverage Rules, Conditional & Topical Categories (three-band ipo_ma materiality) | Scanner ×N, Merger, Verifier |
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
