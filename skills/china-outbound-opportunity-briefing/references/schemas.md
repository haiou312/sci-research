# Pipeline Schemas

## Category Scanner Output

```text
SCANNER_OUTPUT
Lane: <lane>
Status: complete | failed
Date range: <YYYY-MM-DD> to <YYYY-MM-DD>
Search actions: <integer>
Open-page attempts: <integer>
Open-page successes: <integer>
Open-page failures: <integer>
Candidates found: <integer>

CANDIDATES

Candidate: <lane>-<N>
Event date: <YYYY-MM-DD>
Title: <title>
Source: <publisher>
URL: <canonical URL>
Source type: official | company | established-media | specialist | research
Readable body: yes
Companies: <comma-separated names or none>
Countries: <comma-separated countries>
Chinese nexus: confirmed | probable | requires-verification | not-applicable
Transaction stage: <rubric stage>
Companies House numbers: <comma-separated company numbers or none>
Factual excerpt: <source-backed factual paragraph>
Why it may matter: <one concise sentence>
Potential banking angles: <comma-separated hypotheses or none>
Image URL: <direct or page image URL or none>
Image source: <owner/publisher or none>
Image rights note: official-press | official-chart | licensed-media | link-only | unknown | none

...repeat...

COVERAGE_NOTES
<short description of searched angles and gaps>
END_SCANNER_OUTPUT
```

Every admitted candidate must have a readable opened source. `Candidates found` must not exceed `Open-page successes`.

## Scanner Batch

```text
SCANNER_BATCH
Date range: <date_from> to <date_to>
Lanes expected: 5
Lanes complete: 5
Total search actions: <integer>
Total open-page attempts: <integer>
Total open-page successes: <integer>
Total open-page failures: <integer>
Total candidates: <integer>

BEGIN LANE uk_economy
<verbatim Category Scanner Output>
END LANE uk_economy

BEGIN LANE outbound_europe
...
END LANE outbound_europe

BEGIN LANE cross_border_ma
...
END LANE cross_border_ma

BEGIN LANE investment_footprint
...
END LANE investment_footprint

BEGIN LANE companies_house_discovery
...
END LANE companies_house_discovery
END_SCANNER_BATCH
```

## Companies House Analyst Output

```text
COMPANIES_HOUSE_ANALYSIS
Status: complete
Registry data status: available | unavailable | skipped | partial
Monitored universe: <watchlist/company-number coverage statement>

ENTITY_FINDINGS

Entity finding: CH-<N>
UK entity: <registered name>
Company number: <number>
Chinese parent or nexus: <name or unknown>
Nexus confidence: confirmed | probable | unverified
Nexus evidence: <specific evidence and URLs>
Observed change: <incorporation/status/name/address/SIC/officer/PSC/capital/charge/filing>
Effective or filing date: <YYYY-MM-DD>
Change evidence: <Companies House field/filing and URL>
Materiality: high | medium | monitor | immaterial
Commercial interpretation: <fact-separated interpretation>
Potential banking angles: <hypotheses or none>
Watch next: <next filing/event or none>

...repeat...

EXCLUDED_OR_UNVERIFIED
- <entity, company number, reason>

COVERAGE_LIMITS
<API, watchlist, ownership, and discovery limitations>
END_COMPANIES_HOUSE_ANALYSIS
```

## Verifier Output

```text
VERIFIER_OUTPUT
Date range: <date_from> to <date_to>
Candidates reviewed: <integer>
Selected: <integer>
Dropped: <integer>

KEEP

Item: KEEP-<N>
Final section: uk_economy | outbound_europe | cross_border_ma | investment_footprint | companies_house
Priority: high | medium | monitor
Event date: <YYYY-MM-DD>
Headline: <Chinese-ready factual headline>
Primary source: <URL>
Corroborating sources: <URLs or none>
Companies: <names>
Countries: <countries>
Chinese nexus: confirmed | probable | not-applicable
Transaction stage: <stage>
Verified facts: <dense factual paragraph>
Key impact: <what changes for Chinese enterprises or UK/Europe operations>
Opportunity hypothesis: <specific potential banking needs, explicitly framed as hypotheses>
Recommended follow-up: <named action and target>
Watch triggers: <dated or stage-based triggers>
Image URL: <URL or none>
Image source: <source or none>
Image rights note: <policy label>
Companies House evidence: <company number/change or none>
Selection commentary: <why this is selected>

...repeat...

DROP
- Candidate: <ID>
  URL: <URL>
  Reason: <precise reason>

COVERAGE_GAPS
- <lane or topic and reason>
END_VERIFIER_OUTPUT
```

## Fact Manifest

Write YAML:

```yaml
report:
  date_from: YYYY-MM-DD
  date_to: YYYY-MM-DD
items:
  - id: KEEP-1
    section: uk_economy
    primary_url: https://...
    allowed:
      names: []
      dates: []
      amounts: []
      percentages: []
      transaction_stage: not-applicable
      company_numbers: []
      registry_changes: []
      quotations: []
      image:
        url: null
        source: null
        rights_note: none
    source_anchors:
      - url: https://...
        excerpt: "..."
```

## Writer Markdown

The exact report structure is defined in `output-spec.md`. The Writer must create the complete file in one `apply_patch`.
