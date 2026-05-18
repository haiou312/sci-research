# Schemas — Scanner, Merged Bundle, and Verifier Output Formats

Loaded by the per-category Scanner, the Merger, and the Verifier stages. Not needed by the Writer.

## Scanner Output Schema (single category)

Each Scanner instance handles **exactly one category** and returns exactly this shape (English raw data — no translation):

```
## Scan Summary
- Country: <country>
- Date: <YYYY-MM-DD>
- Category: <your one assigned category id>
- Candidates fetched: <N>
- Candidates kept: <M>  (Pass A: <a> | Pass B: <b>)

## Stories

### [<category>] <English headline>
- Publish date (verified): <ISO timestamp or local date from article>
- Discovery: <A | B>
- Source: <outlet name> [T4-official|T1-wire|T1-flagship|T2|T3] (Lead must be Free or T4-official; Hard-paywall outlets are recorded under Corroborated by, never as Lead)
- Source legitimacy: <matrix | auto-accept | conditional-accept>   (matrix = Pass A; auto/conditional = Pass B per rubric § Source Legitimacy)
- Proposed category: <your category>
- Reroute hint: <other category id — only if dominant frame looks misfiled; omit otherwise>
- URL: <full https URL>
- Byline: <author name or "No byline">
- Corroborated by: <each entry on its own indented line "  - <outlet name> [<tier>|<paywall_status>] — <full https URL>"; or "None">
- Factual excerpt (≥200 words English): <fact-only extract from the Lead URL, with numbers, named officials with titles, direct quotations in quote marks, explicit time references>
- Commentary: <verbatim analyst / official / institutional commentary from the Lead article, or exactly "No analyst commentary in source">

... (repeat per story, source-authority order) ...

## Category Coverage Gap   (include only if your category < min_per_category after Pass A + Pass B)
- Category: <your category>
- Queries attempted: <q1>, <q2>, <q3>
- Reason: <single sentence>
```

## Merged Bundle Schema

The Merger consumes the N single-category Scanner bundles and emits one unified bundle plus a short report. Same per-story field shape as the Scanner schema (all tags carried verbatim: `Discovery`, `Source legitimacy`, tier, `Corroborated by`, excerpt, commentary), grouped by `active_categories` order:

```
## Merge Report
- Input bundles: <N>  (one per active category)
- Cross-category duplicates collapsed: <d>
- Reroutes applied: <r>

## Scan Summary
- Country: <country>
- Date: <YYYY-MM-DD>
- Candidates kept: <M>
- Category counts: one `id=<n>` token per category in active-category order (per `references/language-spec.md` § Category Catalog & Selection), pipe-separated. Non-China report: `econ=<n1> | politics=<n2> | tech=<n3> | society=<n4> | ipo_ma=<n5> | other=<n6>`. China report: `econ=<n1> | politics=<n2> | tech=<n3> | society=<n4> | china_nexus=<n5> | ipo_ma=<n6> | other=<n7>`

## Stories
(grouped by active-category order; each story keeps the Scanner per-story fields verbatim, minus `Reroute hint` which the Merger resolves)

### [<final category>] <English headline>
- Publish date (verified): <...>
- Discovery: <A | B>
- Source: <outlet name> [tier]
- Source legitimacy: <matrix | auto-accept | conditional-accept>
- URL: <full https URL>
- Byline: <...>
- Corroborated by: <merged list — every cross-category duplicate folded here verbatim; or "None">
- Factual excerpt (≥200 words English): <verbatim>
- Commentary: <verbatim>

... (repeat per surviving story) ...

## Category Coverage Gap   (include per category still short after merge)
- Category: <id>
- Reason: <single sentence>
```

## Verifier Output Schema

Verifier must consume the **Merged bundle** and emit exactly this shape (still English raw data — no translation, no Writer-style narrative):

```
## Verification Report
- Input count (from Merger): <N>
- Kept count: <M>
- Category counts after verification: one `id=<n>` token per category in active-category order, pipe-separated. Non-China report: `econ=<n1> | politics=<n2> | tech=<n3> | society=<n4> | ipo_ma=<n5> | other=<n6>`. China report: `econ=<n1> | politics=<n2> | tech=<n3> | society=<n4> | china_nexus=<n5> | ipo_ma=<n6> | other=<n7>`
- Fallback used: <none | fallback_1 | fallback_1+gap>

## Kept Stories

### [Category] <English headline>
- Publish date (verified): <ISO timestamp or local date>
- Source: <outlet name> [T1|T2|T3|T4]
- URL: <full https URL>
- Byline: <author name or "No byline">
- Discovery: <A | B>   (carried verbatim from the Merged bundle)
- Source legitimacy: <matrix | auto-accept | conditional-accept>   (carried verbatim)
- Corroborated by: <carried verbatim from the Merged bundle — each entry as "  - <outlet name> [<tier>|<paywall_status>] — <full https URL>"; or "None">
- Factual excerpt (≥200 words English): <carried verbatim>
- Commentary: <carried verbatim>
- Verdict: KEEP
- Originality: <Original | Syndicated | Unclear | Sanctioned-syndication>
- Authority score: <T1-primary | T1-wire | T4-official | T2-primary | T2-wire | T3>
- Impact tier: <Policy | Market | Structural | Humanitarian | Regional-structural>
- Dedup role: <Lead | Corroboration-of-#X | Standalone>

... (repeat per kept story) ...

## Dropped Stories

- URL: <full https URL>
- Reason: <Duplicate-of-#X | Syndicated-rewrite | Illegitimate-source | Low-impact | Op-ed | Routine-PR | Celebrity-or-lifestyle | Incremental-no-new-fact | Sports-non-political | China-aid-smallcountry-excluded | Below-IPO-MA-threshold | Other-specific-reason>

... (repeat per dropped story) ...

## Post-Verification Coverage
(one line per category in active-category order; include the `china_nexus` line only for a China report)
- econ: <n>/<min_per_category>
- politics: <n>/<min_per_category>
- tech: <n>/<min_per_category>
- society: <n>/<min_per_category>
- china_nexus: <n>/<min_per_category>   (China report only — omit this line otherwise)
- ipo_ma: <n>/<min_per_category>
- other: <n>/<min_per_category>

## Post-Verification Coverage Gap   (include only if any category still < min_per_category after fallback_1)
- Category: <name>
- Scanner kept count: <n>
- Verifier kept count (after fallback_1): <m>
- Reason: <single sentence>
```
