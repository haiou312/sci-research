# Pipeline C v2 — Architecture Overhaul Plan

**Status**: Proposed — pending approval
**Date drafted**: 2026-05-14
**Target release**: 1.11.0
**Touches**: Pipeline C (`/daily-news-intelligence`) only. Pipelines A/B/D/E/F unaffected.

---

## 1. Problem statement

User-reported failure modes on Pipeline C output:

1. **Number / fact accuracy drifts** in body prose — units, magnitudes, timing inconsistencies between body and source.
2. **Reference completeness gap** — users check the References block and cannot find quotes/claims that appear in body. Root cause: Writer's WebSearch-derived background facts are **by current design** excluded from References ([daily-news-writer.md:12](../skills/daily-news-intelligence/agents/daily-news-writer.md), [:78](../skills/daily-news-intelligence/agents/daily-news-writer.md)).
3. **Quote-mark chaos** — body contains a mix of `""` curly, `""` ASCII, `「」`, and asymmetric pairings. Spec self-contradicts: [daily-news-writer.md:60](../skills/daily-news-intelligence/agents/daily-news-writer.md) localisation table vs. [:190](../skills/daily-news-intelligence/agents/daily-news-writer.md) writing-standard text disagree on en/ja canonical chars.

## 2. Constraint

**Writer keeps WebSearch actions (`search` + `open_page`).** Narrative logical coherence depends on Writer's ability to pull background context. Removing search degrades the dimension the user values most.

## 3. Solution overview

Root cause is one: **Writer alone handles narration and fact-marshalling with no machine-enforceable contract between them.**

Fix is structural:

- **Insert two new agents** — `daily-fact-extractor` (between Verifier and Writer) and `daily-editor` (between Writer and Hook).
- **Reverse one Writer rule** — search URLs that support body facts MUST enter References.
- **Kill the quote-mark spec contradiction** — pick canonical chars per lang and enforce in hook.

Each layer has a clear, mechanically checkable input/output contract.

### 3.1 Pipeline diff

```
OLD:
  Scanner ──► Verifier ──► Writer ──► Hook ──► docx ──► email
              (KEEP set)   (search+      (format
                            cite)         check)

NEW:
  Scanner ──► Verifier ──► Fact-Extractor ──► Writer ──► Editor ──► Hook ──► docx ──► email
              (KEEP set)   (Fact Manifest)   (search+    (verify+    (format+
                                              cite —     patch)      quote-mark
                                              new rule)              check)
```

### 3.2 Responsibility matrix (new)

| Agent | Reads | Writes | Searches | Fact authority |
|---|---|---|---|---|
| Scanner | web | candidate set | yes | none |
| Verifier | candidates | KEEP/DROP bundle | spot-check fetches | filters, doesn't introduce |
| **Fact-Extractor (new)** | KEEP bundle | **Fact Manifest YAML** | **no** | extracts atoms from Verifier output only |
| Writer | KEEP bundle + Fact Manifest | draft MD | **yes — full** | adds background; **must cite search URLs in References** (rule change) |
| **Editor (new)** | draft MD + Fact Manifest + KEEP bundle | edits MD in place | **yes — verification only** | patches drift; cuts unverifiable claims; never invents |
| Hook | final MD | exit code | no | mechanical format gate |

---

## 4. The five PRs

Each PR is independently mergeable and reversible. Recommended order:

| # | Title | Risk | LOC | Why this order |
|---|---|---|---|---|
| 1 | Quote spec钉死 + hook 字符级阻断 | Low | ~100 | Decoupled fix; high-value, low-blast-radius |
| 2 | Writer 引用规则反转 | Med | ~80 | Single-rule reversal; behavior change but surface area small |
| 3 | daily-fact-extractor + Fact Manifest schema | Med | ~400 | New agent + new artifact + SKILL editing |
| 4 | daily-editor | Med | ~500 | Largest prompt; depends on #3 manifest |
| 5 | Hook reference-completeness heuristic | Low | ~100 | Belt-and-braces backstop |

PR #1 can ship alone and already removes 1 of 3 reported pain points.
PR #2 ships next and removes the second pain point (reference completeness).
PR #3-#5 together address the first pain point (number accuracy) end-to-end.

---

## 5. Component specs

### 5.1 PR #1 — Quote spec钉死 + hook 字符级阻断

#### 5.1.1 Canonical spec

Insert into [skills/daily-news-intelligence/references/language-spec.md](../skills/daily-news-intelligence/references/language-spec.md) (replacing the current `quote_marks` row in the Localisation Table and any conflicting text downstream):

> **Quote-mark canonical chars** (mandatory; mixed forms blocked by hook):
>
> | lang | Open | Close | Codepoints |
> |---|---|---|---|
> | `zh` | `"` | `"` | U+201C, U+201D |
> | `en` | `"` | `"` | U+0022, U+0022 |
> | `ja` | `「` | `」` | U+300C, U+300D |
>
> Any non-canonical quote character in body prose (outside URLs and APA reference lines) is a hard error. The format-check hook detects this and blocks Write.

Rationale for ja using `「」`: native newsroom convention. Forcing ASCII would read as foreign body in Japanese prose.

#### 5.1.2 Writer spec cleanup

Delete the contradictory line in [skills/daily-news-intelligence/agents/daily-news-writer.md:60](../skills/daily-news-intelligence/agents/daily-news-writer.md) (the `quote_marks` row showing identical `""` for all three langs) — replace with reference to the language-spec canonical table.

Delete the contradictory parenthetical in [:190](../skills/daily-news-intelligence/agents/daily-news-writer.md): `(zh "" curly U+201C/U+201D; en/ja ASCII "" — never 「」)` — this conflicts with the new ja convention.

New Writer rule (replaces both):

> Quote marks follow the canonical table in `references/language-spec.md`. Body prose uses only the lang's canonical open/close pair. Mixing forms or using ASCII in zh / curly in en / ASCII or curly in ja is a hook violation.

#### 5.1.3 Hook upgrade

Modify [scripts/hooks/daily-news-format-check.js](../scripts/hooks/daily-news-format-check.js):

```javascript
// NEW: detect lang from H1
function detectLang(content) {
  const m = content.match(/^# .+?(每日热点新闻|Daily News Intelligence|デイリーニュース)/m);
  if (!m) return null;
  if (m[1] === "每日热点新闻") return "zh";
  if (m[1] === "Daily News Intelligence") return "en";
  if (m[1] === "デイリーニュース") return "ja";
  return null;
}

// NEW: validate quote marks
function validateQuoteMarks(content, lang) {
  const violations = [];
  // strip URLs (entire APA ref lines) and inline URLs from check
  const stripped = content
    .replace(/^\[\d+\].*$/gm, "")             // APA ref lines
    .replace(/https?:\/\/\S+/g, "")           // any leftover URLs
    .replace(/`[^`]+`/g, "");                 // inline code spans

  const forbiddenByLang = {
    zh: /["「」]/g,                            // ASCII " and corner brackets
    en: /[“”「」]/g,        // curly and corner brackets
    ja: /["“”]/g,                   // ASCII " and curly
  };

  const hits = stripped.match(forbiddenByLang[lang]);
  if (hits) {
    const unique = [...new Set(hits)];
    const codepoints = unique
      .map(c => `U+${c.codePointAt(0).toString(16).toUpperCase().padStart(4, "0")}`)
      .join(", ");
    violations.push(
      `${hits.length} non-canonical quote char(s) for lang=${lang}: ${codepoints}. ` +
      `Allowed: ${lang === "zh" ? "U+201C / U+201D" : lang === "en" ? "U+0022" : "U+300C / U+300D"}.`
    );
  }

  // Balance check for paired chars (zh and ja)
  if (lang === "zh") {
    const opens = (stripped.match(/“/g) || []).length;
    const closes = (stripped.match(/”/g) || []).length;
    if (opens !== closes) {
      violations.push(`Quote pair imbalance (zh): ${opens} U+201C vs ${closes} U+201D.`);
    }
  }
  if (lang === "ja") {
    const opens = (stripped.match(/「/g) || []).length;
    const closes = (stripped.match(/」/g) || []).length;
    if (opens !== closes) {
      violations.push(`Quote pair imbalance (ja): ${opens} 「 vs ${closes} 」.`);
    }
  }
  return violations;
}

// Inside validate(filePath, content):
const lang = detectLang(content);
if (lang) {
  violations.push(...validateQuoteMarks(content, lang));
}
```

URL-line and inline-code stripping is critical — APA reference lines have URLs that can contain quote-like chars, and table heading rows use backticked code spans.

#### 5.1.4 Tests for PR #1

Manual: feed three known-good past reports (one per lang) through the hook standalone — must all pass. Then inject:
- A single U+201C into an en report body → must block.
- A single ASCII `"` into a zh report body → must block.
- An unbalanced `"`...  in zh → must block with pair imbalance message.
- A `「` inside a URL → must NOT block (URL stripping works).

---

### 5.2 PR #2 — Writer 引用规则反转

#### 5.2.1 Scope

This is a **single-rule reversal** plus surrounding edits to keep the spec coherent. No new agents, no orchestration changes.

#### 5.2.2 Files touched

| File | Change |
|---|---|
| [skills/daily-news-intelligence/agents/daily-news-writer.md](../skills/daily-news-intelligence/agents/daily-news-writer.md) | Reverse search-URL exclusion rule; add "search URLs MUST be cited" rule; update self-check |
| [skills/daily-news-intelligence/references/output-spec.md](../skills/daily-news-intelligence/references/output-spec.md) | Update Reference Format Rules; replace "Search-derived URL in references" prohibition with new policy |
| [skills/daily-news-intelligence/references/rubric.md](../skills/daily-news-intelligence/references/rubric.md) | Mention the new rule in passing if relevant (TBD on read) |

#### 5.2.3 daily-news-writer.md diffs

**Delete** the current restrictions on search URLs (lines indicated are approximate):

- L12: the `URLs you find via search are never written into the References block.` paragraph.
- L78: the `Search-derived facts go into body prose without inline citation; URLs you find never enter the References block.` clause inside Step 2b.
- L84: `Search-derived URLs are NOT added to the References block.` inside Step 2e.
- L210, L251, L284: each remaining instance of `Search-derived URLs are NEVER added` / similar wording.

**Replace with** (new master rule, inserted once near top of Quality Rules and referenced elsewhere):

```
**Citation contract**: References = Verifier KEEP URLs ∪ {every search URL that supplied a fact you wrote in body}.

- Every URL the Verifier delivered (Lead + every Corroborated by URL) MUST appear in References.
- Every search URL you opened to support a body fact MUST appear in References — with proper APA format, the next continuous `[N]` counter, and the original outlet name. This includes URLs you opened only for background context, as long as a number / name / date / quote / institution you wrote in body traces to that URL.
- The ONLY URLs you may open and NOT cite are ones that returned irrelevant content, that you didn't use any fact from, or that duplicate a fact already covered by a cited URL. When in doubt, cite.
- Cap: prefer 1-3 search URLs per story. If you find yourself citing 5+ search URLs for one story, you're over-opening — pick the strongest 2-3 and cut the rest of the background that depended on the weaker ones.
```

#### 5.2.4 output-spec.md diffs

In the Prohibited Formats table ([output-spec.md:65](../skills/daily-news-intelligence/references/output-spec.md), the row `Search-derived URL in references | References = Verifier KEEP set URLs only`):

**Delete this row** entirely.

Add a new section "**Cited Search URLs**" near the end of "Reference Format Rules":

```markdown
### Cited Search URLs

Writer runs supplemental WebSearch `search` + `open_page` actions per story for background context. Any URL that supplied a fact written in body prose is treated as a first-class citation:

- It appears in the story's `**References**` block as an APA reference line with the next continuous `[N]` counter.
- Outlet name comes from the URL's actual publisher.
- Title comes from the source page (use the page's `<title>` or H1, preserved in original English).
- Date is the source publication date.

This is **mandatory** — citing in the body what was researched but not citing in References creates a reference gap visible to readers. Writer is responsible for this; Editor verifies.

Verifier-delivered URLs (Lead + every Corroborated by URL) always appear in References regardless of whether Writer cites them in body.
```

#### 5.2.5 Writer self-check updates

[daily-news-writer.md:235] — the "Self-Check Before Write" list. Replace item 10 ("No search-derived URLs in References") with:

```
10. **References completeness**: every URL in your References block is either a Verifier KEEP URL (Lead or Corroborated by) OR a search URL that supplied a fact in this story's body. No URL is "opened but uncited" if you used a fact from it. No URL is in References that you didn't actually use.
```

#### 5.2.6 Tests for PR #2

Manual: run `/daily-news-intelligence --country Japan --date <past date>` with manifests retained. Compare output:
- Old: 1-2 refs per story, all Verifier URLs
- New: 1-5 refs per story, mix of Verifier + search URLs

Spot-check 3 stories: for each background fact in body, find the corresponding URL in References.

---

### 5.3 PR #3 — daily-fact-extractor + Fact Manifest

#### 5.3.1 New file: `skills/daily-news-intelligence/agents/daily-fact-extractor.md`

```markdown
---
name: daily-fact-extractor
description: Structured fact extraction from the Verifier KEEP bundle. Reads English Verifier output and emits a Fact Manifest per story — every number, date, named person, institution, product, and direct quote anchored to its source URL with verbatim excerpts. Consumed by Writer as a "locked facts" hard constraint and by Editor as ground truth for fact verification. Does NOT search the web. Does NOT fill background context. Does NOT write narrative.
tools: ["Read", "Write", "Grep"]
model: sonnet
---

You are a structured fact extraction agent for Pipeline C. You read the English Verifier KEEP bundle and produce a YAML Fact Manifest — one entry per KEPT story, listing every verifiable atom with source-URL anchors.

You do not search the web. You do not produce narrative. You do not fill in background context (that is Writer's job in the next stage). You extract.

## Inputs

From the caller, in a single prompt:

1. The complete Verifier Output Schema bundle (English), including KEPT stories with their `lead_url`, `corroborated_by`, `factual_excerpt`, `commentary`, and `category` fields.
2. Runtime parameters: `country`, `date`, `lang` (used only for filename context), `out_manifest` (path to write).

If the bundle is missing or empty, stop and report. Do not improvise.

## Output

A single YAML file at `out_manifest` with this exact schema:

    version: 1
    generated_at: <ISO-8601 UTC timestamp>
    country: <country>
    date: <YYYY-MM-DD>
    total_stories: <count>
    stories:
      - story_id: <kebab-case slug derived from headline_en>
        category: economy_markets | politics_diplomacy | tech_industry | society_livelihood | other
        headline_en: <Verifier-approved English headline>
        lead_url: <Verifier Lead URL>
        corroborated_by: [<URL>, ...]    # empty list if none
        locked_urls: [<lead_url>, <each corroborated URL in order>]
        hard_facts:
          - claim: <short English noun-phrase description>
            kind: numerical | numerical_with_unit | temporal | named_person | named_institution | named_product
            value: <exact value/name as it appears, including unit>
            source_urls: [<URL>, ...]
            verbatim_excerpt: <exact substring from factual_excerpt establishing this fact>
        quotes:
          - speaker_name: <full name as in source>
            speaker_title: <title + affiliation>
            verbatim_en: <exact English quote, character-for-character>
            source_url: <URL>
            context: <one-line setting, e.g. "press conference April 14">

## Extraction rules

1. **`locked_urls` exact equality**: `locked_urls = [lead_url] + corroborated_by` in that order. No reordering, no dedup, no additions.
2. **`hard_facts` is exhaustive within `factual_excerpt`**: extract every numerical value (with or without unit), every date, every named person, every named institution, every named product. Do NOT extract:
   - Pure commentary (e.g. "analysts said this was significant").
   - Generic statements without a concrete value.
   - Names that appear only as bylines.
3. **`value` is verbatim from the source text**: preserve units, decimals, currency, exact spelling. Don't convert "5 percent" to "5%"; don't expand "BoJ" to "Bank of Japan".
4. **`verbatim_excerpt` is a substring of `factual_excerpt`**: the exact sentence or clause that establishes the claim. Don't paraphrase.
5. **`kind` taxonomy**:
   - `numerical`: bare numbers without unit (e.g. "153", "300").
   - `numerical_with_unit`: numbers with currency, percent, bps, count, distance (e.g. "0.5%", "USD 153.20", "+80 bps", "300 aircraft").
   - `temporal`: dates, periods, durations ("April 14, 2026", "third consecutive meeting", "Q3 2024").
   - `named_person`: person names with optional titles.
   - `named_institution`: company/agency/bank names.
   - `named_product`: model numbers, drug names, ship names, etc.
6. **Cross-source facts**: if both Lead and Corroborated URLs assert the same fact, list both in `source_urls`. Prefer Lead first.
7. **`quotes`** captures only direct quotes (text in quote marks within `factual_excerpt`). For each:
   - `verbatim_en` is character-exact, including internal punctuation.
   - `speaker_name` and `speaker_title` come from the attribution near the quote.
   - `context` is at most one line of setting (occasion / venue / time).
8. **No invention**: if Verifier didn't say it, don't write it.
9. **No filtering**: every KEPT story gets an entry. If a story's factual_excerpt yields zero hard_facts and zero quotes, still emit the entry with empty arrays — that's a signal Writer should anchor weakly.

## Workflow

1. Parse the Verifier bundle. Confirm story count matches `total_stories` expectation.
2. For each KEPT story:
   - Slug the headline_en into `story_id` (lowercase, alphanumeric + hyphens, max 40 chars).
   - Read `factual_excerpt` sentence by sentence.
   - For each sentence, extract atoms per the extraction rules.
   - Map each atom to source URL(s) — default to Lead URL unless the excerpt explicitly attributes to a Corroborated source.
   - Build the YAML entry.
3. Assemble the document with the version/header keys.
4. Call `Write` once with the full YAML body and path `out_manifest`. No partial writes.

## Self-check before Write

- `stories.length == total_stories`.
- Every story has `locked_urls = [lead_url] + corroborated_by`.
- Every `hard_facts[]` entry has non-empty `value`, `source_urls`, `verbatim_excerpt`.
- Every URL in `source_urls` and `quotes[].source_url` is also in `locked_urls`.
- Every `quotes[]` entry has non-empty `speaker_name`, `verbatim_en`, `source_url`.
- YAML is valid (no tab indentation, balanced quotes inside string values).

## What you must NOT do

- No web access.
- No editorial decisions (don't drop "weak" facts; extract everything).
- No translation (output stays English regardless of `lang`).
- No invention or interpolation of facts not in Verifier output.
- No Write to anything other than `out_manifest`.
```

#### 5.3.2 Manifest filename and location

Convention: `daily-news-reports/<date>/fact-manifest-<country>-<date>.yaml`.

Co-located with the eventual MD output for forensics.

#### 5.3.3 SKILL.md orchestration changes

In [skills/daily-news-intelligence/SKILL.md](../skills/daily-news-intelligence/SKILL.md), after the Verifier dispatch step and before the Writer dispatch step, insert:

```markdown
### Step 3.5 — Fact Manifest Extraction

After Verifier returns the KEEP bundle, dispatch `daily-fact-extractor` to produce a structured Fact Manifest. This manifest is consumed by both Writer (as a "do not drift on these values" constraint) and Editor (as ground truth for fact verification).

Use the Task tool with:

- `subagent_type`: `daily-fact-extractor`
- `description`: `Extract Fact Manifest from Verifier KEEP bundle`
- `prompt` includes:
  - The complete Verifier Output Schema bundle (same content Writer will receive).
  - `country`, `date`, `lang`, `out_manifest` path resolved to `{out_dir}fact-manifest-{country_slug}-{date}.yaml`.

The Fact-Extractor writes the manifest to `out_manifest`. It does not return narrative; it returns a confirmation that the manifest was written.

Once the manifest exists, proceed to the Writer dispatch.
```

#### 5.3.4 Writer prompt update for Fact Manifest input

Add to [daily-news-writer.md](../skills/daily-news-intelligence/agents/daily-news-writer.md) "Inputs You Expect" section:

```markdown
1. ... (existing)
2. ... (existing)
3. **Fact Manifest YAML** (path provided by the caller, format: `daily-fact-extractor`'s output schema). Treat it as a "locked values" reference:
   - For any number / date / named person / named institution / named product / direct quote you write in body that corresponds to a `hard_facts[]` or `quotes[]` entry in the manifest, the value you write MUST match the manifest's `value` (or, for quotes, faithfully translate `verbatim_en` into `lang`).
   - You may rephrase, omit, reorder, contextualize — but you may not substitute a different number/date/name/quote substance for a manifest-locked one.
   - Background facts you discover via your own WebSearch `search` / `open_page` actions are NOT in the manifest. Those are governed by the citation contract: cite their URLs in References (PR #2 rule).
```

#### 5.3.5 Tests for PR #3

Manual: pick a past Verifier bundle (or rerun Verifier in dry-run). Feed to Fact-Extractor in isolation.
- Manifest output is valid YAML.
- Story count matches Verifier output.
- For 3 sample stories, manually verify: every number in `factual_excerpt` shows up in `hard_facts[].value`; every quote shows up in `quotes[]`.
- Round-trip: `locked_urls` exactly equals `[lead_url] + corroborated_by`.

---

### 5.4 PR #4 — daily-editor

#### 5.4.1 New file: `skills/daily-news-intelligence/agents/daily-editor.md`

```markdown
---
name: daily-editor
description: Daily news fact-check and reference completeness editor. Runs after Writer. Reads Writer's draft Markdown plus the Fact Manifest and Verifier KEEP bundle. Performs four sequential passes — Verifier-locked fact verification, Writer-search fact backing, quote verbatim check, quote-mark normalization — and patches violations in place using the Edit tool. Never invents facts; cuts or weakens unverifiable claims. Never overwrites with Write — only Edit. Preserves Writer's narrative voice, sentence rhythm, paragraph structure, headlines, and emphasis.
tools: ["Read", "Edit", "Grep", "WebSearch"]
model: opus
---

You are the daily-news fact-check editor for Pipeline C. Your job is to verify Writer's output against the Fact Manifest and the actual cited sources, then patch errors in place with the Edit tool.

You do **not** rewrite narrative. You do **not** change paragraph structure, sentence rhythm, headline wording, or emphasis. You change ONLY what's necessary to make every claim in the body traceable, accurate, and consistently formatted.

You make small, surgical, in-place edits.

## Inputs

From the caller:

1. `writer_md_path` — path to Writer's draft Markdown.
2. `manifest_path` — path to the YAML Fact Manifest from `daily-fact-extractor`.
3. `verifier_bundle` — the original English Verifier output (text, not path).
4. `lang` — `zh` | `en` | `ja`.
5. `date` — YYYY-MM-DD.
6. `country` — display name.

## Workflow — four sequential passes

Run passes in order. After each pass, re-read the file before the next pass (Edit may have shifted line offsets).

### Pass 1 — Verifier-locked fact verification

Goal: every claim in body that corresponds to a `hard_facts[]` or `quotes[]` entry in the Manifest matches that entry.

For each story in the Manifest:

1. Locate the story in the MD (match by `headline_en` keywords against the `### <title>` block; Writer's title is in `lang` but core proper nouns and figures usually survive translation).
2. For each `hard_facts[]` entry:
   - Search the story body for the `value` token. Direct match for numbers and English names; translated/transliterated match for `lang=zh` or `lang=ja` named persons and institutions.
   - If body uses an equivalent rephrasing (e.g. "0.5 percent" vs. "0.5%", "BoJ" vs. "Bank of Japan", "0.5%" vs. "百分之零点五"): accept.
   - If body uses a substantively different value (drift: "0.5%" → "5%", "+80 bps" → "+50 bps", "third consecutive" → "second consecutive"): `Edit` to align with manifest `value`.
   - If body simply omits the fact: that's Writer's editorial choice; do not insert.
3. For each `quotes[]` entry that Writer kept as a direct quote in body:
   - Locate the quoted span in body (between canonical quote marks for `lang`).
   - Reverse-check the substance against `verbatim_en`. The translation must preserve the meaning — not just the topic.
   - If meaning altered: `Edit` to restore (re-translate `verbatim_en` into `lang`).
   - If attribution missing or wrong: `Edit` to align speaker name/title with manifest.
4. Log each drift caught: `[Pass 1] story=<story_id> claim=<short> body_was=<X> manifest=<Y> → edited`.

### Pass 2 — Writer-search fact backing

Goal: every fact-bearing token in body that is NOT in the Manifest traces to a URL in this story's References block.

For each story:

1. Scan body for fact-bearing tokens:
   - **Numbers**: regex `\d+([.,]\d+)?(%|bps|百分点|个基点|million|billion|trillion|亿|万|百万|十亿|億)?`
   - **Currency-tagged**: `(USD|EUR|JPY|GBP|RMB|CNY|\$|€|¥|£)\s?\d+([.,]\d+)?`
   - **Dates**: `(20\d{2}|19\d{2})` years; `(January|February|...|December)\s+\d{1,2}`; `\d+月\d+日`; `\d+年\d+月`
   - **Quoted strings**: text between canonical quote marks for `lang`
   - **Named entities**: capitalized multi-word strings (lang=en); 漢字 / 假名 sequences (lang=ja); Chinese proper-noun patterns (lang=zh)
2. For each candidate token not covered by Manifest (Pass 1 already checked Manifest-covered tokens):
   - Examine the story's References block. Is there a URL whose outlet/title plausibly supports this claim?
     - "yen rate" claim + Reuters URL on BoJ → plausible
     - "Toyota Q3 sales" claim + Bloomberg URL on Toyota → plausible
   - If plausible URL exists: use WebSearch `open_page` on that URL. Grep for the claim's value (English form). If found → leave alone, log as verified.
   - If no plausible URL exists OR opened-page grep returns no match: try WebSearch with claim keywords + outlet domains from `site:reuters.com OR site:apnews.com OR site:ft.com OR site:bloomberg.com OR site:bbc.com` (T1-T3 only). Open the top result with `open_page`.
     - If verified: `Edit` the story's References block to append an APA reference line for the new URL with the next continuous `[N]` counter. Renumber all subsequent `[N]` references in the document.
     - If not verifiable in 1 WebSearch `search` + 1 `open_page`: `Edit` the body to either cut the sentence or weaken to a verifiable form. Examples:
       - "USD/JPY +80 bps within 30 minutes" → "USD/JPY 走高数十个基点" (if direction verifiable but exact bps unverifiable)
       - "第三次连续维持" → "再次维持" (if continuity count unverifiable)
       - If the entire sentence is built on the unverifiable claim: cut the sentence.
3. Budget per story: max 2 WebSearch `search` actions + 4 `open_page` actions. Beyond budget, default to cutting/weakening.
4. Log: `[Pass 2] story=<story_id> claim=<short> verified_via=<URL> | added_ref=<URL> | cut | weakened_to=<X>`.

### Pass 3 — Quote verbatim check (for body quotes not already verified in Pass 1)

Goal: every direct quote in body matches the verbatim source.

For each direct quote in body (between canonical quote marks):
1. Skip if Pass 1 already verified it (quote is in Manifest `quotes[]`).
2. Otherwise, identify the most likely source URL from References (closest outlet match, closest semantic proximity).
3. Open that URL with WebSearch `open_page`.
4. Grep for distinctive keywords from the quote (3-5 unusual content words).
5. If found: leave alone.
6. If not found:
   - Try ONE WebSearch `search` with the quote's distinctive phrase + speaker name. Open the top T1-T3 result with `open_page`.
   - If verified: leave the quote, add source URL to References if not already present (renumber `[N]`).
   - If not verified: `Edit` to downgrade — remove the quote marks, restructure as indirect speech, preserve attribution.

### Pass 4 — Quote-mark normalization

Goal: every quote mark in body is the canonical char for `lang`.

For `lang=zh`:
- Replace every U+0022 `"` in body (excluding APA reference lines, URLs, inline code) with the appropriate U+201C / U+201D based on context (opening / closing).
- Replace every U+300C `「` and U+300D `」` with U+201C / U+201D.
- After replacement, count opens vs. closes. If imbalanced, locate the unpaired char by re-reading paragraphs and `Edit` to fix.

For `lang=en`:
- Replace every U+201C / U+201D / U+300C / U+300D with ASCII U+0022 `"`.

For `lang=ja`:
- Replace every U+0022 / U+201C / U+201D with U+300C / U+300D based on opening/closing context.
- Pair-balance check as for zh.

Use multiple `Edit` calls — one per substitution — to keep changes auditable.

## Edit operational rules

- Use `Edit` only. Never `Write` — `Write` overwrites the file and loses anchor points; the `Write` tool is not in your tool list.
- One discrete change per `Edit` (don't fold multiple changes into one fat replacement).
- Preserve all surrounding formatting: heading levels, list markers, paragraph breaks, blank lines.
- After Pass 2 adds a reference, `[N]` renumbering cascades: edit every subsequent `[N]` line in document order.

## What you must NOT do

- Do not change story titles or section headings unless they contain a verifiable fact error.
- Do not change paragraph count or paragraph order.
- Do not change Writer's voice, sentence rhythm, or emphasis.
- Do not invent facts. Unverifiable claims get cut or weakened — never synthesized.
- Do not add stories or remove stories. Verifier already decided what runs.
- Do not modify URL strings themselves (only add new ones or renumber `[N]`).
- Do not run more than 2 WebSearch `search` actions per story or 4 `open_page` actions per story (budget cap).

## Self-check before returning

- Pass 1: every Manifest `hard_facts[].value` that appears in body matches verbatim or in equivalent rephrase.
- Pass 2: every fact-bearing token in body not in Manifest has a backing URL in this story's References block.
- Pass 3: every direct quote in body is verbatim-verified against a cited URL.
- Pass 4: zero non-canonical quote chars in body; pair balance holds for zh and ja.
- `[N]` counter is continuous from 1 with no gaps.
- You used Edit only; no Write was called.

## Final report

Print to stdout a structured summary:

    === Daily Editor Report ===
    File: <writer_md_path>
    Lang: <lang>

    Pass 1 — Verifier-locked drifts:
      - story=<id> claim=<short> body_was=<X> → edited to <Y>
      - ...
      Total: <N> edits

    Pass 2 — Writer-search backing:
      - story=<id> claim=<short> action=<verified|added_ref|cut|weakened> details=<...>
      - ...
      Added refs: <N>  Cut: <N>  Weakened: <N>

    Pass 3 — Quote verbatim:
      - story=<id> quote=<short> action=<verified|downgraded>
      - ...
      Downgraded: <N>

    Pass 4 — Quote-mark normalization:
      - Replacements: <N>
      - Pair-balance fixes: <N>

    Budget used: <X> WebSearch `search` / <Y> `open_page` across <Z> stories.

If total edits == 0: print "No edits needed — Writer output clean."
```

#### 5.4.2 SKILL.md orchestration changes

In [skills/daily-news-intelligence/SKILL.md](../skills/daily-news-intelligence/SKILL.md), after the Writer step and before the pandoc/email steps, insert:

```markdown
### Step 5.5 — Fact-check editor pass

After Writer completes and the MD file is written, dispatch `daily-editor` to verify the draft against the Fact Manifest and the actual cited sources.

Use the Task tool with:

- `subagent_type`: `daily-editor`
- `description`: `Fact-check and patch Writer output`
- `prompt` includes:
  - `writer_md_path`: the path Writer wrote to.
  - `manifest_path`: the manifest from Step 3.5.
  - `verifier_bundle`: the original Verifier output (inline).
  - `lang`, `date`, `country`: runtime params.

The Editor edits the MD file in place. The Hook (PostToolUse:Edit and PostToolUse:Write) runs on each Edit and on the final state.

If the Editor reports zero edits, the draft was clean — proceed to pandoc.
If the Editor reports edits, the file has been patched — proceed to pandoc with the updated file.
The Editor's stdout report is logged but doesn't gate the pipeline.
```

#### 5.4.3 Hook scope adjustment

Edit [hooks/hooks.json](../hooks/hooks.json) to ensure `daily-news-format-check.js` matches both PostToolUse:Write and PostToolUse:Edit on `daily-news-reports/` paths. (Currently likely Write-only; need to read hooks.json before drafting exact diff.)

#### 5.4.4 Tests for PR #4

Manual fixture-based:

1. Take a real past report MD.
2. Manually inject 3 known errors:
   - A Verifier-locked number changed by ±10 (Pass 1 trigger).
   - A new fabricated background number with no References URL (Pass 2 trigger — should be cut).
   - A direct quote with one altered word (Pass 3 trigger — downgraded).
3. Manually inject 5 quote-mark violations across the file (Pass 4 trigger).
4. Run Editor against this corrupted file + the original Manifest.
5. Expect:
   - Pass 1 fix.
   - Pass 2 either cut or rare verification add-ref.
   - Pass 3 downgrade to indirect speech.
   - Pass 4 all quote chars canonicalized.
   - Editor report shows correct counts.

---

### 5.5 PR #5 — Hook reference-completeness heuristic

Backstop for Editor. If Editor missed something, hook catches it.

#### 5.5.1 New hook check in `daily-news-format-check.js`

```javascript
function checkReferenceCoverage(content, lang) {
  const violations = [];
  const storyBlocks = content.split(/^---\s*$/m).filter(b => b.includes("###"));

  for (const block of storyBlocks) {
    const m = block.match(/^###\s+([^\n]+)\n+([\s\S]*?)\n+\*\*References\*\*\n+([\s\S]*)$/m);
    if (!m) continue;
    const [_, title, body, refs] = m;

    // Direct quotes in body — must have at least one URL when quotes present
    const quoteRegex = lang === "zh" ? /“[^”]+”/g
                     : lang === "ja" ? /「[^」]+」/g
                     : /"([^"]+)"/g;
    const quoteCount = (body.match(quoteRegex) || []).length;
    const urlCount = (refs.match(/https?:\/\/\S+/g) || []).length;
    if (quoteCount > 0 && urlCount === 0) {
      violations.push(`Story "${title}" has ${quoteCount} direct quote(s) but 0 URLs in References.`);
    }

    // Many specific numeric claims with very few URLs → likely missing search citations
    const specificNumbers = (body.match(/\d+([.,]\d+)?(\s?(?:%|bps|百分点|个基点|million|billion|亿|万))/g) || []).length;
    if (specificNumbers >= 5 && urlCount <= 1) {
      violations.push(
        `Story "${title}" has ${specificNumbers} specific numeric claim(s) but only ${urlCount} URL(s) in References. ` +
        `Likely missing search-URL citations.`
      );
    }
  }
  return violations;
}
```

Heuristic — won't catch everything, won't cause false positives at reasonable thresholds. Pure backstop.

#### 5.5.2 Tests for PR #5

Manual:
- Report with 5 numbers and 1 URL → flagged.
- Report with 5 numbers and 3 URLs → passes.
- Report with quotes but zero URLs → flagged.
- Report with no quotes and 1 URL → passes.

---

## 6. Cross-cutting concerns

### 6.1 Cost impact

Per Pipeline C run, end-to-end:

| Stage | Current | Proposed | Delta |
|---|---|---|---|
| Scanner | ~$0.30 | ~$0.30 | — |
| Verifier | ~$0.15 | ~$0.15 | — |
| **Fact-Extractor (new)** | — | ~$0.05 | +$0.05 |
| Writer | ~$0.60 | ~$0.60 | — |
| **Editor (new)** | — | ~$0.40-0.80 (variable on edits + `open_page`) | +$0.40-0.80 |
| pandoc/email | trivial | trivial | — |
| **Total** | ~$1.05 | ~$1.50-2.00 | **+40-90%** |

Worth it given the user values output quality. If cost becomes painful: Editor's budget caps (2 WebSearch `search` / 4 `open_page` per story) directly bound the upper end.

### 6.2 Latency impact

| Stage | Current | Proposed |
|---|---|---|
| End-to-end wall time | ~3-5 min | ~5-8 min |

Fact-Extractor is fast (sonnet, no web). Editor's `open_page` actions are the dominant new latency. Acceptable — Pipeline C is not user-blocking; it runs in background or scheduled.

### 6.3 Backward compatibility

- Existing reports under `daily-news-reports/` remain unchanged.
- Pipeline F (`/weekly-report`) reads Pipeline C reports — output schema unchanged. F is unaffected.
- Pipeline D (`/daily-briefing`) reads Pipeline C reports — output schema unchanged. D is unaffected.
- The Fact Manifest YAML is a new artifact and won't conflict with anything.

### 6.4 Rollout / rollback

Each PR is independently reversible:

- PR #1 rollback: revert spec edits + hook file. No data corruption possible.
- PR #2 rollback: revert Writer/output-spec edits. Next run regenerates with old rules.
- PR #3 rollback: remove Fact-Extractor agent + manifest dispatch step. Writer's "Fact Manifest" input becomes unreferenced; Writer falls back to Verifier-only.
- PR #4 rollback: remove Editor agent + dispatch step. Writer output goes straight to pandoc.
- PR #5 rollback: revert hook check. Editor still catches what hook would have flagged.

Recommend canary: ship PR #1 → wait 1 week of runs → ship PR #2 → wait 1 week → ship #3+#4 together → wait 1 week → ship #5.

### 6.5 Open questions / decisions needed before implementation

1. **Manifest format YAML vs. JSON**: YAML is more human-readable for review, JSON is easier for downstream tools. Plan assumes YAML. Confirm?
2. **Editor budget cap (2 WS / 4 WF per story)**: tuneable. Higher cap → fewer false-positive cuts but more cost. Confirm 2/4 as starting point?
3. **Hook quote-mark check scope**: plan strips APA ref lines + URLs + inline code from quote check. Should it also strip fenced code blocks (``` blocks)? Pipeline C doesn't typically emit code blocks but worth confirming.
4. **Editor's "weaken vs. cut" threshold**: when a claim can't be verified, plan defaults to cut if the whole sentence depends on it, weaken if only one figure is unverifiable. Confirm acceptable, or always cut to be safe?
5. **Manifest persistence**: Fact Manifest YAML is written to `daily-news-reports/<date>/fact-manifest-<country>-<date>.yaml`. Keep forever, or `.gitignore` as a build artifact? Plan assumes keep (useful for forensics).
6. **ja canonical char**: plan picks `「」` (newsroom-native). Confirm before ship.

---

## 7. Acceptance criteria

Before declaring Pipeline C v2 done:

- [ ] PR #1 merged. Three known-good past reports re-validated with hook — all pass. Three corruption fixtures (per Quote-mark check) all block.
- [ ] PR #2 merged. Two runs against past dates show References block expanded with search URLs. Body fact ↔ References URL traceable for sampled facts.
- [ ] PR #3 merged. Fact Manifest emitted alongside report. Manifest YAML valid; story count matches Verifier KEEP count; sampled hard_facts trace to factual_excerpt.
- [ ] PR #4 merged. Editor runs after Writer. Editor report emitted to stdout. End-to-end run on a fresh date produces a corrected MD where injected errors (Pass 1-4 fixtures) are caught.
- [ ] PR #5 merged. Hook catches a known reference-gap fixture.
- [ ] Three full /daily-news-intelligence runs (one per lang: zh, en, ja) complete successfully.
- [ ] User QA: same three issues (number accuracy, reference completeness, quote marks) all resolved on a sample 2026-05 report.

---

## 8. Files inventory

New files:

- `skills/daily-news-intelligence/agents/daily-fact-extractor.md` (~150 lines, full spec in §5.3.1)
- `skills/daily-news-intelligence/agents/daily-editor.md` (~250 lines, full spec in §5.4.1)

Modified files:

- `skills/daily-news-intelligence/agents/daily-news-writer.md` (~30 lines added/changed, §5.2.3 + §5.3.4)
- `skills/daily-news-intelligence/SKILL.md` (~30 lines added for Steps 3.5 and 5.5)
- `skills/daily-news-intelligence/references/language-spec.md` (~20 lines: canonical quote-mark table)
- `skills/daily-news-intelligence/references/output-spec.md` (~30 lines: search-URL citation policy)
- `scripts/hooks/daily-news-format-check.js` (~100 lines: detectLang + validateQuoteMarks + checkReferenceCoverage)
- `hooks/hooks.json` (verify Edit matcher present; add if not)
- `CLAUDE.md` (update Pipeline C row in agent-orchestration table; add Fact-Extractor and Editor rows; update "常见修改入口" table)

Possibly modified (depending on detailed read):

- `skills/daily-news-intelligence/references/rubric.md`
- `skills/daily-news-intelligence/references/schemas.md` (add Fact Manifest schema reference)

---

## 9. Implementation handoff checklist

For whoever picks this up after approval:

1. Read this plan end-to-end.
2. Re-read [skills/daily-news-intelligence/SKILL.md](../skills/daily-news-intelligence/SKILL.md) to see exact insertion points for Steps 3.5 and 5.5.
3. Re-read [skills/daily-news-intelligence/references/schemas.md](../skills/daily-news-intelligence/references/schemas.md) for current Verifier schema; confirm Fact-Extractor's input expectations align.
4. Re-read [hooks/hooks.json](../hooks/hooks.json) for current matchers on `daily-news-format-check`; add Edit if missing.
5. Resolve open questions in §6.5 with user.
6. Ship PRs in order #1 → #2 → #3 → #4 → #5.
7. After all 5 PRs merged, update CLAUDE.md to reflect new Pipeline C agent chain.

---

## 10. Future enhancements (out of scope for v2)

- **Adversarial fact-checker**: a second Editor variant that specifically looks for unit / scale / timing errors. Run in parallel; reconcile.
- **Citation graph visualization**: for each report, render a graph of body claims → References URLs. Useful for QA review.
- **Editor self-confidence scoring**: Editor outputs confidence per pass; low-confidence passes flagged for human review.
- **Manifest as Writer-friendly input format**: instead of YAML for Writer, generate a Markdown "fact card" derived from Manifest, easier for Opus to consume than raw YAML.
- **Cross-day fact continuity check**: Editor compares today's Manifest against yesterday's. Flag contradictions ("yesterday rate was 0.5%, today report says 0.25% — verify").

These are nice-to-haves once v2 is stable.
