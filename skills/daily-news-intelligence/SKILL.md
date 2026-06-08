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

- Validate params → parse `lang` as `langs = lang.split('+')` (single or bilingual) → expand `~` → compute derived fields per `lang` (incl. `active_categories`)
- Launch ONE Scanner with all active categories (6 or 7); it processes them sequentially (Pass A + Pass B per category), performs cross-category dedup + routing internally, and emits one unified Scanner Bundle (may carry a `## Reserve Pool`)
- IF Scanner Bundle empty (main pool AND reserve pool) → STOP with message
- Verifier (Scanner Bundle in prompt) → Three-Step Fallback (1 impact / 1.5 reserve-pool promote / 2 gap) → Verifier Output Schema
- Fact-Extractor (Verifier output + params) → fact-manifest YAML (single, language-agnostic — shared across bilingual halves)
- **FAN OUT per `lang` in `langs`**:
  - Writer (Verifier output + manifest path + that `lang`'s params) → `Write` Markdown to `out_md_{lang}`
  - Editor (`writer_md_{lang}` + manifest + `verifier_bundle` + lang/date/country) → in-place `Edit` across 5 passes (1 fact / 2 search-backing / 3 quote / 4 quote-mark / 5 local fluency)
  - pandoc export `out_md_{lang}` → `out_docx_{lang}` (skip if pandoc missing)
- IF `--email` → send via `scripts/send-report-email.py` (dry-run or real). Single-lang body + 1-2 attachments. **Bilingual body (stacked primary+secondary)** + 2-4 attachments per § email-spec.md.
- Verify: `ls` each generated `out_md_{lang}` / `out_docx_{lang}`, grep H2/H3 counts per file

## Operating Principle

Evidence priority order:

1. Articles whose publication date matches `date` exactly, verified by `web_fetch` on the canonical URL (primary truth).
2. `web_search` is only used to surface candidate URLs — never standalone evidence.
3. Model inference is permitted only when directly supported by the fetched article text.

Apply a two-stage filter before anything reaches the Writer:

- **Stage 1 (Scanner, single agent)**: one Scanner across all active categories sequentially. Pass A (Source Matrix tier ladder) + Pass B (free discovery under § Source Legitimacy) + per-URL date verification per category, then cross-category dedup + `china_nexus`↔`ipo_ma` routing. Emits one unified Scanner Bundle with `Discovery: A|B` and `Source legitimacy:` tags. Active set = 6 categories for a non-China report, 7 for a China report (see `references/language-spec.md` § Category Catalog & Selection).
- **Stage 2 (Verifier)**: originality + authority + impact + **source legitimacy** + dedup-validation, per the Authority & Impact Rubric and § Source Legitimacy.

Hard rules:

- Do not admit a candidate without passing the date-verification gate.
- Do not pad a category with low-tier sources to meet the minimum.
- Do not merge unrelated events into one synthetic story.
- Cross-category dedup and routing happen inside the Scanner (§ Step 6), before the Verifier.
- The Writer must read the Verifier's KEEP set, never the Scanner Bundle directly.

## Input Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `country` | Yes | — | Single country or region, e.g. `United Kingdom`, `Japan`, `China`, `Germany` |
| `date` | No | today | Target publication date in ISO `YYYY-MM-DD` |
| `lang` | No | `zh` | Output language for the final report. Single: `zh` / `en` / `ja`. **Bilingual (1.18.0+)**: any two of `zh / en / ja` joined by `+` (`zh+en`, `en+zh`, `zh+ja`, `ja+zh`, `en+ja`, `ja+en`). The first token is the **primary language** (drives email subject + body lead section). 3-language combos are not supported in 1.18.0. |
| `out_dir` | No | `~/Desktop/github/daily-news-reports/{date}/` | Output directory. `{date}` is replaced with the ISO date (e.g. `2026-04-16`). `~` is expanded at runtime. The directory is auto-created if missing (Workflow Step 8). Default writes directly into the GitHub Pages publishing repo so reports can be published with one `git push`. |
| `min_per_category` | No | `2` | Minimum stories per category |
| `email` | No | empty | Comma-separated recipient email addresses. When non-empty, Step 10 emails the report via Gmail SMTP. |
| `email_subject` | No | auto | Email subject line. Default is `{country_display} {title_label} — {date_display}` in `lang`. |
| `email_body` | No | auto | Plain-text email body. Default template in `references/email-spec.md` filled with Verifier coverage counts. |
| `email_attach` | No | `both` | Attachment selection: `both` (md + docx), `docx`, `md`, or `none`. |
| `email_dry_run` | No | `false` | When `true`, Step 10 prints a preview and exits without connecting to SMTP. |

Derived fields (`date_en`, `date_display`, `country_display`, `out_md`, `out_docx`) are computed per `lang` — see `references/language-spec.md`. **Bilingual mode (1.18.0+)** computes one set per token in `langs = lang.split('+')` — i.e. `out_md_zh` + `out_md_en`, `country_display_zh` + `country_display_en`, etc. See `references/language-spec.md` § Bilingual Mode.

Email delivery reads Gmail SMTP credentials from environment variables (`GOOGLE_EMAIL_USERNAME`, `GOOGLE_EMAIL_APP_PASSWORD`, `GOOGLE_EMAIL_FROM_NAME`, `GOOGLE_EMAIL_HOST`, `GOOGLE_EMAIL_PORT`, `GOOGLE_EMAIL_START_TLS`). See `.env.example` at the repo root and `references/email-spec.md` for the full spec.

## Data Handoff Between Stages

### Subagent Dispatch Rule (READ FIRST — applies to every stage below)

Every stage spawns as the built-in **`general-purpose`** agent type with the agent body embedded as the prompt. For each stage the orchestrator MUST:

1. `Read` `${CLAUDE_PLUGIN_ROOT}/skills/daily-news-intelligence/agents/<name>.md`.
2. Strip the YAML frontmatter; use the **body** as the subagent's instruction prompt.
3. Append that stage's injected parameters + verbatim upstream data (per the handoff list below).
4. Spawn with `subagent_type: general-purpose` and an **explicit `model` argument** — `general-purpose` ignores frontmatter `model:`, so pass it yourself: **`sonnet`** for Scanner / Verifier / Fact-Extractor, **`opus`** for Writer / Editor.

Rationale (why we embed bodies rather than register `sci-research:*` subagents — anthropics/claude-code#21318 history, corroborated by #25200 / #52055 / #46250 / #31002): see `CLAUDE.md` § 项目定位 point 6.

The orchestrator passes data between stages via the subagent **prompt text** — not files, not environment variables. Specifically:

- **Orchestrator → Scanner**: the orchestrator launches ONE Scanner subagent with **all** `active_categories` plus `country`, `date`, `min_per_category`. The Scanner processes all categories sequentially, performs cross-category dedup + routing internally, and returns a unified Scanner Bundle (`references/schemas.md` § Scanner Bundle Schema).
- **Scanner → Verifier**: the orchestrator includes the Scanner's full Scanner Bundle verbatim in the Verifier agent's prompt.
- **Verifier → Fact-Extractor**: The orchestrator includes the Verifier's full output verbatim plus runtime parameters (`country`, `date`, `lang`) and `out_manifest` (target YAML path, e.g. `${OUT_DIR}/fact-manifest-{country_slug}-{date}.yaml`) in the Fact-Extractor agent's prompt. The Fact-Extractor writes the manifest to `out_manifest` and returns confirmation.
- **Verifier + Fact-Extractor → Writer (per `lang` in `langs`)**: For each `lang` the orchestrator launches a separate Writer subagent with the same Verifier full output, the same Fact Manifest content (read from `out_manifest`) or its absolute path, plus that invocation's runtime parameters (`country`, `date`, that `lang`, `out_md_{lang}`, `min_per_category`). Single-lang: 1 Writer invocation. Bilingual: 2 parallel-or-sequential Writer invocations sharing the same Verifier/Manifest inputs.
- **Writer + Fact-Extractor + Verifier → Editor (per `lang` in `langs`)**: For each `lang` the orchestrator launches a separate Editor subagent with `writer_md_path` = `out_md_{lang}` (this lang's Writer output), `manifest_path` (single, from Step 7.5), `verifier_bundle` (same Verifier output passed verbatim, inline), plus that invocation's runtime parameters (that `lang`, `date`, `country`). Each Editor makes in-place `Edit` calls on its own `writer_md_path` and prints a structured stdout report. The format-check hook fires on every Edit and on the final state, per file.

The orchestrator must not summarise, truncate, or reformat the upstream output — pass it verbatim so downstream agents can parse the expected schema.

## Workflow

1. **Validate scope.** Normalize `country` for English search and target-language rendering. Default `date` to today (`date +%Y-%m-%d`). Parse `lang` into the list `langs = lang.split('+')` — single-lang has `len == 1`, bilingual (1.18.0+) has `len == 2`. Reject `len > 2` (3-language combos are not supported in 1.18.0). Set `primary_lang = langs[0]`, `secondary_lang = langs[1] if len(langs) > 1 else None`, `is_bilingual = len(langs) == 2`.

   Build all derived fields per `references/language-spec.md`:
   - `date_en` — e.g. `April 16, 2026` (singular, language-agnostic)
   - `active_categories` — the ordered category set for this report, per `references/language-spec.md` § Category Catalog & Selection: `[econ, politics, tech, society]` ++ (`country == China` ? `[china_nexus]` : `[]`) ++ `[ipo_ma, other]`. 6 categories for a non-China report, 7 for a China report. The H2 number is the 1-based position in this list. **Identical for both halves of a bilingual report** (single Verifier KEEP set → identical counts).

   **Per-lang derived fields** — compute one set per token in `langs` (single-lang has 1 set, bilingual has 2):
   - `date_display_{lang}` — per `lang` (e.g. `2026年4月16日` for zh/ja, `April 16, 2026` for en)
   - `country_display_{lang}` — country name in `{lang}` (e.g. `China`→`中国`/`中国`/`China`)
   - `out_md_{lang}` / `out_docx_{lang}` — per filename pattern in `references/language-spec.md`

   In single-lang mode, drop the `_{lang}` suffix for brevity — `out_md` ≡ `out_md_{primary_lang}`.

   **Active categories at a glance:**

   | Country | Active categories (ordered, by H2 position) | Count |
   |---------|----------------------------------------------|-------|
   | `China` | econ → politics → tech → society → **china_nexus** → ipo_ma → other | 7 |
   | (other) | econ → politics → tech → society → ipo_ma → other | 6 |

   **Print the resolved values before Step 2.** Emit one visible line per generated file so the translation step cannot be silently skipped:
   ```
   DERIVED[zh]: country_display=<value>  date_display=<value>  out_md=<absolute path>  out_docx=<absolute path>
   DERIVED[en]: country_display=<value>  date_display=<value>  out_md=<absolute path>  out_docx=<absolute path>   # bilingual only
   ```
   Self-check (per `lang` in `langs`): when that `lang` is `zh` or `ja`, the country segment of `out_md_{lang}`/`out_docx_{lang}` **must** be the translated `country_display_{lang}`, not the raw `--country` input. If the filename contains only ASCII letters in the country segment for a non-English `lang` (e.g. `china-2026-04-21.md` for `lang=zh`), abort and regenerate — you skipped the translation.

   Expand `~` and substitute `{date}` in `out_dir`:
   ```bash
   OUT_DIR="${out_dir/#\~/$HOME}"
   OUT_DIR="${OUT_DIR//\{date\}/$DATE}"
   ```
   Use `OUT_DIR` (expanded) in all subsequent bash commands. The default resolves to e.g. `~/Desktop/github/daily-news-reports/2026-04-16/`.

2. **Scan candidates** (Scanner stage, English only — SINGLE AGENT). Launch **ONE Scanner subagent** for the full report. **The Scanner is a `general-purpose` subagent with the `skills/daily-news-intelligence/agents/daily-news-scanner.md` body embedded and model `sonnet` passed explicitly — never `subagent_type: sci-research:daily-news-scanner` (see § Subagent Dispatch Rule).** The Scanner prompt carries **all** `active_categories` plus `country`, `date`, `min_per_category`; it processes each category sequentially (Pass A + Pass B per category), then performs cross-category dedup + routing, and returns a unified Scanner Bundle (`references/schemas.md` § Scanner Bundle Schema). Query construction is **per-term, never `OR`-joined** — see `skills/daily-news-intelligence/agents/daily-news-scanner.md` § Step 1 for the term lists (single source of truth).

   **Per-category specifics:**
   - **Corporate IPO & M&A** — runs in every report; country-anchored. Primary-filing queries (SEC EDGAR / LSE RNS / exchange disclosure) and T3 Finance & Trade/Legal verticals are **always-first-class** — run first regardless of `min_per_category`.
   - **China-Nexus** — runs **only in a China report**; **not** `{country}`-anchored (region-unbounded global topical sweep); leads with the external-T4 + global-wire sweep.

   Authoritative rules (eligibility, China-aid exclusion + key-industry carve-out, materiality floor, `china_nexus`↔`ipo_ma` routing) live in `references/rubric.md` § Conditional & Topical Categories.

The Scanner gathers 20-30 candidate URLs across all categories. If the Scanner Bundle is empty (main pool AND reserve pool), stop and report: "No news candidates found for {country} on {date}. The date may be a future date, a holiday, or WebSearch may be temporarily unavailable." Do not proceed to the Verifier.

3–6. **[Scanner internal]** Per-URL date verification, tier filtering, category coverage enforcement, per-category dedup, cross-category dedup, and `china_nexus`↔`ipo_ma` routing all happen inside the Scanner per `agents/daily-news-scanner.md`. The orchestrator waits for the Scanner Bundle before proceeding.

7. **Quality filter** (Verifier stage). Spawn per § Subagent Dispatch Rule (`general-purpose` + `skills/daily-news-intelligence/agents/news-verifier.md` body, model `sonnet`) with the **Scanner Bundle** (`references/schemas.md` § Scanner Bundle Schema) included verbatim in its prompt. The Verifier applies the five-check rubric in `references/rubric.md` (originality, authority, impact, **source legitimacy**, dedup-validation) plus § Source Legitimacy for Pass-B sources. Applies the **Three-Step Coverage Fallback** if any category drops below `min_per_category`: Fallback 1 relaxes impact tier (→ `Regional-structural`); Fallback 1.5 promotes from the Scanner Bundle's `## Reserve Pool` (held `below-authority-cap` candidates become `T3-extended` Leads; held `below-ipo-ma-floor` soft-band deals become Leads at their real tier) — revalidating Source Legitimacy on every promotion, never relaxing date / China red-line / originality; Fallback 2 records the gap. Hard-paywall Leads (`Body-source: paywall-stub`, admitted at Scanner Step 3.5 when no free same-event alternative existed) flow through unchanged — the Writer's mandatory ≥2 background-search obligation and Editor Pass 3's quote-downgrade rule handle the body and quote constraints downstream. Emits the Verifier Output Schema from `references/schemas.md`. The orchestrator captures this output for the next two stages (Fact-Extractor and Writer).

7.5. **Extract Fact Manifest** (Fact-Extractor stage). Spawn per § Subagent Dispatch Rule (`general-purpose` + `skills/daily-news-intelligence/agents/daily-fact-extractor.md` body, model `sonnet`) with the Verifier's full output included verbatim in its prompt plus `country`, `date`, `lang`, and `out_manifest`. Resolve `out_manifest` to `${OUT_DIR}/fact-manifest-{country_slug}-{date}.yaml` where `{country_slug}` is the lowercase ASCII slug of `country` (e.g. `japan`, `united-kingdom`, `china`). The agent emits a YAML Fact Manifest — one entry per KEPT story listing every number, date, named person, institution, product, and direct quote in the Verifier's `factual_excerpt`, each anchored to its source URL with a verbatim excerpt (see `skills/daily-news-intelligence/agents/daily-fact-extractor.md` for the full schema). The Fact-Extractor calls `Write` once and returns confirmation. The orchestrator captures the manifest path for downstream stages (Writer in Step 8; Editor in the future Step 8.5).

8. **Translate and write the report** (Writer stage — **fans out per `lang` in `langs`** when `is_bilingual`). Spawn per § Subagent Dispatch Rule (`general-purpose` + `skills/daily-news-intelligence/agents/daily-news-writer.md` body, model `opus`). Ensure the output directory exists:
   ```bash
   mkdir -p "$OUT_DIR"
   ```
   If `mkdir -p` fails (permissions, read-only filesystem), stop and report the error — do not silently write to a fallback location.

   **For each `lang` in `langs`** (single-lang: 1 invocation; bilingual: 2 invocations) launch a separate Writer subagent, each receiving:
   - The same Verifier KEEP set (verbatim, inline) — the **spine of which stories run**.
   - The same Fact Manifest (path or content) — the **locked-fact contract**.
   - That invocation's `lang`, `out_md_{lang}`, `country`, `date`, `min_per_category`.

   Each Writer invocation **runs 1-3 supplemental `WebSearch` / `WebFetch` calls per story by default** to enrich body prose with background context — what came before, broader pattern, prior policy. Each invocation generates its own background searches independently (no cross-lang sharing — keeps the prompt simple, accepts the duplicated web cost). **References = Verifier KEEP URLs ∪ {search URLs that supplied a fact in body}** — every search URL whose content backed a body fact MUST be cited with proper APA and continuous `[N]` (see `references/output-spec.md` § Cited Search URLs).

   Compose narrative in `lang` per `references/language-spec.md`. Structure is `### title → body → **References**` per story — **no `**摘要**` / `**Summary**` / `**要約**` / `**分析**` / `**Analysis**` markers anywhere**. **Quote marks follow `references/language-spec.md` § Canonical Quote Marks** (en ASCII `""` / zh curly `""` / ja corner `「」` — the format-check hook blocks Write on any non-canonical char). When `lang=zh`, also comply with `references/language-spec.md` § Language-Specific Rules (official titles, country prefixes, time anchors, terminology, foreign media naming). Produce Markdown obeying `references/output-spec.md`. Use the `Write` tool to overwrite `out_md_{lang}`.

   **Bilingual parallelism**: the two Writer invocations may run in parallel (independent inputs / independent outputs / no shared file). Sequential is also fine — the dominant cost is Opus inference, not orchestration overhead.

8.5. **Fact-check + local-fluency editor pass** (Editor stage — **fans out per `lang` in `langs`** when `is_bilingual`). Spawn per § Subagent Dispatch Rule (`general-purpose` + `skills/daily-news-intelligence/agents/daily-editor.md` body, model `opus`).

   **For each `lang` in `langs`** (single-lang: 1 invocation; bilingual: 2 invocations) launch a separate Editor subagent, each receiving:
   - `writer_md_path` = `out_md_{lang}` (this lang's Writer output).
   - `manifest_path` (same single manifest from Step 7.5).
   - `verifier_bundle` (same Verifier output verbatim, inline).
   - That invocation's `lang`, `date`, `country`.

   Each Editor patches its own MD in place using `Edit` (never `Write`) across **five sequential passes**:

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

9. **Export to Word** (**fans out per `lang` in `langs`** when `is_bilingual`). First verify pandoc is available:
   ```bash
   command -v pandoc >/dev/null 2>&1
   ```
   If pandoc is not installed, skip docx export and report: "pandoc not found — .docx export skipped. Install pandoc to enable Word export." The Markdown file(s) remain valid output. If pandoc is available, run one export **per `lang` in `langs`**:
   ```bash
   for L in "${LANGS[@]}"; do
     MD_BASENAME="$(basename "$(eval echo \"\$out_md_$L\")")"
     DOCX_BASENAME="$(basename "$(eval echo \"\$out_docx_$L\")")"
     cd "$OUT_DIR" && pandoc --extract-media=./media "$MD_BASENAME" -o "$DOCX_BASENAME"
   done
   ```
   (Single-lang: this loop has 1 iteration; bilingual: 2 iterations.) If pandoc exits non-zero on any iteration, report the error but do not delete the Markdown file — the next iteration still runs.

10. **Send email** (optional — only if `email` parameter is non-empty). Build the subject and body per `references/email-spec.md` (single-lang or bilingual variant based on `is_bilingual`), write the body to a temp file, assemble the attachment list per § Attachment Selection (bilingual doubles the file count), and invoke:
    ```bash
    python3 "${CLAUDE_PLUGIN_ROOT}/scripts/send-report-email.py" \
      --to "{email}" \
      --subject "{email_subject}" \
      --body-file "{tmp_body_file}" \
      --attach {attach_files} \
      [--dry-run if email_dry_run=true]
    ```
    Where `{attach_files}` is one of:
    - Single-lang `email_attach=both` → `$out_md $out_docx` (2 files)
    - Single-lang `email_attach=docx` / `md` / `none` → 1 / 1 / 0 files
    - Bilingual `email_attach=both` → `$out_md_primary $out_docx_primary $out_md_secondary $out_docx_secondary` (4 files)
    - Bilingual `email_attach=docx` → `$out_docx_primary $out_docx_secondary` (2 files)
    - Bilingual `email_attach=md` → `$out_md_primary $out_md_secondary` (2 files)
    - Bilingual `email_attach=none` → omit `--attach`

    `send-report-email.py --attach` is already `nargs="*"` — no script change needed. Handle the script's non-zero exit codes per `references/email-spec.md` § Exit Code Handling. **Email failure must never delete or modify the local `.md` or `.docx` files** — they were already delivered in Step 8-9.

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
| Scanner (Step 2, single agent — all active categories sequentially) | `general-purpose` + embed `skills/daily-news-intelligence/agents/daily-news-scanner.md` body, model `sonnet` (see § Subagent Dispatch Rule) | `references/rubric.md`, `references/schemas.md` |
| Verifier (Step 7) | `general-purpose` + embed `skills/daily-news-intelligence/agents/news-verifier.md` body, model `sonnet` | `references/rubric.md`, `references/schemas.md` |
| Fact-Extractor (Step 7.5) | `general-purpose` + embed `skills/daily-news-intelligence/agents/daily-fact-extractor.md` body, model `sonnet` | (Verifier output only — agent prompt has full schema) |
| Writer (Step 8 — **× len(langs)** in bilingual mode) | `general-purpose` + embed `skills/daily-news-intelligence/agents/daily-news-writer.md` body, model `opus` | `references/language-spec.md`, `references/output-spec.md`, `references/verification.md`, Fact Manifest from Step 7.5 |
| Editor (Step 8.5 — **× len(langs)** in bilingual mode) | `general-purpose` + embed `skills/daily-news-intelligence/agents/daily-editor.md` body, model `opus` | Writer's MD (per lang), Fact Manifest (shared), Verifier bundle (verbatim, shared), `references/language-spec.md` § Canonical Quote Marks (Pass 4) + § Language Rules (Pass 5 foreign-residue / inconsistent-name detection) |
| Email sender (Step 10) | — (Bash + `scripts/send-report-email.py`) | `references/email-spec.md` |
| Orchestrator delivery check | — | `references/verification.md` |

See `references/verification.md` § Recommended Agent Assignment for substitution rules and caveats. **The § Subagent Dispatch Rule above overrides any `sci-research:*` agent name appearing in that section or elsewhere — execution is always `general-purpose` + embedded body.**

## Failure Modes

Scattered through the Workflow above; consolidated here for quick scanning. **None of these may silently swallow errors — always report what failed and why.**

| Condition | Handling |
|-----------|----------|
| Scanner Bundle empty (main + reserve) | STOP. Report: "No news candidates found for {country} on {date}. The date may be a future date, a holiday, or WebSearch may be temporarily unavailable." Do not proceed to Verifier. |
| `mkdir -p "$OUT_DIR"` fails (permissions / read-only FS) | STOP. Report the OS error. Do not silently fall back to a different path. |
| `--lang` has 3+ tokens (e.g. `zh+en+ja`) | REJECT at Step 1. Report: "1.18.0 supports at most 2-language combos (zh+en, en+zh, zh+ja, ja+zh, en+ja, ja+en). 3-language combos are not implemented in this release." |
| `--lang` has an unknown token (e.g. `zh+ko`) | REJECT at Step 1. Report which token is invalid; the supported set is `zh / en / ja`. |
| `--lang` repeats a token (e.g. `zh+zh`) | REJECT at Step 1. Report: "bilingual mode requires two distinct languages." |
| Bilingual: one Writer succeeds, the other fails | Report which `lang` failed and why. Do NOT delete the succeeding-lang's MD. Skip pandoc + email for the failing lang; the email Step 10 must still run for the succeeding lang (single-lang fallback body) OR halt entirely — orchestrator choice, default: halt + report. |
| Editor Pass 5 unrecoverable failure (per lang) | Abort Pass 5 for that lang only. Pipeline continues with Passes 1-4's changes for that lang. Other lang(s) unaffected. Log it; do not gate the run. |
| `pandoc` not installed | Skip docx export for ALL langs. Markdown(s) remain valid output. Report: "pandoc not found — .docx export skipped." |
| `pandoc` exits non-zero on one lang | Report the error for that lang. Continue with the next lang. Do NOT delete any Markdown file. |
| Email script exits non-zero (codes 1-9) | Halt and report per `references/email-spec.md` § Exit Code Handling. **Never** delete or modify any local `.md` / `.docx`. **Never** fall back to inline SMTP — the PreToolUse hook will reject it anyway. |
| `out_dir` is not a git working tree | Skip Step 12 (publish). Best-effort detection: walk up at most three levels looking for `.git`. |
| `git push` fails in Step 12 | Report but do not fail the run — the docx already exists on disk; the user can push manually. |

## References

| File | Contents | Consumed by |
|------|----------|-------------|
| `references/schemas.md` | Scanner Bundle Schema (all categories), Verifier Output Schema | Scanner, Verifier |
| `references/rubric.md` | Source Tier Rules, Source Discovery Model (with Reserve Pool), Source Legitimacy Rubric, Authority & Impact Rubric, Three-Step Coverage Fallback (1 impact / 1.5 reserve-pool promote / 2 gap), Date Verification Rules, Category Coverage Rules, Conditional & Topical Categories (three-band ipo_ma materiality) | Scanner, Verifier |
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

# Bilingual mode (1.18.0+) — 4 attachments (zh+en md + docx) + stacked zh+en email body
/daily-news-intelligence --country "China" --lang zh+en --email "boss@company.com"
/daily-news-intelligence --country "Japan" --lang en+zh --email "you@gmail.com" --email-attach docx
/daily-news-intelligence --country "Germany" --lang zh+ja --email "you@gmail.com" --email-dry-run
```
