# Schemas — Scanner Bundle and Verifier Output Formats

Loaded by the Scanner and the Verifier stages. Not needed by the Writer.

## Scanner Bundle Schema (all categories)

The Scanner handles all active categories and returns one unified bundle. Same per-story field shape, grouped by `active_categories` order (English raw data — no translation):

```
## Scan Report
- Categories processed: <N>  (N=6 non-China, N=7 China)
- Cross-category duplicates collapsed: <d>
- Reroutes applied: <r>
- Reserve pool entries held: <p>
- Geography exclusions: <g>   (unique candidate URLs discarded by the hard geography gate)

## Scan Summary
- Country: <country>
- Geography scope: <country | Europe-ex-UK>
- Date: <YYYY-MM-DD>
- Candidates kept: <M>
- Category counts: one `id=<n>` token per category in active-category order (per `references/language-spec.md` § Category Catalog & Selection), pipe-separated. Non-China report: `econ=<n1> | politics=<n2> | tech=<n3> | society=<n4> | ipo_ma=<n5> | other=<n6>`. China report: `econ=<n1> | politics=<n2> | tech=<n3> | society=<n4> | china_nexus=<n5> | ipo_ma=<n6> | other=<n7>`. **Example concrete value (Japan, non-China)**: `econ=3 | politics=2 | tech=2 | society=1 | ipo_ma=2 | other=1`. **Example (China)**: `econ=3 | politics=2 | tech=2 | society=1 | china_nexus=2 | ipo_ma=1 | other=1`.
- Reserve pool counts: same `id=<n>` token format, pipe-separated; zero entries shown as `<id>=0`.

## Stories
(grouped by active-category order; each story keeps the Scanner per-story fields verbatim, minus `Reroute hint` which the Scanner resolves in § Step 6)

### [<final category>] <English headline>
- Publish date (verified): <...>
- Discovery: <A | B>
- Source: <outlet name> [tier]
- Source legitimacy: <matrix | auto-accept | conditional-accept>
- Body-source: <full | paywall-stub>
- Geographic nexus: <primary country, non-UK European jurisdiction, or EU/pan-European institution>
- UK role: <not-applicable | none | context | external-counterparty>
- Impact tier: <Policy | Market | Structural | Humanitarian>
- URL: <full https URL>
- Byline: <...>
- Corroborated by: <merged list — every cross-category duplicate folded here verbatim; or "None">
- Factual excerpt: <verbatim Scanner extract; full body or paywall stub per Body-source>
- Commentary: <verbatim>

... (repeat per surviving story) ...

## Reserve Pool
(consolidated from all per-category passes, grouped by `active_categories` order; same dedup discipline as main stories — if a reserve-pool entry shares the underlying event with a main-pool story, fold the reserve entry into the main story's `Corroborated by` instead and drop the reserve entry; if two reserve entries collide, keep the higher-real-tier one and fold the other into its `Corroborated by`. Omit the whole block when no held candidates remain.)

### [<final category>] <English headline>
- Publish date (verified): <...>
- Discovery: B
- Source: <outlet name> [real tier]
- Source legitimacy: <auto-accept | conditional-accept>
- Held: <below-authority-cap | below-ipo-ma-floor>
- Held reason: <single sentence>
- Geographic nexus: <primary country, non-UK European jurisdiction, or EU/pan-European institution>
- UK role: <not-applicable | none | context | external-counterparty>
- URL: <full https URL>
- Byline: <...>
- Corroborated by: <merged list or "None">
- Factual excerpt (≥200 words English): <verbatim>
- Commentary: <verbatim>

... (repeat per surviving reserve entry) ...

## Category Coverage Gap   (include per category still short after Pass A + Pass B AND reserve pool would not lift it to min_per_category)
- Category: <id>
- Queries attempted: <q1>, <q2>, <q3>
- Reserve pool size: <R>   (0 if no held candidates for this category)
- Reason: <single sentence>
```

## Verifier Output Schema

Verifier must consume the **Scanner Bundle** and emit exactly this shape (still English raw data — no translation, no Writer-style narrative):

```
## Verification Report
- Input count (from Scanner): <N>
- Reserve pool input count (from Scanner): <P>
- Kept count: <M>   (includes any Fallback-1.5 promotions)
- Geography scope: <country | Europe-ex-UK>
- Category counts after verification: one `id=<n>` token per category in active-category order, pipe-separated. Non-China report: `econ=<n1> | politics=<n2> | tech=<n3> | society=<n4> | ipo_ma=<n5> | other=<n6>`. China report: `econ=<n1> | politics=<n2> | tech=<n3> | society=<n4> | china_nexus=<n5> | ipo_ma=<n6> | other=<n7>`
- Fallback used: <none | fallback_1 | fallback_1+gap | fallback_1+1.5 | fallback_1+1.5+gap>
- Reserve pool promotions (Fallback 1.5): <k>   (omit or "0" when fallback_1.5 did not run)

## Kept Stories

### [Category] <English headline>
- Publish date (verified): <ISO timestamp or local date>
- Source: <outlet name> [T1|T2|T3|T4]
- URL: <full https URL>
- Byline: <author name or "No byline">
- Discovery: <A | B>   (carried verbatim from the Scanner Bundle)
- Source legitimacy: <matrix | auto-accept | conditional-accept>   (carried verbatim)
- Body-source: <full | paywall-stub>   (carried verbatim from the Scanner Bundle)
- Geographic nexus: <carried verbatim from the Scanner Bundle>
- UK role: <not-applicable | none | context | external-counterparty>   (carried verbatim from the Scanner Bundle)
- Origin: <main-pool | reserve-pool>   (reserve-pool means promoted via Fallback 1.5; omit field for main-pool entries)
- Corroborated by: <carried verbatim from the Scanner Bundle — each entry as "  - <outlet name> [<tier>|<paywall_status>] — <full https URL>"; or "None">
- Factual excerpt: <carried verbatim — full body or paywall stub per Body-source>
- Commentary: <carried verbatim>
- Verdict: KEEP
- Originality: <Original | Syndicated | Unclear | Sanctioned-syndication>
- Authority score: <T1-primary | T1-wire | T4-official | T2-primary | T2-wire | T3 | T3-extended>   (`T3-extended` = promoted via Fallback 1.5 from `below-authority-cap`)
- Impact tier: <Policy | Market | Structural | Humanitarian | Regional-structural>
- Dedup role: <Lead | Corroboration-of-#X | Standalone>

... (repeat per kept story) ...

## Dropped Stories

- URL: <full https URL>
- Reason: <Duplicate-of-#X | Syndicated-rewrite | Illegitimate-source | UK-primary-nexus-excluded | Low-impact | Op-ed | Routine-PR | Celebrity-or-lifestyle | Incremental-no-new-fact | Sports-non-political | China-aid-smallcountry-excluded | Below-IPO-MA-threshold | Other-specific-reason>

... (repeat per dropped story) ...

## Reserve Pool — Held (not promoted)
(reserve-pool entries the Verifier left held — either because the category already met `min_per_category` without 1.5, or because 1.5 ran and stopped at the floor without needing this entry. Omit this block when the Scanner Bundle's reserve pool was empty.)

- URL: <full https URL>
- Category: <id>
- Held: <below-authority-cap | below-ipo-ma-floor>
- Disposition: <category-already-met | not-needed-by-fallback-1.5 | dropped-illegitimate-on-revalidation | dropped-geography-on-revalidation>

... (repeat per held entry) ...

## Post-Verification Coverage
(one line per category in active-category order; include the `china_nexus` line only for a China report)
- econ: <n>/<min_per_category>
- politics: <n>/<min_per_category>
- tech: <n>/<min_per_category>
- society: <n>/<min_per_category>
- china_nexus: <n>/<min_per_category>   (China report only — omit this line otherwise)
- ipo_ma: <n>/<min_per_category>
- other: <n>/<min_per_category>

## Post-Verification Coverage Gap   (include only if any category still < min_per_category after fallback_1 AND fallback_1.5)
- Category: <name>
- Scanner kept count: <n>
- Verifier kept count (after fallback_1+1.5): <m>
- Reserve pool size for this category: <r>   (0 if the Scanner's reserve pool was empty for this category; > 0 means 1.5 ran and still could not lift it — typically because the pool entries were `Illegitimate-source` on revalidation)
- Reason: <single sentence>
```
