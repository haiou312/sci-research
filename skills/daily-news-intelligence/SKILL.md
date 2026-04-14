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
| `out_dir` | No | `/Users/peterwang/Desktop/deep-research/` | Absolute output directory with trailing slash |
| `min_per_category` | No | `2` | Minimum stories per category |

Derived fields (`date_en`, `date_display`, `country_display`, `out_md`, `out_docx`) are computed per `lang` — see `references/language-spec.md`.

## Workflow

1. **Validate scope.** Normalize `country` for English search and target-language rendering. Default `date` to today if omitted. Build all derived fields via `references/language-spec.md`.

2. **Scan candidates** (Scanner stage, English only). Generate at least three distinct query patterns per category. Collect 20-30 candidate URLs across the five fixed categories. Prioritise breadth over depth.

3. **Verify each candidate.** For every candidate URL, call `web_fetch` and extract the publication date. Apply the rules in `references/rubric.md` § Date Verification Rules — keep only stories where publication date equals `date` (local or UTC match).

4. **Apply tier filter.** Keep only T1-T4 sources per `references/rubric.md` § Source Tier Rules.

5. **Enforce category coverage.** If any category has fewer than `min_per_category`, run a second search pass scoped to that category. If still insufficient, record the gap — do not substitute low-tier sources.

6. **Compose the Scanner output.** Return a single English data bundle matching `references/schemas.md` § Scanner Output Schema.

7. **Second-pass filter** (Verifier stage). Consume the Scanner bundle and apply the four-check rubric in `references/rubric.md` § Authority & Impact Rubric (originality, authority, impact, dedup). Apply the two-step fallback if any category drops below `min_per_category`. Emit the Verifier Output Schema from `references/schemas.md`.

8. **Translate and write the report** (Writer stage). Consume the Verifier's KEEP set only. Translate narrative into `lang` per `references/language-spec.md`. Produce Markdown obeying `references/output-spec.md`. Use the `Write` tool to overwrite `out_md`.

9. **Export to Word.** Run:
   ```bash
   pandoc --extract-media=./media "{out_md}" -o "{out_docx}"
   ```
   Working directory must be `out_dir` so `--extract-media` resolves cleanly.

10. **Verify delivery.** Apply the checks in `references/verification.md` § End-to-End Verification.

## Stage → Agent → Reference Map

| Stage | Recommended Agent | Required References |
|-------|-------------------|---------------------|
| Scanner | `sci-research:news-scanner` (sonnet) | `references/rubric.md`, `references/schemas.md` |
| Verifier | `sci-research:news-verifier` (sonnet) | `references/rubric.md`, `references/schemas.md` |
| Writer | `sci-research:daily-news-writer` (opus) | `references/language-spec.md`, `references/output-spec.md`, `references/verification.md` |
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

## Invocation Examples

```
/daily-news-intelligence --country "Japan" --date 2026-04-14 --lang zh
/daily-news-intelligence --country "United Kingdom" --date 2026-04-14 --lang en --min-per-category 3
/daily-news-intelligence --country "Germany" --lang ja
/daily-news-intelligence --country "China"
```
