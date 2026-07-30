# Schemas - Minimal Search, Scanner Batch, and Pass-Through Formats

Each category-scoped Scanner uses the first schema. The orchestrator wraps all category outputs verbatim in the second schema. The Verifier consumes that Scanner Batch and emits the third schema.

## Category Scanner Output Schema

Return one English output for the single assigned category. This is a search-results list, not a verification record. Do not open result pages and do not reject a result because the page may be blocked, paywalled, or unavailable.

```
## Category Scan Report
- Status: complete
- Country: <country>
- Geography scope: <country | Europe-ex-UK>
- Date: <YYYY-MM-DD>
- Searched category: <category id>
- Candidates found: <M>

## Stories

### [<searched category>] <headline shown by search>
- Candidate ID: <category-prefixed ID unique within the Scanner Batch, such as econ-1>
- Publish date (search result): <date displayed by search, relative date, or "Not shown">
- Source: <source shown by search>
- URL: <result URL>
- Search-result summary: <concise account based only on the search result>

... (repeat for every useful result; do not merge possible duplicates) ...
```

Rules:

- `Candidates found` must equal the number of story blocks.
- Search for the supplied target date, but copy the date exactly as search displays it; do not open a page merely to prove the date.
- A blocked, paywalled, snippet-only, dynamically rendered, or currently unavailable page remains a valid result.
- For China, use foreign-media search results only. For `Europe-ex-UK`, exclude results focused primarily or solely on the United Kingdom.
- Do not score sources, assess news value, deduplicate events, route categories, produce rejection notes, or claim that a result was opened or verified.

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

## Category Outputs

<!-- BEGIN CATEGORY OUTPUT: <category id> -->
<complete Category Scanner Output reproduced verbatim>
<!-- END CATEGORY OUTPUT: <category id> -->

... (repeat in active-category order) ...
```

The batch is valid only when every requested category has one `Status: complete` output. Candidate IDs remain category-prefixed and unchanged.

## Verifier Output Schema

The Verifier is a schema adapter, not an editorial gate. It forwards every Scanner candidate in the same order and searched category. It does not use WebSearch, open pages, verify dates, assess sources, score news value, deduplicate, reroute, or drop results.

```
## Verification Report
- Input count (from Scanner): <N>
- Kept count: <N; must equal Input count>
- Geography scope: <country | Europe-ex-UK>
- Category counts after verification: copy the Scanner counts in active-category order.
- Mode: pass-through

## Kept Stories

### [<searched category>] <headline copied from Scanner>
- Publish date (search result): <copied from Scanner>
- Source: <copied from Scanner>
- URL: <copied from Scanner>
- Body-source: search-result
- Corroborated by: None
- Factual excerpt: <Search-result summary copied verbatim from Scanner>
- Commentary: <same search-result summary, or a shorter faithful restatement>
- Verdict: KEEP
- Forwarding note: unverified-search-result

... (repeat per kept story) ...

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
(include only for a category below `min_per_category`; this records search scarcity, not an editorial rejection)

- Category: <id>
- Scanner candidate count: <n>
- Verifier kept count: <same as Scanner candidate count>
- Reason: Search returned fewer than <min_per_category> results for this category.
```
