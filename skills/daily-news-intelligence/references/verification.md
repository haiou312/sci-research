# Verification — Output Rules, End-to-End Check, Flow Diagram, Agent Assignment

Loaded at the end of the workflow (Writer self-check + orchestrator delivery check) and during initial setup (agent assignment).

## Output Rules

- Output only the final Markdown report to `out_md` via the `Write` tool.
- The first non-whitespace character of the file must be `#`.
- Exactly `len(active_categories)` H2 section headings must appear (6 for a non-China report, 7 for a China report), in the country-derived order from `references/language-spec.md` § Category Catalog & Selection, before any other H2.
- Every story title line must start with `### `.
- Every references block must occupy its own line and be followed on the next line by a single APA-formatted reference.
- No heading marker may share a line with prose, emphasis, or citations.
- Use `---` as the between-story separator.
- Do not emit a trailing global sources / references list.
- Do not include planning text, tool logs, or preamble in the Markdown file.
- After `Write`, run the `pandoc` export command specified in the skill's Workflow.

## Writer Self-Check (before calling `Write`)

Silently verify all of the following. If any check fails, fix before writing — do not ship a document that fails self-check.

1. First non-whitespace character is `#`.
2. H1 matches `h1_pattern` exactly for the chosen `lang`.
3. The active-category H2 headings appear in order (6 for a non-China report, 7 for a China report; `china_nexus` only for a China report) and each matches its composed value from `references/language-spec.md` § Category Catalog & Selection exactly.
4. Every story title line starts with `### ` and satisfies the Title Length Rules for `lang`.
5. Every `**References**` line is followed on the next line by a single APA 7th reference: `Author. (Year, Month Day). Title. Outlet. https://...`
6. No Markdown link syntax `[text](url)` appears anywhere in the document.
7. No alternative reference formats: no `来源：` blocks, no `（来源：...）` inline citations, no bullet-list URLs, no global reference section at the end.
8. Every category either has `min_per_category` stories or carries a single italic `gap_note` line.
9. **No `**摘要**` / `**Summary**` / `**要約**` / `**分析**` / `**Analysis**` markers anywhere** — body prose follows `### title` directly.
10. Every URL in the references block traces to the Verifier KEEP set (Lead or Corroborated by). No search-derived URLs admitted.

When `lang=zh`, additionally verify that the output complies with every rule in `references/language-spec.md` § Language-Specific Rules — `lang=zh` only. That document is the single source of truth for zh-specific writing rules (quote marks, official titles, country prefixes, time anchors, terminology, foreign media naming).

## End-to-End Verification (after pandoc export)

Run from the skill orchestrator:

```bash
ls -la "{out_md}" "{out_docx}"
```

Both files must exist. Then spot-check the Markdown:

1. `grep -c '^## ' {out_md}` should return `6` for a non-China report and `7` for a China report (= `len(active_categories)`).
2. `grep -c '^### ' {out_md}` should return at least `len(active_categories) × min_per_category` (≥ `6 × min` for a non-China report, ≥ `7 × min` for a China report).
3. Pick one story at random, open its URL, confirm the publication date equals `date`.
4. Confirm every references line matches `^<Org|Surname>.* \(\d{4}, [A-Z][a-z]+ \d{1,2}\)\. .+\. .+\. https?://`.

## Flow Diagram

```
[User request: country + date + lang]
          │
          ▼
┌────────────────────────────────────────┐
│ Step 2-6: Scanner ×N (parallel,        │
│  one per active category, English)     │
│  Pass A matrix ladder + Pass B free    │
│  WebFetch → per-URL date verification  │
│  Emit N single-category bundles        │
└──────────────────┬─────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────┐
│ Step 6.5: Merger stage                 │
│  Cross-category dedup + china_nexus↔   │
│  ipo_ma routing (no quality judgement) │
│  Emit one unified Merged Bundle        │
└──────────────────┬─────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────┐
│ Step 7: Verifier stage                 │
│  Originality + Authority + Impact +    │
│  Source legitimacy + Dedup-validation  │
│  Two-step fallback on coverage gap     │
│  Emit KEEP set + Dropped list          │
└──────────────────┬─────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────┐
│ Step 8: Writer stage                   │
│  Consume Verifier KEEP set only        │
│  Translate narrative to target lang    │
│  Apply Markdown Syntax Contract        │
│  Write overwrite {out_md}              │
└──────────────────┬─────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────┐
│ Step 9: pandoc export                  │
│  pandoc --extract-media=./media ...    │
└──────────────────┬─────────────────────┘
                   │
                   ▼
           [{out_md} + {out_docx}]
```

## Recommended Agent Assignment

| Stage | Recommended subagent | Model | Rationale |
|-------|----------------------|-------|-----------|
| Scanner ×N (parallel, one per active category) | `sci-research:daily-news-scanner` | sonnet | Purpose-built single-date, single-category scanner. Pass A walks tier order (T4-official → T1-wire → T1-flagship → T2 → T3); Pass B is free discovery under § Source Legitimacy. Strict per-URL WebFetch date verification — publication date must equal `date` exactly, no neighbouring days. Do NOT substitute `sci-research:news-scanner` — that agent uses time windows (7d/30d/90d) and lacks single-date enforcement |
| Merger | `sci-research:daily-news-merger` | sonnet | Purpose-built merge/route stage. Consumes the N single-category bundles, performs cross-category dedup + the `china_nexus`↔`ipo_ma` routing tie-break only — no quality judgement. Do NOT fold into the Verifier; keeping it separate stops the Verifier from overloading |
| Verifier | `sci-research:news-verifier` | sonnet | Purpose-built news-desk filter encoding the five-check rubric (Originality / Authority / Impact / Source legitimacy / Dedup-validation) and two-step coverage fallback; consumes the Merged Bundle. Do NOT substitute `fact-checker` — fact-checker grades factual truth (Verified / Disputed), not editorial news value |
| Writer | `sci-research:daily-news-writer` | opus | Purpose-built daily briefing writer. System prompt encodes the Localisation Table, Category Catalog & country-derived active-category ordering, Markdown Syntax Contract, APA 7th format, Writing Standard, and self-check protocol. Do NOT substitute `news-analyst` — news-analyst runs its own dedup/impact analysis which is redundant with (and potentially contradicts) the Verifier's KEEP set. Do NOT substitute `writer` — writer's default output is a scientific popular-science article structure |

The skill does not hard-code subagent types — `general-purpose` can stand in for any stage if the above agents are unavailable. When substituting, the skill prompt still governs behaviour; the dedicated agents are preferred only because their system prompts reduce prompt-surface required on every invocation.

## Invocation Examples

```
/daily-news-intelligence --country "Japan" --date 2026-04-14 --lang zh
/daily-news-intelligence --country "United Kingdom" --date 2026-04-14 --lang en --min-per-category 3
/daily-news-intelligence --country "Germany" --lang ja
/daily-news-intelligence --country "China"
```
