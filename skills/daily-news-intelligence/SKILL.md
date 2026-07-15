---
name: daily-news-intelligence
description: "Generate a dated single-country daily news briefing (daily news, news intelligence, daily briefing, country news report, 每日新闻, 每日情报, デイリーニュース). Five-stage Scanner → Verifier → Fact Extractor → Writer → Editor pipeline: adaptive English WebSearch with per-URL date verification, credibility and editorial review, target-language Markdown, final fact/style checks, and optional docx/email delivery. Supports scheduled/automated execution."
---

# Daily News Intelligence (Single Country)

Generate a professional dated daily report for institutional readers covering a single country or region. Designed for both interactive and **scheduled/automated** execution. Evidence collection is always performed in English against verified live web sources; the final report is translated into the requested target language at the end.

## Quick Reference (Orchestrator Checklist)

**Rule (every stage):** spawn the exact installed `sci-research-*` custom agent with `fork_turns="none"` (see § Subagent Dispatch Rule below).

**Pipeline flow** (high-level — Workflow below has the numbered procedure with bash commands):

- Validate params → parse `lang` as `langs = lang.split('+')` (single or bilingual) → expand `~` → compute derived fields per `lang` (incl. `active_categories`)
- Launch ONE Scanner with all active categories (6 or 7); it searches them sequentially using adaptive source discovery, aims for a broad per-category candidate buffer, performs cross-category dedup + routing internally, and emits one unified Scanner Bundle
- IF Scanner Bundle has no stories → STOP with message
- Verifier (Scanner Bundle in prompt) → credibility + new-information + daily-news-value + originality + dedup review → Coverage Review for short categories → Verifier Output Schema
- Fact-Extractor (Verifier output + params) → fact-manifest YAML (single, language-agnostic — shared across bilingual halves)
- **FAN OUT per `lang` in `langs` — PARALLEL** (concurrent Writer subagents in one orchestrator message; then concurrent Editor subagents after all Writers complete; see § Workflow Step 8 § Bilingual execution order for rationale):
  - Writer (Verifier output + manifest path + that `lang`'s params) → one `apply_patch` operation creating or overwriting Markdown at `out_md_{lang}`
  - Editor (`writer_md_{lang}` + manifest + `verifier_bundle` + lang/date/country) → in-place `apply_patch` operations across 5 passes (1 fact / 2 search-backing / 3 quote / 4 quote-mark / 5 local fluency)
  - pandoc export `out_md_{lang}` → `out_docx_{lang}` (skip if pandoc missing; sequential bash loop is fine — pandoc is local + fast)
- IF `--email` → send via `scripts/send-report-email.py` (dry-run or real). Single-lang body + 1-2 attachments. **Bilingual body (stacked primary+secondary)** + 2-4 attachments per § email-spec.md.
- Verify: `ls` each generated `out_md_{lang}` / `out_docx_{lang}`, grep H2/H3 counts per file

## Operating Principle

Evidence priority order:

1. Articles whose publication date matches `date` exactly, verified by WebSearch `open_page` on the canonical URL (primary truth).
2. `web_search` is only used to surface candidate URLs — never standalone evidence.
3. Model inference is permitted only when directly supported by the opened article text.

Apply a two-stage filter before anything reaches the Writer:

- **Stage 1 (Scanner, single agent)**: one Scanner across all active categories sequentially. It searches broadly without a fixed outlet list or source tiers, prefers official primary channels and accountable international, national, regional, and specialist media, verifies each URL's date and geography, then performs cross-category dedup + `china_nexus`↔`ipo_ma` routing. It aims for `max(min_per_category * 2, 6)` distinct candidates per category when credible material exists.
- **Stage 2 (Verifier)**: source credibility and evidence fit + concrete new information + daily briefing value + originality/corroboration + dedup/category validation. It uses contextual editorial judgement rather than fixed impact numbers or outlet grades, then runs Coverage Review for any category below `min_per_category`.

Hard rules:

- Do not admit a candidate without passing the date-verification gate.
- When normalized `country == Europe`, apply the hard `Europe-ex-UK` geography gate in `references/rubric.md`: a UK-only or UK-primary event is out of scope. Outlet nationality is not event geography, so UK publications remain valid sources for in-scope European events.
- Do not pad a category with untrustworthy, off-date, out-of-scope, or fact-free material.
- Do not merge unrelated events into one synthetic story.
- Cross-category dedup and routing happen inside the Scanner before the Verifier.
- The Writer must read the Verifier's KEEP set, never the Scanner Bundle directly.

## Input Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `country` | Yes | — | Single country or region, e.g. `United Kingdom`, `Europe`, `Japan`, `China`, `Germany`. `Europe` uses the Europe-ex-UK scope defined in `references/rubric.md`. |
| `date` | No | today | Target publication date in ISO `YYYY-MM-DD` |
| `lang` | No | `zh` | Output language for the final report. Single: `zh` / `en` / `ja`. **Bilingual (1.18.0+)**: any two of `zh / en / ja` joined by `+` (`zh+en`, `en+zh`, `zh+ja`, `ja+zh`, `en+ja`, `ja+en`). The first token is the **primary language** (drives email subject + body lead section). 3-language combos are not supported in 1.18.0. |
| `out_dir` | No | `~/.sci-research/reports/daily-news/{date}/` | Output directory. `{date}` is replaced with the ISO date (e.g. `2026-04-16`). `~` is expanded at runtime. The directory is auto-created if missing (Workflow Step 8). |
| `min_per_category` | No | `2` | Minimum stories per category |
| `email` | No | empty | Comma-separated recipient email addresses. When non-empty, Step 10 emails the report via Gmail SMTP. |
| `email_subject` | No | auto | Email subject line. Default is `{country_display} {title_label} — {date_display}` in `lang`. |
| `email_body` | No | auto | Plain-text email body. Default template in `references/email-spec.md` filled with Verifier coverage counts. |
| `email_attach` | No | `both` | Attachment selection: `both` (md + docx), `docx`, `md`, or `none`. |
| `email_dry_run` | No | `false` | When `true`, Step 10 prints a preview and exits without connecting to SMTP. |

Derived fields (`date_en`, `date_display`, `country_display`, `out_md`, `out_docx`) are computed per `lang` — see `references/language-spec.md`. **Bilingual mode (1.18.0+)** computes one set per token in `langs = lang.split('+')` — i.e. `out_md_zh` + `out_md_en`, `country_display_zh` + `country_display_en`, etc. See `references/language-spec.md` § Bilingual Mode.

Email delivery reads Gmail SMTP credentials from environment variables (`GOOGLE_EMAIL_USERNAME`, `GOOGLE_EMAIL_APP_PASSWORD`, `GOOGLE_EMAIL_FROM_NAME`, `GOOGLE_EMAIL_HOST`, `GOOGLE_EMAIL_PORT`, `GOOGLE_EMAIL_START_TLS`). See `.env.example` at the repo root and `references/email-spec.md` for the full spec.

## Runtime Paths

Before running the workflow, set `SKILL_DIR` to the absolute directory containing this `SKILL.md`, then derive the plugin root once:

```bash
SKILL_DIR=<absolute path to skills/daily-news-intelligence>
PLUGIN_ROOT="$(cd "$SKILL_DIR/../.." && pwd)"
RUNTIME_SYNC="$PLUGIN_ROOT/skills/setup-sci-research-runtime/scripts/sync_runtime.py"
```

Use these absolute paths for every bundled script. Do not rely on the current working directory or on Claude-specific environment variables. Before Step 1, run `python3 "$RUNTIME_SYNC" --project-root "$PWD" --check`. If it fails, stop and tell the user to run `$sci-research:setup-sci-research-runtime` in this workspace, then start a new Codex task.

## Data Handoff Between Stages

### Subagent Dispatch Rule (READ FIRST — applies to every stage below)

Every stage runs as a **native Codex custom agent** installed by `$sci-research:setup-sci-research-runtime`. For each stage the orchestrator MUST:

1. Select the exact custom-agent role through the spawn tool's agent-type/role selector: `sci-research-daily-news-scanner`, `sci-research-news-verifier`, `sci-research-daily-fact-extractor`, `sci-research-daily-news-writer`, or `sci-research-daily-editor`. `task_name` is only a thread label and MUST NOT be used as the role selector.
2. Set `fork_turns="none"` so the selected role's TOML model, reasoning effort, and developer instructions are applied instead of inheriting a full parent history.
3. Start every spawn prompt with absolute `plugin_root: {PLUGIN_ROOT}` and `skill_root: {SKILL_DIR}`, then pass that stage's injected parameters + the verbatim upstream output (per the handoff list below).
4. Wait for the subagent's result, then feed it into the next stage.

If the active Codex surface exposes no custom-agent selector, rejects the role as unknown, or cannot start it with `fork_turns="none"`, halt with a runtime-compatibility error. Do not fall back to `default`, `worker`, `explorer`, another generic subagent, or an embedded copy of the TOML instructions.

Model allocation is set per-agent in the TOML: Scanner = `gpt-5.6-luna / medium`; Verifier = `gpt-5.6-terra / high`; Fact-Extractor = `gpt-5.4-mini / medium`; Writer and Editor = `gpt-5.6-sol / high`. Do NOT pass a model argument at spawn time. Native Codex subagents receive their tools directly (no embed workaround).

The orchestrator passes data between stages via the subagent **prompt text** — not environment variables. Every prompt includes the runtime-path header above. Specifically:

- **Orchestrator → Scanner**: the orchestrator launches ONE Scanner subagent with **all** `active_categories` plus `country`, `date`, `min_per_category`, and `geography_scope`. The Scanner processes all categories sequentially, performs cross-category dedup + routing internally, and returns a unified Scanner Bundle (`references/schemas.md` § Scanner Bundle Schema).
- **Scanner → Verifier**: the orchestrator includes the Scanner's full Scanner Bundle verbatim plus `country`, `min_per_category`, and `geography_scope` in the Verifier agent's prompt.
- **Verifier → Fact-Extractor**: The orchestrator includes the Verifier's full output verbatim plus runtime parameters (`country`, `date`, `lang`) and `out_manifest` (target YAML path, e.g. `${OUT_DIR}/fact-manifest-{country_slug}-{date}.yaml`) in the Fact-Extractor agent's prompt. The Fact-Extractor writes the manifest to `out_manifest` and returns confirmation.
- **Verifier + Fact-Extractor → Writer (per `lang` in `langs`)**: For each `lang` the orchestrator launches a separate Writer subagent with the same Verifier full output, the same Fact Manifest content (read from `out_manifest`) or its absolute path, plus that invocation's runtime parameters: a **single `lang` token** (never the combined `zh+en` string), `out_md_{lang}` **passed into the Writer body's generically-named `out_md` parameter**, plus `country`, `date`, `min_per_category`. Single-lang: 1 Writer invocation. **Bilingual: N Writer invocations dispatched CONCURRENTLY** — emit multiple Agent tool calls in a single orchestrator message so they run in parallel. See § Workflow Step 8 § Bilingual execution order for rationale. (The Writer / Editor agent bodies are pure single-lang by design — they need no bilingual awareness; all bilingual logic lives in this orchestrator.)
- **Writer + Fact-Extractor + Verifier → Editor (per `lang` in `langs`)**: After ALL Writers in Step 8 have completed (Editor needs `writer_md_path` on disk), the orchestrator launches a separate Editor subagent **per lang, concurrently in a single message** with `writer_md_path` = `out_md_{lang}`, `manifest_path` (single, from Step 7.5), `verifier_bundle` (same Verifier output passed verbatim, inline), plus that invocation's runtime parameters (that `lang`, `date`, `country`). Each Editor makes surgical in-place `apply_patch` calls on its own `writer_md_path` and prints a structured stdout report. The format-check hook fires on every `apply_patch` and on the final state, per file — parallel hooks on different files are safe.

The orchestrator must not summarise, truncate, or reformat the upstream output — pass it verbatim so downstream agents can parse the expected schema.

## Workflow

1. **Validate scope.** Normalize `country` for English search and target-language rendering. Default `date` to today (`date +%Y-%m-%d`). Parse `lang` into the list `langs = lang.split('+')` — single-lang has `len == 1`, bilingual (1.18.0+) has `len == 2`. Reject `len > 2` (3-language combos are not supported in 1.18.0). Set `primary_lang = langs[0]`, `secondary_lang = langs[1] if len(langs) > 1 else None`, `is_bilingual = len(langs) == 2`.

   Derive `geography_scope = Europe-ex-UK` when normalized `country == Europe`; otherwise set `geography_scope = country`. `Europe-ex-UK` preserves the pipeline's existing Europe coverage rather than redefining it as EU-27, but hard-excludes any event whose sole or primary geographic nexus is the United Kingdom. UK outlets remain searchable because source location does not determine event scope. The detailed mixed-event and `ipo_ma` rules are authoritative in `references/rubric.md` § Geographic Scope Gate.

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
   Use `OUT_DIR` (expanded) in all subsequent bash commands. The default resolves to e.g. `~/.sci-research/reports/daily-news/2026-04-16/`.

   Derive `country_slug` once from normalized English `country` (lowercase ASCII, spaces and punctuation collapsed to `-`). Then set:

   ```bash
   AUDIT_DIR="$OUT_DIR/audit"
   SCANNER_AUDIT="$AUDIT_DIR/scanner-bundle-${country_slug}-${DATE}.txt"
   VERIFIER_AUDIT="$AUDIT_DIR/verifier-report-${country_slug}-${DATE}.txt"
   mkdir -p "$AUDIT_DIR"
   ```

   Audit artifacts use `.txt`, not `.md`, so Pipeline D never mistakes them for country reports. If directory creation fails, stop and report the error.

2. **Scan candidates** (Scanner stage, English only — SINGLE AGENT). Launch **ONE Scanner subagent** for the full report. **Spawn `sci-research-daily-news-scanner` (`.codex/agents/sci-research-daily-news-scanner.toml`) — see § Subagent Dispatch Rule.** The Scanner prompt carries **all** `active_categories` plus `country`, `date`, `min_per_category`, and `geography_scope`; it processes each category sequentially using adaptive broad discovery, applies the hard date and geography gates, classifies source provenance, then performs cross-category dedup + routing and returns a unified Scanner Bundle (`references/schemas.md` § Scanner Bundle Schema). It does not use a fixed outlet matrix, per-domain sweep, or source tier.

   **Per-category specifics:**
   - **Corporate IPO & M&A** — runs in every report; country-anchored. Search official filings/disclosures and accountable business, legal, financial, regional, and specialist reporting adaptively. Eligibility is contextual; no fixed transaction-value floor decides whether an event is newsworthy.
   - **China-Nexus** — runs **only in a China report**; **not** `{country}`-anchored (region-unbounded global topical sweep). It follows the China external-view rule and searches eligible external official and media sources without a fixed domain list.

   Authoritative rules (source eligibility, China-aid exclusion + key-industry carve-out, contextual IPO/M&A materiality, and `china_nexus`↔`ipo_ma` routing) live in `references/rubric.md` § Conditional and Topical Categories.

The Scanner aims for `max(min_per_category * 2, 6)` distinct, credible, date-verified events per category when available. If the Scanner Bundle contains no stories, stop and report: "No news candidates found for {country} on {date}. The date may be a future date, a holiday, or WebSearch may be temporarily unavailable." Do not proceed to the Verifier.

After receiving a non-empty Scanner Bundle, use `apply_patch` to create or overwrite `SCANNER_AUDIT` with the full Scanner output verbatim. Do not summarize or reformat it. This artifact records admitted candidates, rejection counts, source assessments, and discovery gaps.

3–6. **[Scanner internal]** Adaptive discovery, per-URL date verification, hard geography filtering, source-eligibility assessment, candidate-buffer enforcement, per-category dedup, cross-category dedup, and `china_nexus`↔`ipo_ma` routing all happen inside the Scanner per `.codex/agents/sci-research-daily-news-scanner.toml`. The orchestrator waits for the Scanner Bundle before proceeding.

7. **Quality filter** (Verifier stage). Spawn `sci-research-news-verifier` (`.codex/agents/sci-research-news-verifier.toml`) per § Subagent Dispatch Rule with the **Scanner Bundle** (`references/schemas.md` § Scanner Bundle Schema) included verbatim in its prompt plus `country`, `min_per_category`, and `geography_scope`. The Verifier re-applies the hard geography and China external-view gates, then evaluates source credibility/evidence fit, concrete new information, contextual daily briefing value, originality/corroboration, and dedup/category placement. It does not use outlet tiers, fixed financial thresholds, or a named-byline requirement. If a category is short, Coverage Review may admit credible narrower regional, specialist, institutional, or company-level developments, but never relaxes date, geography, source provenance, factual support, or true-duplicate rules. Hard-paywall Leads (`Body-source: paywall-stub`) flow through unchanged; the Writer's mandatory background-search obligation and Editor quote checks handle body depth and quote retrievability. The Verifier emits the schema from `references/schemas.md`, including a complete DROP audit and any remaining coverage gaps.

   After receiving the Verifier output, use `apply_patch` to create or overwrite `VERIFIER_AUDIT` with the full Verifier output verbatim. Do not summarize or reformat it. This is the durable KEEP/DROP audit for the run and must be written before Fact-Extractor starts.

7.5. **Extract Fact Manifest** (Fact-Extractor stage). Spawn `sci-research-daily-fact-extractor` (`.codex/agents/sci-research-daily-fact-extractor.toml`) per § Subagent Dispatch Rule with the Verifier's full output included verbatim in its prompt plus `country`, `date`, `lang`, and `out_manifest`. Resolve `out_manifest` to `${OUT_DIR}/fact-manifest-{country_slug}-{date}.yaml` where `{country_slug}` is the lowercase ASCII slug of `country` (e.g. `japan`, `united-kingdom`, `china`). The agent emits a YAML Fact Manifest — one entry per KEPT story listing every number, date, named person, institution, product, and direct quote in the Verifier's `factual_excerpt`, each anchored to its source URL with a verbatim excerpt (see `.codex/agents/sci-research-daily-fact-extractor.toml` for the full schema). The Fact-Extractor calls `apply_patch` once and returns confirmation. The orchestrator captures the manifest path for downstream stages (Writer in Step 8; Editor in the future Step 8.5).

8. **Translate and write the report** (Writer stage — **fans out per `lang` in `langs`** when `is_bilingual`). Spawn `sci-research-daily-news-writer` (`.codex/agents/sci-research-daily-news-writer.toml`) per § Subagent Dispatch Rule. Ensure the output directory exists:
   ```bash
   mkdir -p "$OUT_DIR"
   ```
   If `mkdir -p` fails (permissions, read-only filesystem), stop and report the error — do not silently write to a fallback location.

   **For each `lang` in `langs`** (single-lang: 1 invocation; bilingual: 2 invocations) launch a separate Writer subagent, each receiving:
   - The same Verifier KEEP set (verbatim, inline) — the **spine of which stories run**.
   - The same Fact Manifest (path or content) — the **locked-fact contract**.
   - That invocation's runtime parameters: **`lang` = a SINGLE token** (`zh` / `en` / `ja` — NEVER the combined `zh+en` string; the Writer's Localisation Table has no combined column and would break), **`out_md` = the value of `out_md_{lang}`** (the Writer body's parameter is literally named `out_md`; pass this invocation's per-lang path into that slot), plus `country`, `date`, `min_per_category`. The Writer derives `country_display` / `date_display` itself from `lang` via the Localisation Table — by construction this matches the `country_display_{lang}` the orchestrator used to build `out_md_{lang}`, so the H1 and the filename agree.

   Each Writer invocation **runs 1-3 supplemental WebSearch `search` actions per story by default and `open_page` for every result used in body prose** to enrich background context — what came before, broader pattern, prior policy. Each invocation generates its own background searches independently (no cross-lang sharing — keeps the prompt simple, accepts the duplicated web cost). **References = Verifier KEEP URLs ∪ {search URLs that supplied a fact in body}** — every search URL whose content backed a body fact MUST be cited with proper APA and continuous `[N]` (see `references/output-spec.md` § Cited Search URLs).

   Compose narrative in `lang` per `references/language-spec.md`. Structure is `### title → body → **References**` per story — **no `**摘要**` / `**Summary**` / `**要約**` / `**分析**` / `**Analysis**` markers anywhere**. **Body length follows `references/language-spec.md` § Body Length Rules**: `en` targets 300 words and must stay within 250–350; `zh` targets 500 Unicode Han characters and must stay within 450–550; `ja` remains unrestricted. **Quote marks follow `references/language-spec.md` § Canonical Quote Marks** (en ASCII `""` / zh curly `“”` / ja corner `「」` — the format-check hook reports any non-canonical char immediately after the edit). When `lang=zh`, also comply with `references/language-spec.md` § Language-Specific Rules (official titles, country prefixes, time anchors, terminology, foreign media naming). Produce Markdown obeying `references/output-spec.md`. Use one `apply_patch` operation to create or overwrite the `out_md` path it was given (= this invocation's `out_md_{lang}`).

   **Bilingual execution order — PARALLEL**. Spawn both Writer subagents in a single orchestrator message (multi-Agent-tool-uses in one turn). Each Writer is independent: separate `lang`, separate `out_md_{lang}`, no shared file, no shared state. The orchestrator awaits both invocations and proceeds when both have returned.

   Rationale:

   1. **Native Codex parallelism.** Writer and Editor instances operate on independent language-specific paths, so the orchestrator can dispatch them concurrently and wait for all results before entering the dependent stage.
   2. **Wall-clock win.** Sequential adds ~10 min to a typical bilingual run (Writer ~5-10 min + Editor ~3-5 min, both ×2). Parallel runs both lang chains concurrently; total wall-clock = `max(zh_chain, en_chain)` rather than `sum`.
   3. **Failure isolation preserved.** Each Writer writes to its own `out_md_{lang}`. If one fails, the other's output is still on disk. The orchestrator handles "one succeeded, one failed" per the Failure Modes table.
   4. **Hook safety.** `daily-news-format-check` is `PostToolUse:apply_patch` and reads the specific file the patch touched. Parallel hooks fire on different files (`out_md_zh` vs `out_md_en`) with no shared state — Node-level concurrency is not a problem.

   **Cost paid for parallel** (honest accounting, not a reason to revert):

   - **Duplicated prompt work.** Parallel language instances do not share a sequential prompt-cache opportunity. Actual cost depends on the configured agent models and account pricing; measure it from the run rather than relying on a fixed estimate.
   - **Concurrent web-call rate.** Parallel Writers increase WebSearch `search` / `open_page` concurrency. Keep the request rate within the account's current tool limits and tolerate individual retries without compromising one language's output.

   **Failure mode** (per the Failure Modes table): if either parallel Writer fails, the orchestrator preserves the surviving lang's output, surfaces the failed lang's error, and defaults to halting Step 8.5 + Step 10 with a clear report.

8.5. **Fact-check + local-fluency editor pass** (Editor stage — **fans out per `lang` in `langs`** when `is_bilingual`; **PARALLEL like Writer**, same rationale as Step 8 § Bilingual execution order). Wait for Step 8 to fully complete first — Editor needs its `writer_md_path` to exist on disk. Then spawn all `sci-research-daily-editor` (`.codex/agents/sci-research-daily-editor.toml`) subagents in a single orchestrator message (multi-Agent-tool-uses in one turn) per § Subagent Dispatch Rule.

   **For each `lang` in `langs`** (single-lang: 1 invocation; bilingual: 2 invocations dispatched concurrently in a single message) launch a separate Editor subagent, each receiving:
   - `writer_md_path` = this lang's `out_md_{lang}` (the file the matching Writer just produced).
   - `manifest_path` (same single manifest from Step 7.5).
   - `verifier_bundle` (same Verifier output verbatim, inline).
   - That invocation's `lang` (a SINGLE token — `zh` / `en` / `ja`, never the combined `zh+en`; the Editor's Pass 4 quote-mark table and Pass 5 foreign-residue check are keyed on a single lang), `date`, `country`.

   Each Editor patches its own MD in place using `apply_patch` across **five sequential passes**:

   | Pass | Purpose |
   |------|---------|
   | 1 | Verifier-locked fact verification (drift back to manifest values) |
   | 2 | Writer-search fact backing (may add new search URLs to References + renumber `[N]`) |
   | 3 | Quote verbatim check (degrade to indirect speech if source disagrees) |
   | 4 | Quote-mark normalization (canonical per `references/language-spec.md`) |
   | 5 | Local-fluency / logic-gap repair under closed five-class defect whitelist: `pass2-cut-gap` · `foreign-residue` · `inconsistent-name` · `filler-marker` · `awkward-connector` |

   **Budgets.** Pass 2 + Pass 3 combined ≤ 2 WebSearch `search` + 4 `open_page` actions per story. Pass 5 is style-only (zero web-search actions) and is capped at **3 Edits / story** and **`2 × story_count` Edits / document**.

   **Pass 5 rollback.** Any Pass-5 patch that violates its six invariants is reverted: manifest facts preserved · References byte-identical · paragraph count preserved · `### title` preserved · quote-mark pairs balanced · no prohibited marker introduced. On unrecoverable failure, Pass 5 aborts gracefully and the pipeline continues with Passes 1-4's changes only.

   **Reporting.** The Editor prints a structured stdout report (drift counts, refs added, claims cut / weakened, quote-mark fixes, per-class Pass-5 totals); the orchestrator logs it but does not gate on it. The format-check hook fires after every `apply_patch` and validates the resulting file — if a patch produces a malformed state, the hook reports the violation and the Editor must correct that file before continuing.

9. **Export to Word** (**fans out per `lang` in `langs`** when `is_bilingual`). First verify pandoc is available:
   ```bash
   FORMAT_CHECK="$PLUGIN_ROOT/scripts/hooks/daily-news-format-check.js"
   for L in "${LANGS[@]}"; do
     MD_PATH="$(eval echo "\$out_md_$L")"
     node "$FORMAT_CHECK" --file "$MD_PATH" || exit 2
   done

   command -v pandoc >/dev/null 2>&1
   ```
   This direct check is the hard delivery gate: unlike PostToolUse feedback, a non-zero result stops export and email until the already-written Markdown is corrected. If pandoc is not installed, skip docx export and report: "pandoc not found — .docx export skipped. Install pandoc to enable Word export." The Markdown file(s) remain valid output. If pandoc is available, run one export **per `lang` in `langs`**:
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
    # Append --attach and its paths only when the attachment list is non-empty.
    # For email_attach=none, send the body-only email without --attach.
    python3 "$PLUGIN_ROOT/scripts/send-report-email.py" \
      --to "{email}" \
      --subject "{email_subject}" \
      --body-file "{tmp_body_file}" \
      {optional_attach_args} \
      [--dry-run if email_dry_run=true]
    ```
    Where `{optional_attach_args}` is derived from:
    - Single-lang `email_attach=both` → `$out_md $out_docx` (2 files)
    - Single-lang `email_attach=docx` / `md` / `none` → 1 / 1 / 0 files
    - Bilingual `email_attach=both` → `$out_md_primary $out_docx_primary $out_md_secondary $out_docx_secondary` (4 files)
    - Bilingual `email_attach=docx` → `$out_docx_primary $out_docx_secondary` (2 files)
    - Bilingual `email_attach=md` → `$out_md_primary $out_md_secondary` (2 files)
    - Bilingual `email_attach=none` → omit `--attach`

    `{optional_attach_args}` is empty for `email_attach=none`; otherwise it is `--attach` followed by the selected paths. The sender supports body-only text emails. Handle the script's non-zero exit codes per `references/email-spec.md` § Exit Code Handling. **Email failure must never delete or modify the local `.md` or `.docx` files** — they were already delivered in Step 8-9.

    **⚠️ Hard rule — sanctioned script only.** The orchestrator MUST invoke `scripts/send-report-email.py` via the Bash subprocess above. **Do NOT** implement email delivery inline by importing `smtplib`, `email.message`, `email.mime`, `MIMEMultipart`, `MIMEText`, `EmailMessage`, or by shelling out to `sendmail` / `mail -s`. Inline implementations invariably skip the dual `Content-Disposition` filename encoding (RFC 2047 `filename=` + RFC 2231 `filename*=`) the sanctioned script applies — without both forms, recipients on corporate Exchange / Outlook see attachments as `noname`. A PreToolUse hook (`scripts/hooks/email-send-guard.js`) rejects Bash commands matching these inline patterns. If the script exits non-zero (codes 1-5 or 7-9), halt and report per the exit-code table — do NOT fall back to an inline implementation.

11. **Verify delivery.** Apply the checks in `references/verification.md` § End-to-End Verification.

## Stage → Agent → Reference Map

| Stage | Recommended Agent | Required References |
|-------|-------------------|---------------------|
| Scanner (Step 2, single agent — all active categories sequentially) | `sci-research-daily-news-scanner` (`.codex/agents/sci-research-daily-news-scanner.toml`) (see § Subagent Dispatch Rule) | `references/rubric.md`, `references/schemas.md` |
| Verifier (Step 7) | `sci-research-news-verifier` (`.codex/agents/sci-research-news-verifier.toml`) | `references/rubric.md`, `references/schemas.md` |
| Fact-Extractor (Step 7.5) | `sci-research-daily-fact-extractor` (`.codex/agents/sci-research-daily-fact-extractor.toml`) | (Verifier output only — agent prompt has full schema) |
| Writer (Step 8 — **× len(langs)** in bilingual mode) | `sci-research-daily-news-writer` (`.codex/agents/sci-research-daily-news-writer.toml`) | `references/language-spec.md`, `references/output-spec.md`, `references/verification.md`, Fact Manifest from Step 7.5 |
| Editor (Step 8.5 — **× len(langs)** in bilingual mode) | `sci-research-daily-editor` (`.codex/agents/sci-research-daily-editor.toml`) | Writer's MD (per lang), Fact Manifest (shared), Verifier bundle (verbatim, shared), `references/language-spec.md` § Canonical Quote Marks (Pass 4) + § Language Rules (Pass 5 foreign-residue / inconsistent-name detection) |
| Email sender (Step 10) | — (Bash + `scripts/send-report-email.py`) | `references/email-spec.md` |
| Orchestrator delivery check | — | `references/verification.md` |

See `references/verification.md` § Recommended Agent Assignment for substitution rules and caveats. **The § Subagent Dispatch Rule above is authoritative — each stage runs as its exact installed `sci-research-*` custom agent.**

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
| Email script exits non-zero (codes 1-5 or 7-9) | Halt and report per `references/email-spec.md` § Exit Code Handling. **Never** delete or modify any local `.md` / `.docx`. **Never** fall back to inline SMTP — the PreToolUse hook will reject it anyway. |

## References

| File | Contents | Consumed by |
|------|----------|-------------|
| `references/schemas.md` | Scanner Bundle Schema (all categories), Verifier Output Schema | Scanner, Verifier |
| `references/rubric.md` | Adaptive Source Discovery Model, Source Eligibility, Geographic and China external-view gates, contextual Editorial Selection Rubric, Coverage Review, Date Verification Rules, Category Coverage Rules, Conditional and Topical Categories | Scanner, Verifier |
| `references/output-spec.md` | Required Markdown Output, Markdown Syntax Contract, Invalid + Valid examples (`lang=en`, `lang=zh`), APA 7th Reference Format | Writer |
| `references/language-spec.md` | Localisation Table, Derived Display Fields, Filename Pattern, Language Rules, Title Length Rules, Body Length Rules, Writing Standard, **Language-Specific Rules — `lang=zh` only** (quote marks, official titles, country prefixes, time anchors, terminology precision, foreign media naming) | Writer |
| `references/verification.md` | Output Rules, Writer Self-Check, End-to-End Verification, Flow Diagram, Recommended Agent Assignment, Invocation Examples | Writer (self-check), Orchestrator (delivery check) |
| `references/email-spec.md` | Email subject / body templates, env var contract, attachment selection, exit-code handling, security | Orchestrator (Step 10 only when `email` is set) |

## Invocation Examples

```
$sci-research:daily-news-intelligence --country "Japan" --date 2026-04-14 --lang zh
$sci-research:daily-news-intelligence --country "United Kingdom" --date 2026-04-14 --lang en --min-per-category 3
$sci-research:daily-news-intelligence --country "Germany" --lang ja
$sci-research:daily-news-intelligence --country "China"

# With email delivery
$sci-research:daily-news-intelligence --country "China" --email "you@gmail.com"
$sci-research:daily-news-intelligence --country "Japan" --email "a@x.com,b@y.com" --email-attach docx
$sci-research:daily-news-intelligence --country "UK" --lang en --email "you@gmail.com" --email-dry-run

# Bilingual mode (1.18.0+) — 4 attachments (zh+en md + docx) + stacked zh+en email body
$sci-research:daily-news-intelligence --country "China" --lang zh+en --email "boss@company.com"
$sci-research:daily-news-intelligence --country "Japan" --lang en+zh --email "you@gmail.com" --email-attach docx
$sci-research:daily-news-intelligence --country "Germany" --lang zh+ja --email "you@gmail.com" --email-dry-run
```
