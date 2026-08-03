# CRD VI Weekly Regulatory News Method

## Purpose and boundary

Add a distinct `## Regulatory News & Market Commentary` section to every
weekly report. Use it to explain what regulators, banks, industry bodies, media,
and professional advisers reported during the fixed reporting week.

Keep this evidence layer separate from country transposition adjudication. A
news article may trigger an official-source follow-up, but it must not by itself
change `Current Status`. Change a country status only after opening qualifying
official evidence and recording that evidence in `current-state.json`.

## Discovery

Read `news-sources.json` before searching. Run each active search lane once for
the exact `period_start` through `period_end` window. Prefer the configured
Google News MCP when available; otherwise use live web search. Search in English
and formulate local-language terms dynamically when a country lead
requires follow-up.

Search-result dates and recency filters are discovery aids. Open the publisher's
page and verify its displayed publication date. Do not use a result whose date
cannot be verified. A materially updated older page is eligible only when the
publisher displays a substantive update date inside the reporting period and
the report describes it as an update.

Save all plausible candidates and decisions in `audit/news-search-audit.json`:

```json
{
  "schema_version": 1,
  "report_week": "2026-W31",
  "lanes": [{"id": "third_country_branches", "queries": ["..."], "result_count": 4}],
  "candidates": [
    {
      "url": "https://...",
      "published_date": "2026-07-30",
      "decision": "keep",
      "reason": "material Article 21c operational development"
    }
  ]
}
```

Use only `keep` or `drop` for `decision`. Record a concise reason. Do not copy
article body text into audit JSON. A dropped undated candidate may use
`published_date: null`; a kept candidate must have a verified date in the
reporting week.

## Selection

Target three to eight items, but publish fewer rather than fill a quiet week.
Publish zero only after all search lanes ran and no material item qualified.

Keep an item only when all are true:

- its verified publication or qualifying update date falls inside the week;
- CRD VI, national transposition, Article 21c, third-country branches, reverse
  solicitation, grandfathering, authorisation, reporting, SREP, or a concrete
  bank operational response is directly material;
- the page exposes enough content to support the stated development and impact;
- it adds a distinct event or materially different practical interpretation.

Drop generic Basel III or CRR III coverage without a concrete CRD VI link,
duplicate coverage, marketing-only pages, event notices, undated pages, copied
press releases with no added information, and speculative claims without a
clearly attributed basis.

Prefer original official announcements and accountable financial or policy
reporting. A paywalled article may remain a secondary link only when an opened,
accessible source independently supports the material facts. Professional or
law-firm commentary may explain practical impact but must be labelled as
analysis, not law.

Deduplicate by event, not headline. When several outlets cover one event, keep
one row and include no more than three source links. Prefer the original official
release plus the strongest independent report or analysis.

## Selected-items contract

Save final items to `audit/news-items.json`:

```json
{
  "schema_version": 1,
  "report_week": "2026-W31",
  "period_start": "2026-07-27",
  "period_end": "2026-08-02",
  "items": [
    {
      "date": "2026-07-30",
      "country_region": "EU",
      "development": "EBA published ...",
      "practical_impact": "Third-country banks should ...",
      "source_urls": ["https://..."],
      "source_class": "official",
      "status_effect": "none"
    }
  ]
}
```

Use only `official`, `news_media`, `industry`, or `professional_analysis` for
`source_class`. Use `status_effect: none` unless the article led to separately
opened official country evidence; then use `official_follow_up` and add
`official_follow_up_url`. The official URL must also appear in that country's
state evidence.

## Report rendering

Place the section after `## Weekly Changes` and before the country table. When
items exist, use exactly:

| Date | Country/Region | Development | Practical Impact | Sources |
|---|---|---|---|---|

Write concise original English prose. Keep the date in `YYYY-MM-DD`, preserve
source qualification such as "the EBA said" or "the law firm analysed", and put
direct publisher links in Sources. Do not link to a search-result or Google News
redirect.

When no item qualifies, omit the news table and write exactly:

```text
No material CRD VI news identified for this reporting period.
```

Set frontmatter `news_count` to the number of rendered rows. Validate the report
and selected-items JSON with `scripts/validate-news-section.py`.

## Disclaimer and AI disclosure

End every report with exactly one `## Disclaimer` section, after the country
table. Write the heading and body in English. The disclaimer must state that the
report is AI-assisted, briefly describe the workflow, identify the `checked_at`
evidence boundary, warn that the report may contain omissions or errors, and say
that it is not professional advice or a substitute for independent verification.

Use this concise template and replace `<checked_at>` with the report's
frontmatter value:

> This report was drafted and assembled with AI through a structured workflow:
> the reporting period and dynamically verified EU Member State set were defined
> first; official EU and national sources were checked for transposition status;
> in-period regulatory news was searched, dated, deduplicated and kept separate
> from status evidence; and the resulting state, changes, news and citations
> were mechanically validated. It reflects information available and checked as
> of `<checked_at>` and may contain omissions or inaccuracies. It is provided
> for general information only, is not legal, regulatory, accounting, tax,
> investment or other professional advice, and is not a substitute for advice
> from a qualified professional. Verify the current law, regulatory position and
> source material independently before relying on this report or taking action.
> No representation or warranty is made as to completeness, accuracy or
> timeliness, and no responsibility is accepted for decisions or losses arising
> from reliance on it, to the extent permitted by law.
