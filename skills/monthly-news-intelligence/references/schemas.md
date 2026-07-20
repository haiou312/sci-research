# Monthly Pipeline Schemas

Use these schemas exactly. Text fields may span multiple lines, but labels and
ordering are fixed.

## Source Index

`scripts/collect-monthly-reports.py` emits JSON with:

- report identity, aliases, requested month, `as_of`, and language priority;
- active categories;
- coverage dates, found/missing dates, and partial-month state;
- a SHA-256 fingerprint and story counts for every source report;
- every parsed story with a stable ID, source date/language/path, category,
  title, body, and structured APA references.

Treat the JSON as immutable. A downstream ID must match an exact `stories[].id`.

## Category Curator Output

```text
=== Monthly Category Curator Output ===
Status: complete
Country: <country>
Month: <YYYY-MM>
Category: <category id>
Source stories reviewed: <integer>
Primary clusters: <integer>
Alternate clusters: <integer>

PRIMARY 1
Cluster ID: <category>-cluster-01
Working headline: <concise target-language-neutral description>
Coverage dates: <comma-separated ISO dates>
Related story IDs: <comma-separated IDs>
Evidence story IDs: <comma-separated 1-5 IDs>
Monthly significance: <factual editorial rationale>
Synthesis instruction: <chronology and distinctions the Writer must preserve>

ALTERNATE 1
Cluster ID: <category>-alternate-01
Working headline: <description>
Coverage dates: <comma-separated ISO dates>
Related story IDs: <comma-separated IDs>
Evidence story IDs: <comma-separated 1-5 IDs>
Monthly significance: <rationale>
Synthesis instruction: <instruction>

Coverage note: <none OR why fewer than stories_per_category primaries qualify>
```

Repeat PRIMARY and ALTERNATE blocks as needed. A valid zero-result output uses
zero counts, no cluster blocks, and a non-empty Coverage note.

## Curator Bundle

The orchestrator mechanically wraps Curator outputs in active-category order:

```text
=== Monthly Curator Bundle ===
Country: <country>
Month: <YYYY-MM>
Categories expected: <integer>
Categories complete: <integer>

===== BEGIN CATEGORY <category id> =====
<Category Curator Output verbatim>
===== END CATEGORY <category id> =====
```

Do not summarize, reorder, or repair an agent output while constructing the
bundle.

## Monthly Verifier Output

```text
=== Monthly Verifier Output ===
Status: complete
Country: <country>
Month: <YYYY-MM>
Target stories per category: <integer>
Total final stories: <integer>

FINAL CATEGORY: <category id>
Final count: <integer>

STORY <category id>-01
Rank: 1
Working headline: <description>
Evidence story IDs: <comma-separated 1-5 exact IDs>
Source dates: <comma-separated ISO dates>
Selection reason: <concise reason>
Merge instruction: <chronology, stage and uncertainty to preserve>

Category gap note: <none OR why fewer than target qualify>

CROSS-CATEGORY DECISIONS
- <duplicate/routing decision, or none>
```

Emit every active category once in order. Story IDs restart at `01` per
category. Evidence IDs must exist in the source index. A source story ID may
support only one final monthly story.

## Monthly Fact Manifest

Write YAML:

```yaml
schema_version: 1
country: "<country>"
month: "YYYY-MM"
source_index: "<absolute path>"
coverage:
  reports_found: 0
  dates_found: []
  missing_dates: []
stories:
  - id: "econ-01"
    category: "econ"
    evidence_story_ids: []
    source_dates: []
    headline_identity: ""
    chronology:
      - date: "YYYY-MM-DD"
        development: ""
    people: []
    organizations: []
    locations: []
    numbers: []
    dates_and_times: []
    quotations: []
    uncertainty_and_stage: []
    references:
      - apa: ""
        url: "https://..."
```

Copy factual values and reference metadata only from the selected evidence story
blocks. Deduplicate references by exact URL while preserving first-evidence
order. Do not normalize away distinctions between proposal, agreement, approval,
completion, allegation, estimate, or confirmed result.
