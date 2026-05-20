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

**Scope.** This is the **procedure-level** self-check the Writer agent runs before invoking `Write`. The **format-level checksum** (counted invariants like `grep -c '^## '` and `[N]` continuity) lives in `references/output-spec.md` § Self-Check Checksum and is enforced by the `daily-news-format-check` hook on every Write/Edit. If the two lists ever disagree, this list defines intent and output-spec.md defines the machine check; bring them into sync rather than picking a winner.

Silently verify all of the following. If any check fails, fix before writing — do not ship a document that fails self-check.

1. First non-whitespace character is `#`.
2. H1 matches `h1_pattern` exactly for the chosen `lang` (see `references/language-spec.md` § Localisation Table).
3. The active-category H2 headings appear in order (6 for a non-China report, 7 for a China report; `china_nexus` only for a China report) and each matches its composed value from `references/language-spec.md` § Category Catalog & Selection exactly.
4. Every story title line starts with `### ` and satisfies the Title Length Rules for `lang` (see `references/language-spec.md` § Title Length Rules).
5. Every `**References**` line is followed on the next line by a single APA 7th reference: `Author. (Year, Month Day). Title. Outlet. https://...` (see `references/output-spec.md` § APA 7th Reference Format).
6. No Markdown link syntax `[text](url)` appears anywhere in the document (see `references/output-spec.md` § Markdown Syntax Contract).
7. No alternative reference formats: no `来源：` blocks, no `（来源：...）` inline citations, no bullet-list URLs, no global reference section at the end.
8. Every category either has `min_per_category` stories or carries a single italic `gap_note` line whose text comes from `references/language-spec.md` § Localisation Table.
9. **No `**摘要**` / `**Summary**` / `**要約**` / `**分析**` / `**Analysis**` markers anywhere** — body prose follows `### title` directly. (Prohibited-marker list in `references/output-spec.md` § Markdown Syntax Contract.)
10. Every URL in the references block traces to the Verifier KEEP set (Lead or Corroborated by) **or** to a search URL whose content supplied a body fact (per Writer's citation contract — `agents/daily-news-writer.md` § Citation contract). Search-derived URLs that did **not** back a body fact MUST NOT appear.

When `lang=zh`, additionally verify that the output complies with every rule in `references/language-spec.md` § Language-Specific Rules — `lang=zh` only. That document is the single source of truth for zh-specific writing rules (quote marks, official titles, country prefixes, time anchors, terminology, foreign media naming).

## End-to-End Verification (after pandoc export)

Run from the skill orchestrator:

```bash
ls -la "{out_md}" "{out_docx}"
```

Both files must exist. Then spot-check the Markdown:

1. `grep -c '^## ' "{out_md}"` should return `6` for a non-China report and `7` for a China report (= `len(active_categories)`).
2. `grep -c '^### ' "{out_md}"` should return at least `len(active_categories) × min_per_category` (≥ `6 × min` for a non-China report, ≥ `7 × min` for a China report).
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
│  Three-step fallback on coverage gap   │
│  (1 impact / 1.5 reserve-pool / 2 gap) │
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
│ Step 8.5: Editor stage (5 passes)      │
│  1 Verifier-locked fact verification   │
│  2 Writer-search fact backing          │
│    (may add refs, renumber [N])        │
│  3 Quote verbatim check                │
│  4 Quote-mark normalization            │
│  5 Local fluency / logic-gap repair    │
│    (5-class defect whitelist; no web)  │
│  Edit only; rollback on invariant      │
│  failure; aborts gracefully            │
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

**Dispatch rule (mandatory, permanent).** Every stage spawns as the built-in **`general-purpose`** subagent with the corresponding `agents/<name>.md` **body embedded in the prompt** and an **explicit `model` arg**. `subagent_type: sci-research:*` is **forbidden for execution** — marketplace-plugin subagents do not receive `WebSearch` / `WebFetch` at runtime (anthropics/claude-code#21318, closed as "not planned"), even if their frontmatter declares those tools. See `skills/daily-news-intelligence/SKILL.md` § Subagent Dispatch Rule for the full rationale. The names below refer to the **prompt-template files** in `agents/`, not to registered subagents.

| Stage | Dispatch | Model | Rationale (the embedded body encodes this) |
|-------|----------|-------|--------------------------------------------|
| Scanner ×N (parallel, one per active category) | `general-purpose` + embed `agents/daily-news-scanner.md` body | `sonnet` | Single-date, single-category scanner. Pass A walks tier order (T4-official → T1-wire → T1-flagship → T2 → T3); Pass B is free discovery under § Source Legitimacy. Strict per-URL WebFetch date verification — publication date must equal `date` exactly, no neighbouring days. Do NOT embed `agents/news-scanner.md` — that agent uses time windows (7d/30d/90d) and lacks single-date enforcement |
| Merger | `general-purpose` + embed `agents/daily-news-merger.md` body | `sonnet` | Merge/route stage. Consumes the N single-category bundles, performs cross-category dedup + the `china_nexus`↔`ipo_ma` routing tie-break only — no quality judgement. Do NOT fold into the Verifier; keeping it separate stops the Verifier from overloading |
| Verifier | `general-purpose` + embed `agents/news-verifier.md` body | `sonnet` | News-desk filter encoding the five-check rubric (Originality / Authority / Impact / Source legitimacy / Dedup-validation) and the three-step coverage fallback (impact relaxation / reserve-pool promotion / gap record); consumes the Merged Bundle including its Reserve Pool. Do NOT embed `agents/fact-checker.md` — fact-checker grades factual truth (Verified / Disputed), not editorial news value |
| Fact-Extractor | `general-purpose` + embed `agents/daily-fact-extractor.md` body | `sonnet` | Extracts every hard fact + direct quote from the Verifier KEEP set into a locked-values YAML manifest. Pure transformation — no web, no narrative. The manifest is the Writer's locked-values contract and the Editor's Pass-1 ground truth |
| Writer | `general-purpose` + embed `agents/daily-news-writer.md` body | `opus` | Daily briefing writer. Body encodes the Localisation Table, Category Catalog & country-derived active-category ordering, Markdown Syntax Contract, APA 7th format, Writing Standard, search-for-background contract, citation contract (search URLs that supplied a body fact MUST be in References), and self-check protocol. Do NOT embed `agents/news-analyst.md` — it runs its own dedup/impact analysis which contradicts the Verifier's KEEP set. Do NOT embed `agents/writer.md` — that body emits a scientific popular-science article structure |
| Editor | `general-purpose` + embed `agents/daily-editor.md` body | `opus` | Five-pass editor (fact verification / search-backing / quote verbatim / quote-mark normalization / local-fluency repair). Uses `Edit` only, never `Write`. Pass 5 is style-only with closed defect-class whitelist and six rollback invariants; aborts gracefully without blocking the pipeline |

**Substitution.** Do NOT substitute any other agent's body — each body encodes stage-specific invariants (e.g., daily-news-scanner's strict single-date gate, daily-editor's no-`Write` discipline) that are not present in the closest-named alternative agents. If a body file is missing, halt and report rather than substituting.

## Invocation Examples

```
/daily-news-intelligence --country "Japan" --date 2026-04-14 --lang zh
/daily-news-intelligence --country "United Kingdom" --date 2026-04-14 --lang en --min-per-category 3
/daily-news-intelligence --country "Germany" --lang ja
/daily-news-intelligence --country "China"
```
