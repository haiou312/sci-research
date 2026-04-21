# Negativity Rubric — Category + Severity + Credibility

Loaded by the Classifier. Defines the closed taxonomy used to grade every candidate item.

## Categories

| Category | Definition | Typical Signals |
|---|---|---|
| `Legal` | Lawsuits, investigations, regulatory actions, criminal charges | "sued", "class action", "DOJ probe", "SEC investigation", "charged with" |
| `Financial` | Fraud, restatement, downgrades, material distress | "fraud", "restatement", "downgrade", "missed guidance", "bankruptcy", "going concern" |
| `Operational` | Outages, breaches, recalls, safety incidents | "data breach", "ransomware", "outage", "recall", "accident", "fatality" |
| `Ethics` | Discrimination, harassment, misconduct allegations | "harassment", "discrimination", "misconduct", "ethics complaint", "hostile workplace" |
| `Leadership` | Unplanned departures, internal conflict, fiduciary issues | "resigns", "fired", "ousted", "board feud", "no-confidence" |
| `Product` | Defects, backlash, quality issues | "dangerous", "defect", "refund campaign", "widespread complaints", "unsafe" |
| `Activism` | Boycotts, protests, activist investor campaigns | "boycott", "protest", "activist investor demands", "shareholder revolt" |
| `Neutral` | Everything else — no reputational impact | Earnings beats, routine announcements, product launches, positive coverage |

Items classified `Neutral` are dropped before reaching the Writer.

## Severity Levels

| Level | Rule of thumb | Example |
|---|---|---|
| `critical` | Existential risk | CEO criminal indictment; mass-casualty product incident; imminent bankruptcy |
| `high` | Material reputational impact | Class-action lawsuit; 9-figure fine; CEO resignation under cloud; multi-million-user breach |
| `medium` | Noteworthy but not existential | Regulatory warning letter; department-level investigation; mid-tier exec exit under question; single-region outage |
| `low` | Individual complaints or analyst noise | Single-analyst downgrade without specific trigger; isolated user complaint post; minor labor grievance |
| `neutral` | Not negative at all | Positive product review, earnings beat, routine partnership |

The `--severity-min` flag filters here. Default `medium` drops `low` and `neutral`. `--severity-min low` keeps everything except `neutral`.

## Credibility Weighting

Severity is adjusted by source credibility:

| Source tier | Adjustment |
|---|---|
| T1 news (Reuters, Bloomberg, AP, AFP, Xinhua) | No adjustment |
| T2 news (FT, WSJ, BBC, CNBC, Nikkei) | No adjustment |
| T3 news (TechCrunch, industry verticals, regional dailies) | Downgrade one level if commentary-only (no new reporting) |
| T4 news (blogs, opinion outlets) | Require corroboration from a T1-T3 source to claim `medium`+; else downgrade to `low` with `*unverified*` |
| Reddit | `high`/`critical` requires T1-T3 corroboration; else downgrade to `low` or drop |
| X (Twitter) | Same as Reddit. Verified accounts + linked primary evidence can stay at original severity |

**Implausible claims** from social sources without any corroboration (e.g. "CEO arrested" with no news match) should be **dropped**, not downgraded. Noise protection matters more than recall for this use case.

## Required Output Per Kept Item

Every item the Classifier promotes to `kept_items` MUST contain:

```yaml
category: Legal | Financial | Operational | Ethics | Leadership | Product | Activism
severity: critical | high | medium | low     # never neutral (those are dropped)
subject: company | executive:<name>           # name must match an entry in Resolver's executives
quote: <verbatim text from source, max 500 chars, no paraphrase>
source_url: <absolute URL>
source_outlet: <e.g. Reuters, r/investing, x.com/@handle>
source_tier: T1 | T2 | T3 | T4 | social
published_at: <ISO 8601 datetime>
corroborating_urls: []                        # additional sources, may be empty
confidence: high | medium | low
```

## Hard Rules

1. **Verbatim quote required.** If the Classifier cannot extract a quote after `WebFetch`-ing the source, drop with reason `no_verbatim_quote`.
2. **No fabrication.** Every field must trace to the source URL. When in doubt, drop.
3. **Dedup across sources.** When two or more items describe the same event, keep the highest-tier source as primary and list the rest as `corroborating_urls`.
4. **Neutral is silent.** Neutral items go into `dropped_items` with reason `neutral`; they never surface in `kept_items`.
5. **Downgrade rather than drop marginal cases.** For borderline items, downgrade one level and add a low-confidence marker — the recipient can judge from the verbatim quote.
6. **Drop noise.** Single-complaint Reddit threads with no corroboration should be dropped even at `low` severity unless they describe a specific, verifiable incident.
