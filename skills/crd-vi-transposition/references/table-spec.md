# CRD VI Country Table Specification

## Final shape

Use exactly these headers and this order:

| Country | Current Status | Summary |
|---|---|---|

Do not add source, date, Commission status, EY status, or confidence columns.

## Current Status

Use only:

- `Completed`: final national transposition legislation or the complete package
  has been adopted or officially confirmed complete. A future application date
  for Article 21c does not make an otherwise completed transposition Ongoing.
  Commission Full may support Completed when no newer official evidence
  contradicts it, but disclose when the national instrument was not located.
- `Ongoing`: an official draft, bill, partial measure, parliamentary process, or
  incomplete package is confirmed. A final act awaiting only its scheduled
  application date is not Ongoing when transposition itself is complete.
- `Pending`: no official legislative action is confirmed after the required
  search. Explain the search limitation; do not claim that no law exists.

EY's label is a cross-check, not the decision. Prefer newer national official
evidence when it conflicts with an older Commission or EY page.

## Summary contract

Write two to four concise original sentences per country. Include, where known:

1. the national act, ordinance, bill, draft, or latest legislative stage;
2. the latest verified milestone date and any distinct entry/application date;
3. exactly one marker: `Commission: Full`, `Commission: Partial`, or
   `Commission: None communicated`;
4. Article 21c timing plus material grandfathering, exemption, or uncertainty;
5. at least two direct Markdown links, normally one national official source and
   one Commission source; add EY as a third link when it materially supports the
   narrative.

Keep links inside Summary so the final output remains the exact EY three-column
table. Never copy or closely paraphrase EY's prose.

In a weekly report, the table remains cumulative as of `status_cutoff`. Start a
changed country's Summary with `Weekly change:` or a natural equivalent in the
requested language. Do not prepend repetitive no-change text to unchanged rows;
put the no-change conclusion in the separate Weekly Changes section.

## Dynamic EU set

Use only the current run's validated `membership-snapshot.json`. Do not use a
bundled country list, expected count, previous report, Commission CRD VI rows,
EY rows, the EEA, Schengen, or euro-area membership to determine the table
scope. A filtered report may contain only a requested subset of the validated
current membership.

The filter is presentation-only. `current-state.json` and `weekly-diff.json`
remain full-country artifacts. A filtered report must declare its exact
`country_filter` in frontmatter and contain exactly those rows.

## Final checks

- The all-country table exactly matches the unique countries in the current
  validated membership snapshot.
- A filtered table contains only requested EU Member States.
- Every status is Completed, Ongoing, or Pending.
- Every Summary contains one Commission marker, a year, and at least two links.
- `checked_at`, Commission `last_updated`, and EY `last_updated` remain distinct.
- The report distinguishes transposition completion from future Article 21c
  application.
- A weekly report contains valid weekly frontmatter and a Weekly Changes section.
- A weekly report contains exactly one Regulatory News & Market Commentary
  section between Weekly Changes and the country table; `news_count` agrees with
  the rendered rows and `news-items.json`.
- `change_count` equals the material country and membership changes in
  `weekly-diff.json`; a baseline identifies itself instead of presenting every
  row as a new law.
- The table and `current-state.json` agree on country, Current Status, and exact
  Commission marker.
