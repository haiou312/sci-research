# Source Matrix — News + Reddit + X (MVP)

Loaded by the Scanner. Defines the three sources the reputation-track MVP covers, per-source discovery patterns, and date-verification methods.

## Coverage Scope

| Source | Tool | Reliability | Coverage |
|---|---|---|---|
| News | WebSearch `search` + `open_page` | ★★★★★ | T1-T4 wire + financial + industry outlets |
| Reddit | WebSearch `search` + `open_page` | ★★☆☆☆ | Public Reddit threads that are search-indexed and openable |
| X (Twitter) | WebSearch `search` + `open_page` | ★★☆☆☆ | Public X/Twitter posts that are search-indexed and openable |

**Out of scope (disclosed in HTML footer):** Facebook and Threads are intentionally excluded in v1. Reddit and X coverage is also limited to publicly indexed, retrievable pages; the Scanner does not use platform APIs, browser automation, direct scraping, or MCP tools.

## Social-Search Rules

- Use WebSearch `search` to discover candidates and `open_page` to inspect the canonical post/thread page.
- Search-result snippets and their dates are discovery metadata only. They never establish a claim or publication time.
- A social candidate enters `raw_candidates` only after `open_page` exposes a timestamp within the target date ±24h.
- If a public post is not indexed, cannot be opened, requires login, or lacks a retrievable timestamp, record the gap in `coverage_notes` and drop it.
- Do not fabricate account age, engagement, verification status, author details, or post text that the opened page does not show.

## News — Search Patterns

Use the T1-T4 tier hierarchy from `references/news-source.md`. Query templates (substitute `<company>` with `official_name`, `<ticker>`, or an alias; `<exec_name>` for each executive from the Resolver; `<date_en>` with e.g. `"April 21, 2026"`):

```
"<company>" <date_en>
"<ticker>" <date_en>
"<exec_name>" "<company>" <date_en>
"<company>" scandal OR lawsuit OR probe OR investigation OR fine OR recall OR controversy OR downgrade <date_en>
"<exec_name>" resign OR "step down" OR fired OR charged OR allegation <date_en>
"<company>" data breach OR outage OR leak OR violation <date_en>
```

Each query must produce both tier-mixed results and tier-focused results. Prefer T1-T2 wire/financial outlets when available. T4 industry outlets are acceptable as corroboration.

For every candidate URL: use WebSearch `open_page` and verify publication date matches target `date` (±24h for timezone) before admitting.

## Reddit — Public Search-Indexed Threads

Use separate searches; do not call Reddit APIs or `.json` endpoints. Replace placeholders with Resolver data and run the most relevant 3-6:

```
site:reddit.com "<company>" "<date_en>"
site:reddit.com "<ticker>" "<date_en>"
site:reddit.com "<exec_name>" "<company>" "<date_en>"
site:reddit.com "<company>" scandal OR lawsuit OR probe OR investigation OR fine OR recall OR outage "<date_en>"
```

For every promising result:

1. Keep only a canonical public Reddit thread/post URL.
2. Open its canonical URL with `open_page`.
3. Extract the post timestamp from opened-page text, structured metadata, or the permalink. It must fall within `date` ±24h.
4. Record subreddit, author, score, and comment count only if exposed by the opened page.
5. Drop threads that cannot be opened or whose timestamp cannot be verified. Explain the gap in `coverage_notes`.

## X (Twitter) — Public Search-Indexed Posts

Use separate searches; do not call X APIs or direct scrapers. Search `x.com` first and add `twitter.com` when a legacy permalink is useful. Replace placeholders with Resolver data and run the most relevant 3-6:

```
site:x.com "<company>" "<date_en>"
site:x.com "<ticker>" "<date_en>"
site:x.com "<exec_name>" "<company>" "<date_en>"
site:x.com "<company>" scandal OR lawsuit OR probe OR investigation OR fine OR recall OR outage "<date_en>"
site:twitter.com "<company>" "<date_en>"
```

For every promising result:

1. Keep only a canonical public post URL matching `x.com/<handle>/status/<id>` or `twitter.com/<handle>/status/<id>`.
2. Open its canonical URL with `open_page`.
3. Extract the created timestamp from opened-page text, structured metadata, or a visible post timestamp. It must fall within `date` ±24h.
4. Record handle, visible verification indicators, follower count, and engagement only if exposed by the opened page.
5. Drop posts that cannot be opened or whose timestamp cannot be verified. Explain the gap in `coverage_notes`.

## Date Verification

Every candidate — across all three sources — must pass date verification before being emitted:

| Source | Verification method |
|---|---|
| News | WebSearch `open_page` article; parse `<meta property="article:published_time">` or visible byline date |
| Reddit | WebSearch `open_page` canonical thread/post; extract timestamp from opened-page text or structured metadata |
| X | WebSearch `open_page` canonical post; extract created timestamp from opened-page text or structured metadata |

Tolerance: ±24 hours from target `date` (accommodates timezone differences). Reject anything outside this window.

## Hard Cap

Scanner per source: maximum **40 raw candidates**. If more pass date verification, prefer higher-tier sources (News) and higher-signal items when engagement is visible (Reddit/X). Over-collecting inflates Classifier cost without improving coverage.
