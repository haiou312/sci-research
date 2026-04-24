# Source Matrix — News + Reddit + X (MVP)

Loaded by the Scanner. Defines the three sources the reputation-track MVP covers, per-source search patterns, and date-verification methods.

## Coverage Scope

| Source | Tool | Reliability | Coverage |
|---|---|---|---|
| News | WebSearch + WebFetch | ★★★★★ | T1-T4 wire + financial + industry outlets |
| Reddit | `mcp__apidirect__search_reddit` (single call) | ★★★★☆ | Public subreddits, full content |
| X (Twitter) | `mcp__apidirect__search_twitter` (single call) | ★★★★☆ | Full public-post stream (not just Google-indexed) |

**Out of scope (disclosed in HTML footer):** Facebook and Threads are intentionally excluded in v1 — not for tooling reasons (apidirect offers `search_facebook_*`) but to keep the alert concise; v2 may expand.

## apidirect Quota Budget

`mcp__apidirect__*` tools share a **50-token/month** free quota. Reputation-track's discipline:

| Source | Calls per `/reputation-track` run | Tokens burned |
|---|---|---|
| News (WebSearch) | N (5-10 queries) | 0 (WebSearch is free) |
| Reddit (apidirect) | **exactly 1** | 1 |
| X (apidirect) | **exactly 1** | 1 |
| **Per-run total** | — | **2** |

At 2 tokens/run, the 50-token quota supports **~25 runs/month**. If you run daily, you exhaust the quota in ~3.5 weeks. If you run weekly, you have 6× headroom.

**Hard rules** (enforced in `agents/reputation-scanner.md`):
- No retries on failure — if apidirect returns an error or zero results, emit empty `raw_candidates` with a `coverage_notes` line. Do not retry with a different query.
- No pagination — always `page=1` / `pages=1`. Extra pages cost extra tokens.
- No per-executive loop — build ONE compound query covering company + ticker + top 3 executives, ≤500 chars.

If quota is exhausted, apidirect calls will start failing; Scanner should emit empty candidates for the affected sources rather than retrying.

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

## Reddit — `mcp__apidirect__search_reddit` (single call)

Reddit's public `.json` endpoint is now blocked by Reddit's anti-bot measures for WebFetch user agents. Use `mcp__apidirect__search_reddit` instead — one call per `/reputation-track` run.

**Call contract:**

```
mcp__apidirect__search_reddit(
  query: <compound string, ≤500 chars>,
  sort_by: "most_recent",
  page: 1
)
```

**Compound query template** (fits 500-char limit for most companies):

```
"{official_name}" OR "{ticker}" OR "{exec1_name}" OR "{exec2_name}" OR "{exec3_name}"
```

Executives are the top 3 from the Resolver output (typically CEO, CFO, Chair). Drop lower-seniority execs first if the query would exceed 500 chars.

**Response fields to parse** (per post returned):
- `title`, `selftext`, `url`, `permalink`
- `created_utc` (Unix timestamp — **authoritative date** for verification)
- `subreddit`, `author`, `score`, `num_comments`

**Client-side filters at Scanner stage:**
- `created_utc` within target `date` window (±24h UTC)
- Drop accounts with age < 30 days (likely throwaway)
- Drop items with `score ≤ 1` AND `num_comments == 0` (no community traction)
- Keep `score > 50` or `num_comments > 10` as higher-signal items
- Cap at 40 candidates

## X (Twitter) — `mcp__apidirect__search_twitter` (single call)

X blocks direct scraping without login, and Google's index of x.com is sparse enough to be unreliable. Use `mcp__apidirect__search_twitter` instead — one call per run.

**Call contract:**

```
mcp__apidirect__search_twitter(
  query: <same compound string as Reddit, ≤500 chars>,
  sort_by: "most_recent",
  pages: 1
)
```

**Important**: `pages=1` is mandatory. Each extra page is an extra token; the quota forbids pagination loops.

**Response fields to parse** (per tweet returned):
- Tweet text, tweet ID, permalink
- Created-at timestamp (authoritative date for verification)
- Author handle, display name, verified status, follower count
- Engagement (likes, retweets, replies)

**Client-side filters at Scanner stage:**
- Tweet date within target `date` window (±24h UTC)
- Drop new/throwaway accounts (follower count < 100 AND age < 30 days if age is exposed)
- Drop zero-engagement tweets
- Record `verified` flag + `follower_count` for the Classifier's credibility weighting
- Cap at 40 candidates

## Date Verification

Every candidate — across all three sources — must pass date verification before being emitted:

| Source | Verification method |
|---|---|
| News | `WebFetch` article; parse `<meta property="article:published_time">` or visible byline date |
| Reddit | `created_utc` in apidirect response (authoritative) |
| X | Tweet `created_at` in apidirect response (authoritative) |

Tolerance: ±24 hours from target `date` (accommodates timezone differences). Reject anything outside this window.

## Hard Cap

Scanner per source: maximum **40 raw candidates**. If more pass date verification, prefer higher-tier sources (News) and higher-signal items (Reddit score). Over-collecting inflates Classifier cost without improving coverage.
