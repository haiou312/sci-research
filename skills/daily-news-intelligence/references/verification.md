# Verification — Output Rules, End-to-End Check, Flow Diagram, Agent Assignment

Loaded at the end of the workflow (Writer self-check + orchestrator delivery check) and during initial setup (agent assignment).

## Output Rules

- Output only the final Markdown report to `out_md` via one `apply_patch` operation.
- The first non-whitespace character of the file must be `#`.
- Exactly `len(active_categories)` H2 section headings must appear (6 for a non-China report, 7 for a China report), in the country-derived order from `references/language-spec.md` § Category Catalog & Selection, before any other H2.
- Every story title line must start with `### `.
- Every references block must occupy its own line and be followed on the next line by a single APA-formatted reference.
- No heading marker may share a line with prose, emphasis, or citations.
- Use `---` as the between-story separator.
- Do not emit a trailing global sources / references list.
- Do not include planning text, tool logs, or preamble in the Markdown file.
- After `apply_patch`, run the `pandoc` export command specified in the skill's Workflow.

## Writer Self-Check (before calling `apply_patch`)

**Scope.** This is the **procedure-level** self-check the Writer agent runs before invoking `apply_patch`. The **format-level checksum** (counted invariants like `grep -c '^## '` and `[N]` continuity) lives in `references/output-spec.md` § Self-Check Checksum and is enforced by the `daily-news-format-check` hook on every `apply_patch`. If the two lists ever disagree, this list defines intent and output-spec.md defines the machine check; bring them into sync rather than picking a winner.

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
10. Every URL in the references block traces to the Verifier KEEP set (Lead or Corroborated by) **or** to a search URL whose content supplied a body fact (per Writer's citation contract — `.codex/agents/sci-research-daily-news-writer.toml` § Citation contract). Search-derived URLs that did **not** back a body fact MUST NOT appear.
11. **Body length**: every `lang=en` story body contains 250–350 English words and aims near 300; every `lang=zh` story body contains 450–550 Unicode Han characters and aims near 500. Count only text between `### <title>` and `**References**` per `references/language-spec.md` § Body Length Rules. `lang=ja` has no fixed body-length band.

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
│ Step 2: Scanner (single agent, all     │
│  active categories sequentially)       │
│  Adaptive broad source discovery       │
│  Candidate buffer beyond final minimum │
│  WebSearch open_page → per-URL date    │
│  verification                           │
│  Cross-category dedup + routing        │
│  china_nexus↔ipo_ma routing            │
│  Emit one unified Scanner Bundle       │
└──────────────────┬─────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────┐
│ Step 7: Verifier stage                 │
│  Credibility + New information +       │
│  Contextual news value + Dedup          │
│  Coverage Review for short categories  │
│  Emit KEEP set + Dropped list          │
└──────────────────┬─────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────┐
│ Step 8: Writer stage                   │
│  Consume Verifier KEEP set only        │
│  Translate narrative to target lang    │
│  Apply Markdown Syntax Contract        │
│  apply_patch overwrite {out_md}        │
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
│  apply_patch only; rollback on invariant│
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

**Dispatch rule.** Every stage runs as its exact installed `sci-research-*` native Codex custom agent with `fork_turns="none"`; the selected role's `model` + `model_reasoning_effort` come from its TOML. See `skills/daily-news-intelligence/SKILL.md` § Subagent Dispatch Rule. A generic-agent or embedded-prompt fallback is forbidden.

| Stage | Dispatch | Model | Rationale (the embedded body encodes this) |
|-------|----------|-------|--------------------------------------------|
| Scanner (single agent, all active categories sequentially) | `.codex/agents/sci-research-daily-news-scanner.toml` subagent | `gpt-5.6-luna / medium` | Single-date scanner across all active categories. Searches adaptively without a fixed outlet list, prefers official primary and accountable established/regional/specialist sources, targets a broad candidate buffer, verifies every URL's exact date and geography, and performs cross-category dedup + `china_nexus`↔`ipo_ma` routing before emitting the Scanner Bundle |
| Verifier | `.codex/agents/sci-research-news-verifier.toml` subagent | `gpt-5.6-terra / high` | News-desk filter encoding source credibility/evidence fit, concrete new information, contextual daily-news value, originality/corroboration, and dedup/category validation. Coverage Review may admit credible narrower developments when a category is short, without relaxing date, geography, provenance, or factual support |
| Fact-Extractor | `.codex/agents/sci-research-daily-fact-extractor.toml` subagent | `gpt-5.4-mini / medium` | Extracts every hard fact + direct quote from the Verifier KEEP set into a locked-values YAML manifest. Pure transformation — no web, no narrative. The manifest is the Writer's locked-values contract and the Editor's Pass-1 ground truth |
| Writer | `.codex/agents/sci-research-daily-news-writer.toml` subagent | `gpt-5.6-sol / high` | Daily briefing writer. Body encodes the Localisation Table, Category Catalog & country-derived active-category ordering, Markdown Syntax Contract, APA 7th format, Writing Standard, search-for-background contract, citation contract (search URLs that supplied a body fact MUST be in References), and self-check protocol |
| Editor | `.codex/agents/sci-research-daily-editor.toml` subagent | `gpt-5.6-sol / high` | Five-pass editor (fact verification / search-backing / quote verbatim / quote-mark normalization / local-fluency repair). Uses `apply_patch` only. Pass 5 is style-only with closed defect-class whitelist and six rollback invariants; aborts gracefully without blocking the pipeline |

**Substitution.** Do NOT substitute any other agent's body — each body encodes stage-specific invariants (e.g., the Scanner's strict single-date gate and the Editor's `apply_patch`-only discipline) that are not present in the closest-named alternative agents. If a named role is unavailable, halt and report rather than substituting.

## Invocation Examples

```
$sci-research:daily-news-intelligence --country "Japan" --date 2026-04-14 --lang zh
$sci-research:daily-news-intelligence --country "United Kingdom" --date 2026-04-14 --lang en --min-per-category 3
$sci-research:daily-news-intelligence --country "Germany" --lang ja
$sci-research:daily-news-intelligence --country "China"
```
