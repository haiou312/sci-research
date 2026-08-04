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
changed country's Summary with `Weekly change:`. Do not prepend repetitive
no-change text to unchanged rows; put that conclusion in Weekly Changes.

## Dynamic EU set

Derive scope only under `member-state-method.md`. A filtered report declares its
exact `country_filter` and renders only that validated subset; `current-state.json`
and `weekly-diff.json` remain full-country artifacts.

## Final checks

- Every status is Completed, Ongoing, or Pending.
- Every Summary contains one Commission marker, a year, and at least two links.
- `checked_at`, Commission `last_updated`, and EY `last_updated` remain distinct.
- The report distinguishes transposition completion from future Article 21c
  application.
- The table and `current-state.json` agree on country, Current Status, and exact
  Commission marker.

For weekly structure, counts, news placement, disclaimer, baseline, and scope
alignment, apply `weekly-method.md`, `news-method.md`, and the validators.
