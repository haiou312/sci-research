# CRD VI Source and Date Method

## Source priority

Use evidence in this order:

1. national official gazette, legislation portal, parliament, ministry, central
   bank, or financial regulator;
2. European Commission transposition page and EUR-Lex;
3. EBA, ECB, or another EU authority;
4. EY tracker;
5. reputable law-firm or industry analysis as context only.

For the separate regulatory-news section, apply `news-method.md` and
`news-sources.json`. Accountable media and professional analysis may support a
news row and practical-impact explanation, but they remain below official legal
evidence for country-status adjudication.

For every run, derive the country scope from `membership-snapshot.json` and
discover national official URLs and local-language terms dynamically under
`member-state-method.md`. Prior verified URLs are discovery hints, not evidence
that a page still contains the current CRD VI position; reopen the underlying
item.

Open the underlying page before using a fact. Do not rely on a search-result
snippet for a legal status, date, law name, or scope conclusion.

## Date semantics

Keep these fields separate:

- `checked_at`: when the research pass opened or verified the source;
- `source_last_updated`: the date displayed by that source;
- `measure_adopted`: when the national measure was adopted;
- `measure_published`: when it appeared in the official journal or gazette;
- `measure_effective`: when the measure entered into force;
- `article_21c_general_applies`: when the general third-country branch rules apply;
- `article_21c_5_existing_contracts_from`: when the Article 21c(5) existing-contract
  protection begins.
- `discovered_at`: when the weekly process first found the item.

`checked_at` may be later than `source_last_updated`. Never present the check date
as though the source itself was updated on that date.

Do not infer a weekly event from a changed search-result snippet. Use the source's
own publication or material-update date. If that date falls before the reporting
period but the item was first found now, record a late discovery with both dates.

## Country research

For each country:

1. Search the national official sources using CRD VI, Directive 2024/1619, bank
   capital requirements, and third-country branch terms in English and the local
   language where useful.
2. Confirm the latest procedural stage and identify whether the measure covers
   all CRD VI chapters or only selected provisions.
3. Compare the result with the Commission category and EY status, taking each
   page's own update date into account.
4. Preserve uncertainty when the national source is inaccessible, ambiguous, or
   incomplete. Never infer completion from a bill title alone.

## Conflict resolution

- Newer final national law overrides older EY or Commission tracker wording for
  the substantive Current Status; retain the tracker discrepancy in Summary.
- Commission Full is official evidence of full measures communicated, not proof
  that every provision is correctly transposed or already applicable.
- Commission None communicated means no measure was communicated as of that
  page's update date; it does not prove that no national law exists.
- If EY says Completed but no final official measure or Commission Full status is
  verified, do not adopt Completed solely from EY.
- If sources remain irreconcilable, choose the status supported by the strongest
  dated official evidence and state the conflict explicitly.
- A temporary outage, blocked page, or missing search result never overrides the
  previous verified status. Carry it forward and mark source health accordingly.
- Do not regress Completed to Ongoing/Pending, or Ongoing to Pending, without an
  official correction, repeal, or reclassification and an explicit reason.

## Scope separation

Use Commission, EUR-Lex, EY, and national measures to determine country
transposition. Track EBA standards and guidelines, ECB opinions, and Commission
level-two acts as EU implementation developments. Report them in Weekly Changes
when material, but do not use them alone to change a country Current Status.
Treat media, industry, and professional reporting as a separate news layer. If
it reveals a possible country development, open and record the underlying
official evidence before changing Current Status.
