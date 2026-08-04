# CRD VI Brave Search MCP Method

Use the globally configured MCP server named `brave_search` for every CRD VI
search and discovery operation. Do not use Google News or Codex native web
search as a fallback.

## Required tools and preflight

The current Codex task must expose these exact tools:

- `mcp__brave_search__brave_web_search` for official-source, tracker, legal,
  national-portal, and general web discovery;
- `mcp__brave_search__brave_news_search` for the four exact-week regulatory-news
  lanes.

Use `mcp__brave_search__brave_llm_context` when available for source-grounded
context retrieval. It is query based and is not an arbitrary URL opener.

Before research:

1. inspect the current task's available tools;
2. stop if either required tool is absent;
3. make one minimal `brave_web_search` capability probe for
   `"Directive (EU) 2024/1619" site:eur-lex.europa.eu`, with `country: ALL`,
   `search_lang: en`, `count: 1`, and `text_decorations: false`;
4. stop on authentication, plan, startup, Docker, or transport failure.

When preflight fails, report that the user must run
`codex mcp get brave_search`, configure the MCP server's `BRAVE_API_KEY`, and
start a new Codex task. Never install, re-register, or rewrite the user's global
MCP configuration inside a CRD VI run.

## Web search

Call `mcp__brave_search__brave_web_search` with:

```json
{
  "query": "<focused query, at most 400 characters and 50 words>",
  "country": "ALL",
  "search_lang": "en",
  "count": 20,
  "offset": 0,
  "safesearch": "moderate",
  "text_decorations": false,
  "spellcheck": true,
  "result_filter": ["web", "query"]
}
```

Use the relevant supported two-letter country code and local `search_lang` for
a national search when it improves recall. Use `country: ALL` for EU-wide or
cross-border discovery. Add `freshness: YYYY-MM-DDtoYYYY-MM-DD` only when the
search concerns a defined date window; freshness is a discovery filter, not
proof of a source's legal or publication date. Use `site:` and quoted titles or
measure identifiers to target official domains. Paginate with `offset` only
when the first result set is insufficient and the method requires exhaustive
discovery.

## News search

Run each lane from `news-sources.json` with its declared `news_tool`. Copy
`news_parameters` from the same registry, add the lane-specific query, and
resolve the freshness placeholders to the exact reporting window. The registry
is the machine-readable authority for news-search defaults; do not restate or
override them elsewhere in this skill.

Use local-language follow-up queries only for a concrete country lead. The
Brave discovery date and result description are not sufficient to keep an
item: open the canonical publisher URL and verify its displayed date and
substance under `news-method.md`.

## Source context and direct pages

When useful, call `mcp__brave_search__brave_llm_context` with a focused query
containing the exact title, official domain, measure identifier, and CRD VI
terms. Keep `maximum_number_of_urls` small, enable source metadata, and accept a
chunk only when its returned source URL matches the authority being checked.

Brave Search MCP does not expose an arbitrary URL-fetch tool. Directly opening
a known canonical URL is therefore allowed solely to read and verify that page,
including pagination, displayed dates, legal stage, and substantive content.
This is page retrieval, not permission to use native `search_query`, Google
News, or another search provider. If the canonical page cannot be opened and
Brave context does not expose the required evidence, apply the documented
unavailable or carry-forward rule rather than switching search providers.

## Audit

For every query, record the provider (`brave_search`), exact MCP tool name,
query, non-secret parameters, retrieval time, and returned URLs in the relevant
audit JSON. For every retained fact, separately record the canonical page that
was directly opened or the exact Brave-context source URL used. Never store API
keys, MCP environment variables, full article bodies, or generated Brave
summaries in audit artifacts.
