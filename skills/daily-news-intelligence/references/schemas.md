# Schemas - Category Scanner, Scanner Batch, and Verifier Formats

Each category-scoped Scanner uses the first schema. The orchestrator wraps all category outputs verbatim in the second schema. The Verifier consumes that Scanner Batch and emits the third schema.

## Category Scanner Output Schema

Return one English output for the single assigned category. The searched category is provisional; the Verifier owns final routing and cross-category deduplication.

```
## Category Scan Report
- Status: <complete | failed>
- Country: <country>
- Geography scope: <country | Europe-ex-UK>
- Date: <YYYY-MM-DD>
- Searched category: <category id>
- Candidates found: <M>
- Search actions: <non-negative integer>
- Open-page attempts: <non-negative integer>
- Open-page successes: <non-negative integer>
- Open-page failures: <non-negative integer>

## Stories

### [<searched category>] <English headline>
- Candidate ID: <category-prefixed ID unique within the Scanner Batch, such as econ-1>
- Publish date (verified): <ISO timestamp or local date>
- Source: <media organisation>
- URL: <full canonical or readable syndicated https URL>
- Byline: <author, organisation byline, or "No byline">
- Open-page result: verified-readable
- Factual excerpt: <verbatim text from the readable article body>
- Key facts: <concise English account of what the article reports>

... (repeat for every qualifying URL; do not merge possible duplicates) ...

## Coverage Note

- <category id>: <brief description of what was found, why authoritative exact-date reporting with readable factual body was sparse, or why Status is failed>
```

Rules:

- `Status: complete` requires meaningful search execution, even when `Candidates found: 0`.
- `Status: failed` means the Scanner could not complete discovery because of a tool or runtime failure; it is not evidence that the category had no qualifying news.
- `Status: complete` requires `Search actions >= 1`. Count individual queries, not batched tool calls.
- Count `Open-page attempts` by individual URL, not batched tool calls.
- `Open-page successes + Open-page failures` must equal `Open-page attempts`.
- `Candidates found` must not exceed `Open-page successes`.

## Scanner Batch Schema

The orchestrator creates one Scanner Batch after all category Scanner invocations finish. It may calculate only the batch header totals and wrap category outputs in active-category order. It must not rewrite, summarize, deduplicate, reroute, or otherwise transform any category output.

```
## Scanner Batch
- Country: <country>
- Geography scope: <country | Europe-ex-UK>
- Date: <YYYY-MM-DD>
- Categories requested: <N>
- Category outputs complete: <N>
- Candidates found: <M>
- Candidate counts by searched category: one `id=<n>` token per category in active-category order
- Tool totals: search=<n> | open_attempts=<n> | open_successes=<n> | open_failures=<n>

## Category Outputs

<!-- BEGIN CATEGORY OUTPUT: <category id> -->
<complete Category Scanner Output reproduced verbatim>
<!-- END CATEGORY OUTPUT: <category id> -->

... (repeat in active-category order) ...
```

The batch is valid only when every requested category has one `Status: complete` output. Candidate IDs remain category-prefixed and unchanged.

## Verifier Output Schema

The Verifier evaluates every Scanner candidate, selects the final Lead for duplicate events, performs final category routing, and emits this English raw-data shape.

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
- Source: <media outlet name>
- Source class: <established-media | reputable-regional | reputable-specialist | sanctioned-syndication>
- Source assessment: <Verifier judgement of claim-level provenance and evidence fit>
- URL: <full canonical https URL>
- Byline: <author, organisation byline, or "No byline">
- Body-source: full
- Geographic nexus: <target country, non-UK European jurisdiction, or EU/pan-European institution>
- UK role: <not-applicable | none | context | external-counterparty>
- Corroborated by: <same-event candidate URLs folded into this Lead; or "None">
- Factual excerpt: <carried verbatim from the selected Scanner candidate>
- Commentary: <Verifier account of what happened and why it matters>
- Verdict: KEEP
- Source verdict: <credible | credible-with-caveat>
- New-information verdict: <original-reporting | document-based-reporting | transparent-syndication | meaningful-follow-up | unclear-but-supported>
- News value: <high | medium | coverage-keep>
- Dedup role: <Lead | Standalone>

... (repeat per kept story) ...

## Dropped Stories

- URL: <full https URL>
- Searched category: <id>
- Reason: <Duplicate-of-#X | Unsupported-source | UK-primary-nexus-excluded | China-source-excluded | No-new-fact | No-meaningful-news-value | Routine-PR | Op-ed | Unsupported-rumour | Celebrity-or-lifestyle | Sports-non-political | China-aid-smallcountry-excluded | Out-of-category-scope | Other: <specific>>

... (repeat per dropped candidate URL) ...

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
