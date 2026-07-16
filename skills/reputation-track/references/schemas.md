# Pipeline E Schemas

The Scanner emits the first shape. The Verifier consumes it and emits the second.

## Scanner Output Schema

```yaml
status: ok | needs-clarification
resolution_note: <empty when status=ok; otherwise explain the ambiguity>
company:
  official_name: <Yahoo Finance company name>
  ticker: <ticker>
  yahoo_url: <opened Yahoo Finance company or profile URL>
executives:
  - name: <current key executive>
    title: <current title>
date: <YYYY-MM-DD>
candidates:
  - subject: company | executive:<name>
    source_type: media | social
    source_name: <media outlet or social account/platform>
    url: <absolute opened URL>
    published_at: <ISO timestamp or exact local date>
    evidence_excerpt: <verbatim relevant text from the opened page>
```

When `status: needs-clarification`, emit an empty `executives` and `candidates` list.

## Verifier Output Schema

```yaml
company:
  official_name: <carried from Scanner>
  ticker: <carried from Scanner>
date: <YYYY-MM-DD>
findings:
  - subject: company | executive:<name>
    severity: high | medium | low
    headline: <short factual headline>
    what_happened: <concise factual description>
    reputation_impact: <why this may harm reputation>
    evidence_excerpt: <verbatim source text>
    source_type: media | social
    source_name: <media outlet or social account/platform>
    url: <absolute URL>
    published_at: <ISO timestamp or exact local date>
```

An empty `findings` list means the run is clean.
