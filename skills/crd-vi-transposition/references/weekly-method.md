# CRD VI Weekly Method

## Weekly clock

Use `Europe/London`. A normal automated run on Monday reports the previous
completed ISO week, Monday 00:00 through Sunday 23:59:59. Keep these concepts
separate:

- `period_start` and `period_end`: the fixed calendar-week evidence window;
- `status_cutoff`: the Sunday date at which every Current Status is stated;
- `checked_at`: when the automated research actually ran;
- `discovery_start`: two days before `period_start`, used only as an overlapping
  search cursor to catch delayed indexing;
- source publication, legal adoption, publication, commencement, and Article 21c
  dates as defined in `source-method.md`.

Assign a development to the week in which its authoritative source was first
published or materially updated. If an earlier event is discovered late, label
it `late discovery`, retain its true legal date, and include it in the current
run's change note. Never rewrite the event date to fit the reporting week.

Run `scripts/weekly-period.py` rather than calculating ISO weeks manually. An
explicit `week_ending` must be a Sunday. If a scheduled run fails, generate the
missing fixed week as a backfill; do not silently widen the next report's period.

## Snapshot contract

Save one machine-readable snapshot per successful full-country run. Use this
shape; values may be null only when the official evidence does not provide them:

```json
{
  "schema_version": 1,
  "report_week": "2026-W31",
  "period_start": "2026-07-27",
  "period_end": "2026-08-02",
  "status_cutoff": "2026-08-02",
  "checked_at": "2026-08-03T07:00:00+01:00",
  "sources": {
    "commission": {"last_updated": "2026-07-31", "content_hash": "sha256:...", "available": true},
    "ey": {"last_updated": "2026-07-30", "content_hash": "sha256:...", "available": true}
  },
  "countries": {
    "Austria": {
      "status": "Ongoing",
      "commission_marker": "Commission: Partial",
      "national_measure": "Official bill or act identifier",
      "milestone_date": "2026-07-29",
      "measure_effective": null,
      "article_21c_applies": "2027-01-11",
      "source_health": "verified",
      "last_verified": "2026-08-03",
      "source_urls": ["https://...", "https://..."]
    }
  }
}
```

Use only `verified`, `carried_forward`, `conflict`, or `unavailable` for
`source_health`. A temporary source failure must carry forward the last verified
status. It must not create a status change. A status regression requires an
official correction, repeal, or reclassification and a non-empty
`regression_reason` in the current country record.

Compare snapshots with `scripts/diff-weekly-state.py`. Treat changes to status,
Commission marker, national measure, milestone dates, Article 21c timing, or
source health as auditable changes. Do not treat prose-only Summary edits as a
regulatory event.

## Search triage

Read `country-sources.json` before searching. Use this weekly order:

1. Check the Commission page, EUR-Lex national transposition measures, and EY.
   Record displayed update dates and a content hash even when the date is
   unchanged.
2. Deep-check every Pending or Ongoing country through its registered national
   official sources.
3. Deep-check a Completed country when a central tracker changed its category,
   a known national page changed, its source health is not verified, or it has
   not received a full official refresh in 28 days.
4. Otherwise perform a lightweight known-URL check for Completed countries.
5. Every fourth ISO week, perform a full official refresh of all 27 countries.

After identifying central-source country changes, generate the concrete queue:

```bash
python3 "$SKILL_ROOT/scripts/build-weekly-search-plan.py" \
  --registry "$SKILL_ROOT/references/country-sources.json" \
  --period-end "$PERIOD_END" --previous "$PREVIOUS_STATE" \
  --changed-country Austria
```

Omit `--previous` for the baseline, repeat `--changed-country` as needed, and add
`--full-refresh` on a scheduled full refresh. Follow the emitted `deep_checks`
and `light_checks`; do not manually downgrade a deep-check country to save time.

Use local-language terms from the registry together with `2024/1619`, `CRD VI`,
`CRD6`, known national bill or act identifiers, and third-country-branch terms.
Search-engine recency filters are discovery aids only. Open the page and verify
its own publication or update date.

Hash normalized substantive content, such as the Commission country groups or a
national measure's title/status block. Remove navigation, cookie banners,
session tokens, and generated page timestamps before hashing; a raw full-page
HTML hash is too noisy to trigger country research safely.

The Commission categories describe measures communicated to the Commission.
They are not, by themselves, proof that every national provision is legally
complete. EBA and ECB materials belong in a separate EU implementation watch;
they may explain Article 21c, authorisation, reporting, SREP, or opinions on
draft laws, but do not directly determine a country's transposition status.

## Weekly report contract

Start every weekly Markdown report with this frontmatter:

```yaml
---
report_week: 2026-W31
period_start: 2026-07-27
period_end: 2026-08-02
timezone: Europe/London
status_cutoff: 2026-08-02
checked_at: 2026-08-03T07:00:00+01:00
previous_successful_week: 2026-W30
change_count: 2
news_count: 4
---
```

Use `previous_successful_week: none` for the first baseline. Add a
`## Weekly Changes` section, then the news section specified in
`news-method.md`, then the full table. List only material country or
EU-implementation changes in Weekly Changes; when `change_count` is zero, state
that no material change was found. Keep the full current table at exactly three
columns. For a changed country, begin its Summary with `Weekly change:` or an
equivalent phrase in the requested language. Unchanged rows retain their
cumulative Summary. `news_count` records news rows and is independent of
`change_count`.

Save successful runs under:

```text
~/.sci-research/reports/crd-vi/{report_week}/
├── crd-vi-transposition-{report_week}.md
└── audit/
    ├── current-state.json
    ├── previous-state.json
    ├── weekly-diff.json
    ├── news-search-audit.json
    ├── news-items.json
    ├── source-checks.json
    └── run-metadata.json
```

All audit JSON must contain source URLs and dates, not copied article prose.
