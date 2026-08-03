---
name: crd-vi-transposition
description: "Run a weekly or ad hoc CRD VI (Directive (EU) 2024/1619) transposition and regulatory-news tracker across EU Member States. Produces Weekly Changes, Regulatory News & Market Commentary, and the exact EY-style Country, Current Status, Summary table. Use for CRD VI, CRD6, Article 21c, third-country branch rules, weekly automated EU monitoring, market commentary, country comparisons, change detection, or a dated 27-country tracker built from European Commission, EUR-Lex, EY, news media, and independently verified national official sources."
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
columns, or let media reporting alone determine Current Status.

## Parameters

| Parameter | Required | Default | Meaning |
|---|---:|---|---|
| `mode` | no | `weekly` | `weekly` or ad hoc `snapshot` |
| `week_ending` | no | latest completed Sunday | Weekly status cutoff; must be a Sunday |
| `as_of` | snapshot only | today | Ad hoc point-in-time cutoff |
| `previous_state` | no | auto | Prior successful `current-state.json`; `none` for baseline |
| `full_refresh` | no | auto | Full 27-country official rescan; automatic on baseline and every fourth ISO week |
| `news_max` | no | 8 | Maximum selected news items; allowed range 1–8 |
| `country` | no | all 27 EU Member States | Optional one-or-more-country filter |
| `lang` | no | user language | Summary language; headers remain in English |
| `output` | no | inline | `inline` or saved Markdown path |

For a saved weekly report with no explicit path, use:

```text
~/.sci-research/reports/crd-vi/{report_week}/crd-vi-transposition-{report_week}.md
```

For `mode=snapshot`, retain the dated legacy path under `{as_of}` and do not
claim that the output is a weekly change report.

## Required references

Before a weekly run, read these files completely:

- `references/source-method.md` for source priority, date semantics, and conflict
  resolution;
- `references/table-spec.md` for status adjudication, exact row content, and
  final validation rules;
- `references/weekly-method.md` for the weekly clock, snapshots, search triage,
  failures, and output metadata;
- `references/news-method.md` for exact-week news discovery, selection,
  state-isolation, audit, and rendering;
- `references/news-sources.json` for search lanes, source classes, and exclusions;
- `references/country-sources.json` for EU hubs, national official websites, and
  local-language search terms.

Treat those references as authoritative. Keep this file as the orchestration
contract and do not recreate their detailed rules in prompts or output.

## Workflow

1. For `mode=weekly`, calculate the period with one of:

   ```bash
   python3 "$SKILL_ROOT/scripts/weekly-period.py"
   python3 "$SKILL_ROOT/scripts/weekly-period.py" --week-ending "$WEEK_ENDING"
   ```

   Use the returned period, report path, and audit directory without manually
   recomputing the week. Locate the previous successful full-country snapshot;
   baseline when none exists. For `mode=snapshot`, normalize `as_of` instead.
2. Open the Commission page, EUR-Lex Directive and national-measures page, and
   EY tracker. Record displayed update dates, availability, and content hashes.
   Compare central categories with the prior snapshot to identify changed leads.
3. Generate the deterministic search queue with
   `scripts/build-weekly-search-plan.py` as specified in `weekly-method.md`.
   Deep-check Pending/Ongoing, changed, stale, conflicted, or refresh-due
   countries; perform the emitted lightweight known-URL checks for the remaining
   Completed countries. Use the registry's local-language terms. Never rely on
   search snippets or recency filters alone.
4. Independently open national official evidence for every deep-check country.
   Apply `source-method.md` to conflicts and `table-spec.md` to assign Completed,
   Ongoing, or Pending. Carry forward a last verified status when a source is
   temporarily unavailable; do not turn an outage into a status transition.
5. In weekly mode, run all search lanes in `news-sources.json` for the exact
   reporting week. Apply `news-method.md`: verify publisher dates, open source
   pages, deduplicate by event, target three to eight material items, and save
   candidate decisions to `audit/news-search-audit.json`. News may trigger a
   national official-source follow-up but must not directly change Current Status.
6. Create `audit/current-state.json` with `apply_patch`, following the exact
   snapshot contract in `weekly-method.md`. Copy the preceding snapshot to
   `audit/previous-state.json` with `apply_patch`, preserving its content.
7. Compare snapshots before writing prose:

   ```bash
   python3 "$SKILL_ROOT/scripts/diff-weekly-state.py" \
     --previous "$PREVIOUS_STATE" --current "$CURRENT_STATE"
   ```

   Omit `--previous` for a baseline. Read the result, then create
   `audit/weekly-diff.json` with `apply_patch`. Fix unsafe transitions instead of
   overriding the script.
8. Create `audit/news-items.json` from the final news set. Write the weekly
   frontmatter, `## Weekly Changes`, `## Regulatory News & Market Commentary`,
   methodology note, exact three-column country table, enforcement note, source
   dates, practical reading, and disclaimer. Weekly Changes and news are
   incremental; the country table is cumulative as of the cutoff. Preserve the
   exact English Commission marker and direct links inside every Summary.
9. Create all report and audit files with `apply_patch` only. Never emit a
   partially refreshed run as successful. A failed scheduled week must be
   backfilled separately.
10. Validate the final weekly Markdown, state alignment, and news artifacts:

   ```bash
   python3 "$SKILL_ROOT/scripts/validate-country-table.py" \
     --file "$OUT_MD" --weekly --state "$CURRENT_STATE" --diff "$WEEKLY_DIFF"
   python3 "$SKILL_ROOT/scripts/validate-news-section.py" \
     --file "$OUT_MD" --items "$NEWS_ITEMS" --state "$CURRENT_STATE"
   ```

   Add `--allow-subset` only when the user requested fewer than all 27 Member
   States. For `mode=snapshot`, omit `--weekly` and `--state`. Fix every error.

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

Report the ISO week, period and cutoff, country count, material country-change
count, regulatory-news count, status transitions, status counts, Commission and
EY page update dates, carried-forward or conflicted sources, validation results,
and saved report/audit paths.

## Examples

```text
$sci-research:crd-vi-transposition --week-ending 2026-08-02 --lang zh
$sci-research:crd-vi-transposition --mode snapshot --as-of 2026-07-29
$sci-research:crd-vi-transposition --country Germany,France,Netherlands --lang zh
```
