# Schemas - Capped Search, Scanner Batch, Deduplication, and Selection

Scanner, batch, and Verifier handoff formats.

## Category Scanner Output Schema

Return one English report for the assigned category.

```
## Category Scan Report
- Status: complete | partial | unavailable
- Handoff note: <None, or a concise explanation of partial/unavailable output>
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
- URL: <google_news_url returned by search_news, either as a raw URL or a Markdown link>
- Search-result summary: <concise account based only on title, publisher, published_at, and rss_summary returned by search_news>

... (repeat for at most 10 distinct search results; do not merge possible same-event coverage) ...
```

Format constraints:

- `Candidates found` equals the story-block count and is at most 10.
- Copy displayed metadata. Missing values become `Not shown`; never invent them.
- A raw `news.google.com` URL or a Markdown link is valid. Preserve it verbatim.
- Do not include session-local `article_id` or claim that an article was fetched or verified.

## Scanner Batch Schema

The orchestrator wraps one normalized block per active category in order. It caps overflow at 10, preserves parseable stories, repairs IDs/counts, uses `Not shown` for missing fields, and inserts an `unavailable` zero-candidate block when nothing is parseable.

```
## Scanner Batch
- Country: <country>
- Geography scope: <country | Europe-ex-UK>
- Date: <YYYY-MM-DD>
- Categories requested: <N>
- Category outputs usable: <N with one or more parseable candidates>
- Category outputs unavailable: <N>
- Candidates found: <M>
- Candidate counts by searched category: one `id=<n>` token per category in active-category order

## Category Outputs

<!-- BEGIN CATEGORY OUTPUT: <category id> -->
<capped complete/partial output, normalized parseable output, or unavailable zero-candidate placeholder>
<!-- END CATEGORY OUTPUT: <category id> -->

... (repeat in active-category order) ...
```

The batch contains exactly one block per active category and 0-10 candidates per block. All three statuses are valid. Only an all-category zero-candidate batch has no downstream content.

## Verifier Output Schema

The Verifier emits one complete report from the Scanner Batch.

```
## Verification Report
- Input count (from Scanner): <N>
- Kept count: <K selected unique events>
- Duplicate count: <D later same-event candidates>
- Not-selected count: <S unique event representatives omitted by the per-category maximum>
- Geography scope: <country | Europe-ex-UK>
- Category counts after verification: count final retained representatives by their original searched category, in active-category order; every count is 0-6.
- Mode: deduplicate-and-select | mechanical-fallback

## Kept Stories

### [<searched category>] <headline copied from Scanner>
- Candidate ID: <retained Scanner Candidate ID>
- Publish date (search result): <copied from Scanner>
- Source: <copied from Scanner>
- URL: <copied from Scanner>
- Body-source: search-result
- Corroborated by: <distinct URLs of candidates dropped as duplicates of this story, in Scanner Batch order, or None>
- Factual excerpt: <Search-result summary copied verbatim from Scanner>
- Commentary: <Search-result summary copied verbatim from Scanner>
- Verdict: KEEP
- Forwarding note: first-occurrence representative; unverified-search-result

... (repeat once per selected unique event, preserving representative input order) ...

## Duplicate Drops

### DROP_DUPLICATE <dropped Candidate ID> — <headline copied from Scanner>
- Duplicate of: <first-occurrence representative Candidate ID; it may be KEEP or DROP_NOT_SELECTED>
- Searched category: <original category of dropped candidate>
- Source: <copied from Scanner>
- URL: <copied from Scanner>
- Matching basis: <one concise statement of the shared underlying event, using only Scanner Batch fields>
- Verdict: DROP_DUPLICATE

... (repeat in Scanner Batch order; write `None` when Duplicate count is 0) ...

## Selection Drops

### DROP_NOT_SELECTED <unique representative Candidate ID> — <headline copied from Scanner>
- Searched category: <original category copied from Scanner>
- Source: <copied from Scanner>
- URL: <copied from Scanner>
- Selection basis: Category had more than 6 unique events; other retained events ranked higher on direct relevance, concrete target-date development, material consequence, or factual clarity.
- Verdict: DROP_NOT_SELECTED

... (repeat in Scanner Batch order; write `None` when Not-selected count is 0) ...

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
(include only for a category below `min_per_category`; this records scarcity after exact-result cleanup, event deduplication, and selection, not a request to add filler)

- Category: <id>
- Scanner candidate count: <n; never above 10>
- Unique event count before selection: <n>
- Verifier kept count: <selected retained stories in this category; never above 6>
- Reason: Fewer than <min_per_category> unique qualifying events were available; all available events were retained and no filler was added.
```

Integrity rules:

- `Input count = Kept count + Duplicate count + Not-selected count`.
- Every Scanner Candidate ID appears exactly once: as a retained `Candidate ID`, a `DROP_DUPLICATE` heading, or a `DROP_NOT_SELECTED` heading.
- Every duplicate points directly to its first-occurrence event representative, which may be retained or `DROP_NOT_SELECTED`; duplicate chains are forbidden.
- Retained stories preserve first-occurrence order and searched category.
- `Corroborated by` contains only distinct duplicate URLs.
- Each category retains at most 6 events; never add filler.
- The only valid DROP verdicts are `DROP_DUPLICATE` and `DROP_NOT_SELECTED`.

### Non-blocking Verifier fallback

If Verifier output is unusable, create `Mode: mechanical-fallback`: keep the first 6 candidates per original category in batch order; mark overflow `DROP_NOT_SELECTED`; emit no duplicates; copy Scanner fields and summaries; set `Body-source: search-result`, `Corroborated by: None`, and `Forwarding note: mechanical-fallback; unverified-search-result`; recalculate counts and gaps. Continue downstream.
