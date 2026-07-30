# Verification — Output Rules, End-to-End Check, Flow Diagram, Agent Assignment

Loaded at the end of the workflow (Writer self-check + orchestrator delivery check) and during initial setup (agent assignment).

## Output Rules

- Output only the final Markdown report to `out_md`. Create it with `apply_patch`; use focused follow-up patches if self-check or the format hook finds a defect.
- The first non-whitespace character of the file must be `#`.
- Exactly `len(active_categories)` H2 section headings must appear (6 for a non-China report, 7 for a China report), in the country-derived order from `references/language-spec.md` § Category Catalog & Selection, before any other H2.
- Every story title line must start with `### `.
- Every references block must occupy its own line and be followed by one or more APA-formatted references.
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
4. Every story title line starts with `### ` and is a natural, logically coherent single-line newsroom headline for `lang` (see `references/language-spec.md` § Title Length Rules). For `zh` and `en`, multi-clause titles use `，` and `, ` respectively, never bare whitespace or another separator; any causal connection is supported by retained evidence.
5. Every `**References**` line is followed by one or more APA 7th references: `[N] Author. (Year, Month Day). Title. Outlet. https://...` (see `references/output-spec.md` § APA 7th Reference Format).
6. No Markdown link syntax `[text](url)` appears anywhere in the document (see `references/output-spec.md` § Markdown Syntax Contract).
7. No alternative reference formats: no `来源：` blocks, no `（来源：...）` inline citations, no bullet-list URLs, no global reference section at the end.
8. Every category either has `min_per_category` stories or carries a single italic `gap_note` line whose text comes from `references/language-spec.md` § Localisation Table.
9. **No `**摘要**` / `**Summary**` / `**要約**` / `**分析**` / `**Analysis**` markers anywhere** — body prose follows `### title` directly. (Prohibited-marker list in `references/output-spec.md` § Markdown Syntax Contract.)
10. Every URL in the references block is a publisher `canonical_url` returned for a Verifier story, a last-resort Google News discovery URL when canonicalization failed, or a canonical URL whose `get_news_article` full text supplied a body fact (per the Writer citation contract). Supplemental URLs whose returned full text did **not** back a body fact MUST NOT appear.
11. **Body length and depth**: every `en` story has at least 250 English words and every `zh` story has at least 400 Unicode Han characters, counted per `references/language-spec.md` § Body Length Standard. There is no maximum. Use full text returned by `google_news.get_news_article` to add relevant substance; never pad, preserve an unnecessary English gloss, repeat content, or invent context to meet the floor.

For every language, verify native composition under `references/language-spec.md` § Language Rules and § Writing Standard. When `lang=zh`, also apply the Chinese conventions in that document for quote marks, official titles, country prefixes, time anchors, terminology, and foreign media naming.

## End-to-End Verification (after pandoc export)

Run from the skill orchestrator:

```bash
ls -la "{out_md}" "{out_docx}"
```

Both files must exist. Then spot-check the Markdown:

1. `grep -c '^## ' "{out_md}"` should return `6` for a non-China report and `7` for a China report (= `len(active_categories)`).
2. `grep -c '^### ' "{out_md}"` must equal the Verifier's `Kept count`. A category below `min_per_category` after deduplication must carry its localized gap note.
3. Pick one story at random and confirm its URL, source, displayed search-result date, and summary trace to the saved Scanner audit. Do not require the URL to open.
4. Confirm every references line matches `^<Org|Surname>.* \(\d{4}, [A-Z][a-z]+ \d{1,2}\)\. .+\. .+\. https?://`.

Also inspect `SCANNER_AUDIT` before delivery:

1. It contains exactly one `<!-- BEGIN CATEGORY OUTPUT: <id> -->` block per active category, in active-category order.
2. Every category block contains `Status: complete`, the matching `Searched category`, and a candidate count equal to its story blocks.
3. Every story contains a category-prefixed Candidate ID, `Publish date (search result)`, `Source`, `URL`, and `Search-result summary`; `URL` is the `google_news_url` returned by `search_news` and may be either a raw URL or a Markdown link. URL presentation and the `news.google.com` domain are not failures, and the story must not claim that the publisher article was fetched or verified.
4. The Scanner Batch header totals equal the sum of the verbatim category outputs.

Also inspect `VERIFIER_AUDIT` before delivery:

1. `Input count = Kept count + Duplicate count`.
2. Every Scanner Candidate ID appears exactly once, either as a retained `Candidate ID` or a `DROP_DUPLICATE` heading.
3. Every duplicate points directly to a retained Candidate ID; there are no duplicate chains.
4. Retained representatives keep their first-occurrence input order and searched category.
5. The only DROP verdict is `DROP_DUPLICATE`; unique events are never dropped.

## Flow Diagram

```
[User request: country + date + lang]
          │
          ▼
┌────────────────────────────────────────┐
│ Step 2: Scanner fan-out                │
│  One GPT-5.6 Terra per active category │
│  All category agents run concurrently  │
│  One category direction per prompt     │
│  One-sentence google_news search prompt │
│  Return results without fetching text   │
│  No verification, filtering, or dedup   │
└──────────────────┬─────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────┐
│ Orchestrator: mechanical Scanner Batch │
│  Preserve every category output        │
│  verbatim in active-category order     │
│  Calculate header totals only          │
│  No Merger agent or editorial changes  │
└──────────────────┬─────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────┐
│ Step 7: Deduplication-only Verifier    │
│  No web or MCP tools                   │
│  Keep first report of each event       │
│  DROP_DUPLICATE later same-event items │
└──────────────────┬─────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────┐
│ Step 8: Writer stage                   │
│  Consume Verifier KEEP set only        │
│  Re-search + get_news_article for text │
│  Compose native target-language prose  │
│  Apply Markdown Syntax Contract        │
│  apply_patch overwrite {out_md}        │
└──────────────────┬─────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────┐
│ Step 8.5: Editor stage (5 passes)      │
│  1 Manifest semantic fact fidelity     │
│  2 MCP full-text source backing        │
│    (may add refs, renumber [N])        │
│  3 Quote meaning and attribution       │
│  4 Structure, refs, and typography     │
│  5 Full native-language editorial pass │
│    Chinese / English / Japanese        │
│  apply_patch only; preserve facts,     │
│  evidence, categories, and structure   │
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
| Scanner × active category (parallel) | `.codex/agents/sci-research-daily-news-scanner.toml` subagent | `gpt-5.6-terra / high` | Each instance receives one search sentence after the runtime header, uses only `google_news.search_news`, and returns useful same-day results without fetching, verifying, filtering, scoring, deduplicating, or routing them; China uses foreign media only and Europe excludes UK-focused events |
| Deduplication-only Verifier | `.codex/agents/sci-research-news-verifier.toml` subagent | `gpt-5.6-terra / high` | Uses only Scanner Batch fields, keeps each event's first occurrence in its searched category, marks later same-event reports `DROP_DUPLICATE`, and records post-deduplication coverage gaps; no web tools, verification, scoring, Lead replacement, rerouting, or other DROP reasons |
| Fact-Extractor | `.codex/agents/sci-research-daily-fact-extractor.toml` subagent | `gpt-5.6-luna / medium` | Extracts literal atoms from unverified search-result summaries into a YAML manifest marked `evidence_basis: search-results`; no web, inference, or narrative |
| Writer | `.codex/agents/sci-research-daily-news-writer.toml` subagent | `gpt-5.6-sol / high` | Daily briefing writer. Uses semantic Fact Manifest fidelity, native-language composition, complete citations, and hard minimums of 250 English words or 400 Chinese Han characters. Re-finds stories with `google_news.search_news`, retrieves text with `get_news_article`, and researches further only when necessary to supply relevant depth |
| Editor | `.codex/agents/sci-research-daily-editor.toml` subagent | `gpt-5.6-sol / high` | Five-pass editor for manifest facts, MCP full-text source backing, quotations, structure/typography, and full native-language quality. It repairs thin stories from `get_news_article` evidence and may rewrite awkward prose while preserving the story set, facts, sources, categories, and required structure |

**Substitution.** Do NOT substitute any other agent's body — each body encodes stage-specific invariants (e.g., the Scanner's one-sentence recall-first search and the Editor's `apply_patch`-only discipline) that are not present in the closest-named alternative agents. If a named role is unavailable, halt and report rather than substituting.

## Invocation Examples

```
$sci-research:daily-news-intelligence --country "Japan" --date 2026-04-14 --lang zh
$sci-research:daily-news-intelligence --country "United Kingdom" --date 2026-04-14 --lang en --min-per-category 3
$sci-research:daily-news-intelligence --country "Germany" --lang ja
$sci-research:daily-news-intelligence --country "China"
```
