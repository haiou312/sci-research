# Schemas - Scanner Bundle and Verifier Output Formats

Loaded by the Scanner and Verifier stages. These schemas intentionally contain no outlet tiers, Source Matrix fields, Pass A/B markers, authority scores, or Reserve Pool.

## Scanner Bundle Schema

The Scanner handles all active categories and returns one unified English bundle grouped by `active_categories` order.

```
## Scan Report
- Categories processed: <N>  (N=6 non-China, N=7 China)
- Candidate target per category: <max(min_per_category * 2, 6)>
- Distinct candidates admitted: <M>
- Date rejections: <d>
- Geography rejections: <g>
- Source-eligibility rejections: <s>
- Exact-event duplicates collapsed: <x>
- Reroutes applied: <r>

## Scan Summary
- Country: <country>
- Geography scope: <country | Europe-ex-UK>
- Date: <YYYY-MM-DD>
- Category counts: one `id=<n>` token per category in active-category order. Non-China: `econ=<n1> | politics=<n2> | tech=<n3> | society=<n4> | ipo_ma=<n5> | other=<n6>`. China: `econ=<n1> | politics=<n2> | tech=<n3> | society=<n4> | china_nexus=<n5> | ipo_ma=<n6> | other=<n7>`.

## Stories
(grouped by active-category order)

### [<final category>] <English headline>
- Publish date (verified): <ISO timestamp or local date>
- Source: <outlet or institution name>
- Source class: <official-primary | established-media | reputable-regional | reputable-specialist | sanctioned-syndication>
- Source assessment: <one sentence explaining claim-level provenance and why this source is usable>
- Body-source: <full | paywall-stub>
- Geographic nexus: <target country, non-UK European jurisdiction, or EU/pan-European institution>
- UK role: <not-applicable | none | context | external-counterparty>
- URL: <full canonical https URL>
- Byline: <author, organisation byline, or "No byline">
- Provisional news value: <high | medium | routine>
- Corroborated by: <one or more entries as "  - <source name> [<source class>|<full|paywall-stub>] - <full https URL>"; or "None">
- Factual excerpt: <verbatim retrievable text; visible stub only when Body-source=paywall-stub>
- Commentary: <what happened and the concrete reason it may matter>

... (repeat per distinct candidate) ...

## Category Discovery Gap
(include one block per category below `Candidate target per category`)

- Category: <id>
- Candidate target: <n>
- Candidates admitted: <m>
- Query approaches attempted: <concise list of broad, entity-led, official-record, regional, or sector approaches actually used>
- Reason: <why additional credible, date-valid, in-scope distinct events were not found>
```

## Verifier Output Schema

The Verifier consumes the Scanner Bundle and emits this English raw-data shape.

```
## Verification Report
- Input count (from Scanner): <N>
- Kept count: <M>
- Geography scope: <country | Europe-ex-UK>
- Category counts after verification: one `id=<n>` token per category in active-category order. Non-China: `econ=<n1> | politics=<n2> | tech=<n3> | society=<n4> | ipo_ma=<n5> | other=<n6>`. China: `econ=<n1> | politics=<n2> | tech=<n3> | society=<n4> | china_nexus=<n5> | ipo_ma=<n6> | other=<n7>`.
- Coverage review used: <yes | no>
- Coverage-review keeps: <k>

## Kept Stories

### [Category] <English headline>
- Publish date (verified): <ISO timestamp or local date>
- Source: <outlet or institution name>
- Source class: <official-primary | established-media | reputable-regional | reputable-specialist | sanctioned-syndication>
- Source assessment: <carried from Scanner and corrected when revalidation requires>
- URL: <full canonical https URL>
- Byline: <author, organisation byline, or "No byline">
- Body-source: <full | paywall-stub>
- Geographic nexus: <carried from Scanner after revalidation>
- UK role: <not-applicable | none | context | external-counterparty>
- Corroborated by: <carried from Scanner; or "None">
- Factual excerpt: <carried verbatim from Scanner>
- Commentary: <carried verbatim from Scanner>
- Verdict: KEEP
- Source verdict: <credible | credible-with-caveat>
- New-information verdict: <original | primary-record | transparent-syndication | meaningful-follow-up | unclear-but-supported>
- News value: <high | medium | coverage-keep>
- Dedup role: <Lead | Standalone>

... (repeat per kept story) ...

## Dropped Stories

- URL: <full https URL>
- Category: <id>
- Reason: <Duplicate-of-#X | Unsupported-source | UK-primary-nexus-excluded | China-source-excluded | No-new-fact | No-meaningful-news-value | Routine-PR | Op-ed | Unsupported-rumour | Celebrity-or-lifestyle | Sports-non-political | China-aid-smallcountry-excluded | Out-of-category-scope | Other: <specific>>

... (repeat per dropped story) ...

## Post-Verification Coverage
(one line per category in active-category order; include `china_nexus` only for a China report)
- econ: <n>/<min_per_category>
- politics: <n>/<min_per_category>
- tech: <n>/<min_per_category>
- society: <n>/<min_per_category>
- china_nexus: <n>/<min_per_category>   (China only)
- ipo_ma: <n>/<min_per_category>
- other: <n>/<min_per_category>

## Post-Verification Coverage Gap
(include only for a category still below `min_per_category` after Coverage Review)

- Category: <id>
- Scanner candidate count: <n>
- Verifier kept count: <m>
- Coverage-review candidates reconsidered: <r>
- Reason: <single sentence explaining why no additional eligible stories remained>
```
