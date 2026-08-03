---
name: crd-vi-transposition
description: "Run a weekly CRD VI (Directive (EU) 2024/1619) transposition and regulatory-news tracker across the dynamically verified current EU Member States. Produces Weekly Changes, Regulatory News & Market Commentary, and the exact EY-style Country, Current Status, Summary table. Use for CRD VI, CRD6, Article 21c, third-country branch rules, weekly automated EU monitoring, market commentary, country comparisons, membership-safe change detection, or a dated all-country tracker built from European Commission, EUR-Lex, EY, news media, and independently verified national official sources."
---

# CRD VI Transposition

Produce a weekly CRD VI regulatory tracker with an independent news layer and a
country-status table containing exactly three columns:

| Country | Current Status | Summary |
|---|---|---|

Merge Commission notification data, EY tracking, and independent national
official research into one current status and one original Summary per country.
Compare the current result with the previous successful weekly snapshot. Do not
copy EY or news prose, expose separate Commission-status or weekly-change
columns.

Core invariants:

- `membership-snapshot.json` is the only current EU-scope authority.
- `current-state.json` always contains every validated current Member State.
- `weekly-diff.json` always compares two full-country states.
- `--country` filters rendered report rows only; it never narrows state or diff scope.
- News can trigger official follow-up but never changes Current Status by itself.

## Parameters

| Parameter | Required | Default | Meaning |
|---|---:|---|---|
| `week_ending` | no | latest completed Sunday | Weekly status cutoff; must be a Sunday |
| `previous_state` | no | auto | Prior successful `current-state.json`; `none` for baseline |
| `full_refresh` | no | auto | Full current-membership official rescan; automatic on baseline and every fourth ISO week |
| `news_max` | no | 8 | Maximum selected news items; allowed range 1–8 |
| `country` | no | all | Report-only filter for one or more validated Member States |
| `lang` | no | user language | Summary language; headers remain in English |
| `output` | no | inline | `inline` or saved Markdown path |

For a saved weekly report with no explicit path, use:

```text
~/.sci-research/reports/crd-vi/{report_week}/crd-vi-transposition-{report_week}.md
```

## Required references

Before every run, read these files completely:

- `references/source-method.md` for source priority, date semantics, and conflict
  resolution;
- `references/table-spec.md` for status adjudication, exact row content, and
  final validation rules;
- `references/weekly-method.md` for the weekly clock, snapshots, search triage,
  failures, and output metadata;
- `references/member-state-method.md` for dynamic EU membership discovery,
  reconciliation, source discovery, and the hard failure boundary;
- `references/news-method.md` for exact-week news discovery, selection,
  state-isolation, audit, and rendering;
- `references/news-sources.json` for search lanes, source classes, and exclusions.

Treat those references as authoritative. Keep this file as the orchestration
contract and do not recreate their detailed rules in prompts or output.

## Workflow

1. Calculate the period with one of:

   ```bash
   python3 "$SKILL_ROOT/scripts/weekly-period.py"
   python3 "$SKILL_ROOT/scripts/weekly-period.py" --week-ending "$WEEK_ENDING"
   ```

   Use the returned period, report path, and audit directory without manually
   recomputing the week. Locate the previous successful full-country snapshot;
   baseline when none exists.
2. Open both official membership authorities in `member-state-method.md`, create
   `audit/membership-snapshot.json`, and run
   `scripts/validate-member-states.py`. Treat the validated current list as the
   only country-scope authority. Stop the run on any missing, extra, duplicate,
   unavailable, or conflicting membership result.
3. Open the Commission page, EUR-Lex Directive and national-measures page, and
   EY tracker. Record displayed update dates, availability, and content hashes.
   Compare central categories with the prior snapshot to identify changed leads.
4. Generate the deterministic search queue from the membership snapshot with
   `scripts/build-weekly-search-plan.py` as specified in `weekly-method.md`.
   Deep-check Pending/Ongoing, changed, stale, conflicted, or refresh-due
   countries; perform the emitted lightweight known-URL checks for the remaining
   Completed countries. Discover national official sources and local-language
   terms dynamically; reuse prior verified URLs only as hints. Follow
   `source-method.md` for evidence access and date rules.
5. Independently open national official evidence for every deep-check country.
   Apply `source-method.md` to conflicts and `table-spec.md` to assign Completed,
   Ongoing, or Pending. Carry forward a last verified status when a source is
   temporarily unavailable; do not turn an outage into a status transition. When
   `country` is supplied, retain or carry forward non-selected countries so the
   state remains full-country.
6. Run all search lanes in `news-sources.json` for the exact reporting week.
   Apply `news-method.md`: verify publisher dates, open source pages, deduplicate
   by event, target three to eight material items, and save candidate decisions
   to `audit/news-search-audit.json`.
7. Create the full-country `audit/current-state.json` following the exact
   snapshot contract in `weekly-method.md`. Copy the preceding full-country
   snapshot to `audit/previous-state.json`, preserving its content.
8. Compare the full snapshots before writing prose:

   ```bash
   python3 "$SKILL_ROOT/scripts/diff-weekly-state.py" \
     --membership "$MEMBERSHIP_SNAPSHOT" \
     --previous "$PREVIOUS_STATE" --current "$CURRENT_STATE"
   ```

   Omit `--previous` for a baseline. Read the result, then create
   `audit/weekly-diff.json`. Fix unsafe transitions instead of overriding the
   script.
9. Create `audit/news-items.json` from the final news set. Write the weekly
   frontmatter, `## Weekly Changes`, `## Regulatory News & Market Commentary`,
   methodology note, exact three-column country table, enforcement note, source
   dates, practical reading, and disclaimer. Set `country_filter: all` or the
   exact comma-separated requested countries in frontmatter. Weekly Changes and
   news are incremental; the country table is cumulative as of the cutoff.
   Preserve the exact English Commission marker and direct links inside every
   Summary.
10. Create all report and audit files with `apply_patch` only. Never emit a
   partially refreshed run as successful. A failed scheduled week must be
   backfilled separately.
11. Validate dynamic membership, final Markdown, state alignment, and news artifacts:

   ```bash
   python3 "$SKILL_ROOT/scripts/validate-member-states.py" \
     --file "$MEMBERSHIP_SNAPSHOT"
   python3 "$SKILL_ROOT/scripts/validate-current-state.py" \
     --file "$CURRENT_STATE" --membership "$MEMBERSHIP_SNAPSHOT"
   python3 "$SKILL_ROOT/scripts/validate-country-table.py" \
     --file "$OUT_MD" --membership "$MEMBERSHIP_SNAPSHOT" \
     --weekly --state "$CURRENT_STATE" --diff "$WEEKLY_DIFF"
   python3 "$SKILL_ROOT/scripts/validate-news-section.py" \
     --file "$OUT_MD" --items "$NEWS_ITEMS" --state "$CURRENT_STATE" \
     --audit "$NEWS_AUDIT" --sources "$SKILL_ROOT/references/news-sources.json"
   ```

   Add `--allow-subset` to the country-table command only when `country_filter`
   is not `all`. Never use it for current-state validation or weekly diff. Fix
   every error.

## Required legal-date labels

Use these labels without conflation:

- national transposition deadline: 10 January 2026;
- general application from: 11 January 2026, subject to provision-specific and
  national timing;
- Article 21c third-country branch regime: 11 January 2027;
- Article 21c(5) existing-contract reference: contracts entered into before
  11 July 2026, subject to the exact rule and national implementation.

Never call 10 July 2026 the general CRD VI transposition deadline.

## Completion report

Report the ISO week, period and cutoff, dynamic membership count and authority
URLs, country count, material country-change count, regulatory-news count,
membership changes, status transitions, status counts, Commission and
EY page update dates, carried-forward or conflicted sources, validation results,
and saved report/audit paths.

## Examples

```text
$sci-research:crd-vi-transposition --week-ending 2026-08-02 --lang zh
$sci-research:crd-vi-transposition --country Germany,France,Netherlands --lang zh
```
