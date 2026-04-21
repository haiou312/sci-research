# Output Schemas — Resolver / Scanner / Classifier

Data handoff between stages is via subagent prompt text (not files). Each stage returns its output in the exact shape below so downstream stages can parse it. The orchestrator passes upstream output verbatim into downstream prompts.

## Resolver Output Schema

```yaml
official_name: <string>                # e.g. "Apple Inc."
ticker: <string or null>               # e.g. "AAPL" (null if unlisted)
country: <ISO 3166-1 alpha-2>          # e.g. "US", "CN", "JP"
aliases:
  - <string>                           # common short forms, e.g. "Apple"
  - <string>                           # local-language name
executives:
  - name: <full name>
    title: <CEO | CFO | COO | Chair | CTO | President | ...>
    source_url: <URL that was WebFetched>
resolution_confidence: high | medium | low
resolution_notes: <free text; required if confidence is not high>
```

## Scanner Output Schema (one per source)

Each of the three Scanner instances (news / reddit / x) emits this:

```yaml
source: news | reddit | x
query_count: <int>                     # number of distinct queries executed
raw_candidates:
  - url: <absolute URL>
    outlet: <string>                   # e.g. "Reuters", "r/investing", "x.com/@handle"
    tier: T1 | T2 | T3 | T4 | social
    title_or_excerpt: <string>
    published_at: <ISO 8601 datetime>
    author_or_handle: <string>
    date_verified: true | false
    verification_method: webfetch | json | snippet
    raw_snippet: <string, max 1000 chars>
coverage_notes: <free text; flag gaps, blocked fetches, etc.>
```

## Classifier Output Schema

```yaml
total_items_in: <int>                  # sum of raw_candidates across 3 scanners
total_items_kept: <int>                # promoted to kept_items
total_items_dropped: <int>             # everything else
kept_items:
  - category: Legal | Financial | Operational | Ethics | Leadership | Product | Activism
    severity: critical | high | medium | low
    subject: company | executive:<name>
    quote: <verbatim text, max 500 chars>
    source_url: <absolute URL>
    source_outlet: <string>
    source_tier: T1 | T2 | T3 | T4 | social
    published_at: <ISO 8601>
    corroborating_urls: [<string>, ...]
    confidence: high | medium | low
dropped_items:
  - url: <absolute URL>
    drop_reason: neutral | no_verbatim_quote | date_mismatch | duplicate | unverifiable | below_severity_min | low_credibility_implausible
```

## Writer Output

Not a schema — the Writer produces an HTML file at the path specified in `out_html`. File must be UTF-8, inline CSS only, valid HTML. See `references/html-template.md`.
