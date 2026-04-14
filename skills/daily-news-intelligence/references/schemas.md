# Schemas — Scanner and Verifier Output Formats

Loaded by the Scanner and Verifier stages. Not needed by the Writer.

## Scanner Output Schema

Scanner must return exactly this shape (English raw data — no translation):

```
## Scan Summary
- Country: <country>
- Date: <YYYY-MM-DD>
- Candidates fetched: <N>
- Candidates kept: <M>
- Category counts: Economy=<n1> | Politics=<n2> | Technology=<n3> | Society=<n4> | Other=<n5>

## Stories

### [Category] <English headline>
- Publish date (verified): <ISO timestamp or local date from article>
- Source: <outlet name> [T1|T2|T3|T4]
- URL: <full https URL>
- Byline: <author name or "No byline">
- Factual excerpt (≥200 words English): <fact-only extract with numbers, named officials with titles, direct quotations in quote marks, explicit time references>
- Commentary: <verbatim analyst / official / institutional commentary from the article, or exactly "No analyst commentary in source">

... (repeat per story) ...

## Category Coverage Gap   (include only if any category < min_per_category)
- Category: <name>
- Queries attempted: <q1>, <q2>, <q3>
- Reason: <single sentence>
```

## Verifier Output Schema

Verifier must consume the Scanner bundle and emit exactly this shape (still English raw data — no translation, no Writer-style narrative):

```
## Verification Report
- Input count (from Scanner): <N>
- Kept count: <M>
- Category counts after verification: Economy=<n1> | Politics=<n2> | Technology=<n3> | Society=<n4> | Other=<n5>
- Fallback used: <none | fallback_1 | fallback_1+gap>

## Kept Stories

### [Category] <English headline>
- Publish date (verified): <ISO timestamp or local date>
- Source: <outlet name> [T1|T2|T3|T4]
- URL: <full https URL>
- Byline: <author name or "No byline">
- Factual excerpt (≥200 words English): <carried verbatim from Scanner>
- Commentary: <carried verbatim from Scanner>
- Verdict: KEEP
- Originality: <Original | Syndicated | Unclear>
- Authority score: <T1-primary | T1-wire | T4-official | T2-primary | T2-wire | T3>
- Impact tier: <Policy | Market | Structural | Humanitarian | Regional-structural>
- Dedup role: <Lead | Corroboration-of-#X | Standalone>

... (repeat per kept story) ...

## Dropped Stories

- URL: <full https URL>
- Reason: <Duplicate-of-#X | Syndicated-rewrite | Low-impact | Op-ed | Routine-PR | Celebrity-or-lifestyle | Incremental-no-new-fact | Sports-non-political | Other-specific-reason>

... (repeat per dropped story) ...

## Post-Verification Coverage
- Economy: <n>/<min_per_category>
- Politics: <n>/<min_per_category>
- Technology: <n>/<min_per_category>
- Society: <n>/<min_per_category>
- Other: <n>/<min_per_category>

## Post-Verification Coverage Gap   (include only if any category still < min_per_category after fallback_1)
- Category: <name>
- Scanner kept count: <n>
- Verifier kept count (after fallback_1): <m>
- Reason: <single sentence>
```
