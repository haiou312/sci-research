# Schemas - Minimal Search, Scanner Batch, and Deduplication Formats

Each category-scoped Scanner uses the first schema. The orchestrator wraps all category outputs verbatim in the second schema. The Verifier consumes that Scanner Batch and emits the third schema.

## Category Scanner Output Schema

Return one English output for the single assigned category. This is a `google_news.search_news` results list, not a verification record. Do not call `get_news_article` and do not reject a result because the publisher page may be blocked, paywalled, or unavailable.

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
- URL: <google_news_url returned by search_news, either as a raw URL or a Markdown link>
- Search-result summary: <concise account based only on title, publisher, published_at, and rss_summary returned by search_news>

... (repeat for every useful result; do not merge possible duplicates) ...
```

Rules:

- `Candidates found` must equal the number of story blocks.
- Use only `mcp__google_news__search_news` for the supplied target date, but copy the date exactly as the tool displays it; do not call `get_news_article` merely to prove the date.
- URL presentation is not a validation gate. Accept a raw `news.google.com` URL or a Markdown link whose target is that URL, preserve it verbatim in the Scanner Batch, and never retry or stop a run because of the URL's syntax or domain.
- A blocked, paywalled, snippet-only, dynamically rendered, or currently unavailable page remains a valid result.
- For China, use foreign-media search results only. For `Europe-ex-UK`, exclude results focused primarily or solely on the United Kingdom.
- Do not record or forward `article_id`: it is an MCP-session-local retrieval handle, not durable evidence. Writer and Editor must re-run `search_news` before their own `get_news_article` call.
- Do not score sources, assess news value, deduplicate events, route categories, produce rejection notes, or claim that a result was fetched or verified.

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

The Verifier is a deduplication-only schema adapter, not an editorial gate. It uses no web or MCP tools and judges duplication only from the supplied headline, displayed date, source, URL, and search-result summary. Process candidates in Scanner Batch order. Keep the first occurrence of an underlying event in its original searched category and mark later reports of the same event as duplicates, even when another outlet or category uses different wording. Do not merge related but distinct follow-up developments, reactions, decisions, transactions, or transaction stages. Do not verify dates or facts, assess sources or news value, select a better Lead, reroute, rewrite summaries, or drop a unique result.

```
## Verification Report
- Input count (from Scanner): <N>
- Kept count: <K unique events>
- Duplicate count: <D; N - K>
- Geography scope: <country | Europe-ex-UK>
- Category counts after verification: count retained representatives by their original searched category, in active-category order.
- Mode: deduplication-only

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

... (repeat once per unique event, preserving representative input order) ...

## Duplicate Drops

### DROP_DUPLICATE <dropped Candidate ID> — <headline copied from Scanner>
- Duplicate of: <retained Candidate ID>
- Searched category: <original category of dropped candidate>
- Source: <copied from Scanner>
- URL: <copied from Scanner>
- Matching basis: <one concise statement of the shared underlying event, using only Scanner Batch fields>
- Verdict: DROP_DUPLICATE

... (repeat in Scanner Batch order; write `None` when Duplicate count is 0) ...

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
(include only for a category below `min_per_category`; this records unique-result scarcity after deduplication, not an editorial rejection)

- Category: <id>
- Scanner candidate count: <n>
- Verifier kept count: <unique retained stories in this category>
- Reason: Fewer than <min_per_category> unique results remain in this category after same-event deduplication.
```

Arithmetic and scope rules:

- `Input count = Kept count + Duplicate count`.
- Every Scanner Candidate ID appears exactly once: as a retained `Candidate ID` or a `DROP_DUPLICATE` heading.
- Every duplicate points to one retained Candidate ID; duplicate chains are forbidden.
- A retained story keeps the searched category and input position of its first occurrence. Deduplication never reroutes it.
- `Corroborated by` contains only distinct duplicate URLs and does not authorize merging duplicate summaries into `Factual excerpt` or `Commentary`.
- The only valid DROP verdict is `DROP_DUPLICATE`.
