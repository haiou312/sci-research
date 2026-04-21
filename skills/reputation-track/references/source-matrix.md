# Source Matrix — News + Reddit + X (MVP)

Loaded by the Scanner. Defines the three sources the reputation-track MVP covers, per-source search patterns, and date-verification methods.

## Coverage Scope

| Source | Tool | Reliability | Coverage |
|---|---|---|---|
| News | WebSearch + WebFetch | ★★★★★ | T1-T4 wire + financial + industry outlets |
| Reddit | WebFetch `.json` endpoint | ★★★★☆ | Public subreddits, full content |
| X (Twitter) | WebSearch `site:x.com` + nitter fallback | ★★☆☆☆ | Only Google-indexed public posts |

**Out of scope (disclosed in HTML footer):** Facebook and Threads are intentionally excluded in v1 — public-post discoverability via Google is too sparse to be trustworthy.

## News — Search Patterns

Use the T1-T4 tier hierarchy from `rules/research/news-source.md`. Query templates (substitute `<company>` with `official_name`, `<ticker>`, or an alias; `<exec_name>` for each executive from the Resolver; `<date_en>` with e.g. `"April 21, 2026"`):

```
"<company>" <date_en>
"<ticker>" <date_en>
"<exec_name>" "<company>" <date_en>
"<company>" scandal OR lawsuit OR probe OR investigation OR fine OR recall OR controversy OR downgrade <date_en>
"<exec_name>" resign OR "step down" OR fired OR charged OR allegation <date_en>
"<company>" data breach OR outage OR leak OR violation <date_en>
```

Each query must produce both tier-mixed results and tier-focused results. Prefer T1-T2 wire/financial outlets when available. T4 industry outlets are acceptable as corroboration.

For every candidate URL: `WebFetch` and verify publication date matches target `date` (±24h for timezone) before admitting.

## Reddit — Public JSON Endpoint

Reddit's `.json` suffix works on any public URL without auth. Query patterns:

```
WebFetch https://www.reddit.com/search.json?q=<URL-encoded query>&sort=new&t=day&limit=50
```

Queries:
- `"<company>"`
- `"<ticker>"`
- `"<exec name>"`

Also scan high-signal subreddits directly if domain-relevant (e.g. `r/investing`, `r/stocks`, `r/<industry>`):

```
WebFetch https://www.reddit.com/r/<sub>/search.json?q=<company>&restrict_sr=on&sort=new&t=day
```

Parse `data.children[].data`:
- `title`, `selftext`, `url`, `permalink`
- `created_utc` (Unix timestamp — **authoritative date** for verification)
- `subreddit`, `author`, `score`, `num_comments`

**Filter at the Scanner stage:**
- `created_utc` within target `date` window (±24h)
- Drop accounts with age < 30 days (likely throwaway)
- Drop items with `score <= 1` and `num_comments == 0` (no community traction)
- Keep `score > 50` or `num_comments > 10` as higher-signal items

## X (Twitter) — Search via Google

X blocks direct scraping without login. Coverage is limited to Google's public index.

```
WebSearch site:x.com OR site:twitter.com "<company>" <date_en>
WebSearch site:x.com OR site:twitter.com "<exec name>" <date_en>
```

Fallback when Google returns sparse results:

```
WebSearch site:nitter.net "<company>" <date_en>
```

Nitter instances are intermittently up. If `WebFetch` on a nitter URL fails, accept the sparse coverage — do not retry more than twice.

**Authority signals to record (even if partial):**
- Verified checkmark evidence in snippet (blue/gold)
- Follower count if the snippet shows it
- Account handle for reader verification

## Date Verification

Every candidate — across all three sources — must pass date verification before being emitted:

| Source | Verification method |
|---|---|
| News | `WebFetch` article; parse `<meta property="article:published_time">` or visible byline date |
| Reddit | `created_utc` in JSON response (authoritative) |
| X | Snippet date if visible; otherwise Google's indexed date; otherwise drop |

Tolerance: ±24 hours from target `date` (accommodates timezone differences). Reject anything outside this window.

## Hard Cap

Scanner per source: maximum **40 raw candidates**. If more pass date verification, prefer higher-tier sources (News) and higher-signal items (Reddit score). Over-collecting inflates Classifier cost without improving coverage.
