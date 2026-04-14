# Verification — Output Rules, End-to-End Check, Flow Diagram, Agent Assignment

Loaded at the end of the workflow (Writer self-check + orchestrator delivery check) and during initial setup (agent assignment).

## Output Rules

- Output only the final Markdown report to `out_md` via the `Write` tool.
- The first non-whitespace character of the file must be `#`.
- Exactly five H2 section headings must appear, in the fixed order, before any other H2.
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
3. Five H2 headings appear in order and match their Localisation Table values exactly.
4. Every story title line starts with `### ` and satisfies the Title Length Rules for `lang`.
5. Every references marker line is followed on the next line by a single APA 7th reference.
6. No Markdown link syntax `[text](url)` appears anywhere in the document.
7. Every category either has `min_per_category` stories or carries a single italic `gap_note` line.
8. `analysis_marker` never appears with an empty body.

## End-to-End Verification (after pandoc export)

Run from the skill orchestrator:

```bash
ls -la "{out_md}" "{out_docx}"
```

Both files must exist. Then spot-check the Markdown:

1. `grep -c '^## ' {out_md}` should return `5`.
2. `grep -c '^### ' {out_md}` should return at least `5 × min_per_category`.
3. Pick one story at random, open its URL, confirm the publication date equals `date`.
4. Confirm every references line matches `^<Org|Surname>.* \(\d{4}, [A-Z][a-z]+ \d{1,2}\)\. .+\. .+\. https?://`.

## Flow Diagram

```
[User request: country + date + lang]
          │
          ▼
┌────────────────────────────────────────┐
│ Step 2-6: Scanner stage (English only) │
│  English WebSearch → candidate URLs    │
│  WebFetch → per-URL date verification  │
│  T1-T4 filter + 5-category coverage    │
│  Emit English raw data bundle          │
└──────────────────┬─────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────┐
│ Step 7: Verifier stage                 │
│  Originality + Authority + Impact      │
│  Dedup (Lead vs Corroboration)         │
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
| Scanner | `sci-research:news-scanner` | sonnet | WebSearch + WebFetch + built-in source-tier awareness, 50/50 official/media balance, rewrite tracing, dedup protocol — directly matches the Scanner stage contract |
| Verifier | `sci-research:news-verifier` | sonnet | Purpose-built news-desk filter encoding Originality / Authority / Impact / Dedup rubric and two-step coverage fallback. Do NOT substitute `fact-checker` — fact-checker grades factual truth (Verified / Disputed), not editorial news value |
| Writer | `sci-research:daily-news-writer` | opus | Purpose-built daily briefing writer. System prompt encodes the Localisation Table, Markdown Syntax Contract, APA 7th format, five-category ordering, Writing Standard, and self-check protocol. Do NOT substitute `news-analyst` — news-analyst runs its own dedup/impact analysis which is redundant with (and potentially contradicts) the Verifier's KEEP set. Do NOT substitute `writer` — writer's default output is a scientific popular-science article structure |

The skill does not hard-code subagent types — `general-purpose` can stand in for any stage if the above agents are unavailable. When substituting, the skill prompt still governs behaviour; the dedicated agents are preferred only because their system prompts reduce prompt-surface required on every invocation.

## Invocation Examples

```
/daily-news-intelligence --country "Japan" --date 2026-04-14 --lang zh
/daily-news-intelligence --country "United Kingdom" --date 2026-04-14 --lang en --min-per-category 3
/daily-news-intelligence --country "Germany" --lang ja
/daily-news-intelligence --country "China"
```
