---
name: crd-vi-transposition
description: "Run a weekly CRD VI (Directive (EU) 2024/1619) transposition and regulatory-news tracker for the dynamically verified EU Member States. Uses the global Brave Search MCP, compares full-country snapshots, and produces validated Markdown and mandatory Word reports with Weekly Changes, Regulatory News & Market Commentary, and a Country / Current Status / Summary table; controlled email attaches Word by default. Use for CRD VI/CRD6, Article 21c, third-country branches, weekly EU implementation monitoring, market commentary, country comparisons, or membership-safe change detection using Commission, EUR-Lex, EY, and national official sources."
---

# CRD VI Transposition

Produce the weekly tracker by reconciling Commission, EUR-Lex, EY, and national
official evidence, comparing it with the previous successful full-country
snapshot, and rendering the exact report defined by the references below.

Core invariants:

- `membership-snapshot.json` is the only current EU-scope authority.
- `current-state.json` always contains every validated current Member State.
- `weekly-diff.json` always compares two full-country states.
- `--country` filters rendered report rows only; it never narrows state or diff scope.
- Follow `brave-search-method.md` and `news-sources.json` as the sole search
  contract for this skill.

## Parameters

| Parameter | Required | Default | Meaning |
|---|---:|---|---|
| `week_ending` | no | latest completed Sunday | Weekly status cutoff; must be a Sunday |
| `previous_state` | no | auto | Prior successful `current-state.json`; `none` for baseline |
| `full_refresh` | no | auto | Full current-membership official rescan; automatic on baseline and every fourth ISO week |
| `news_max` | no | 8 | Maximum selected news items; allowed range 1–8 |
| `country` | no | all | Report-only filter for one or more validated Member States |
| `output` | no | inline | `inline` or saved `.md` path; Word uses the same stem with `.docx` |
| `email` | no | empty | Comma-separated recipients; empty means no email |
| `email_subject` | no | auto | `CRD VI Transposition Tracker — {report_week}` |
| `email_attach` | no | `docx` | `docx`, `both`, `md`, or `none` |
| `email_dry_run` | no | false | Preview the controlled email without SMTP delivery |

Every successful run saves both formats. With `output=inline`, also render the
Markdown in the response. For an explicit path, require `.md` and derive the
Word path by replacing only that suffix with `.docx`; otherwise use the paths
returned by `weekly-period.py`.

## Required references

Before every run, read these files completely:

- `references/brave-search-method.md` for exact MCP tool names, arguments,
  preflight, direct-page boundary, and audit requirements;
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
- `references/email-spec.md` when `email` is non-empty.

Treat those references as authoritative. Keep this file as the orchestration
contract and do not recreate their detailed rules in prompts or output.

## Workflow

1. Preflight Brave Search exactly as specified in
   `references/brave-search-method.md`; stop on any failed requirement. Then
   preflight the required Word exporter:

   ```bash
   command -v pandoc >/dev/null 2>&1
   ```

   If it is absent, stop and report that CRD VI requires Pandoc to generate its
   mandatory Word deliverable. Do not run a package manager inside the skill.
   Then calculate the period with one of:

   ```bash
   python3 "$SKILL_ROOT/scripts/weekly-period.py"
   python3 "$SKILL_ROOT/scripts/weekly-period.py" --week-ending "$WEEK_ENDING"
   ```

   Use the returned values without recomputing the week; apply the explicit
   output-path rule above when needed. Select the previous state under
   `weekly-method.md`.
2. Build and validate `audit/membership-snapshot.json` under
   `member-state-method.md`; stop on any validation failure.
3. Open the Commission page, EUR-Lex Directive and national-measures page, and
   EY tracker. Record displayed update dates, availability, and content hashes.
   Compare central categories with the prior snapshot to identify changed leads.
4. Generate and follow the deterministic deep/light search queue exactly as
   specified in `weekly-method.md`; apply `brave-search-method.md` for discovery
   and page retrieval.
5. Open national official evidence for every deep-check country. Resolve status
   and conflicts under `source-method.md` and `table-spec.md`, keeping the state
   full-country even when the rendered report is filtered.
6. Run every news lane and save its audit under `news-sources.json` and
   `news-method.md`.
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
9. Create `audit/news-items.json` and the Markdown report under
   `weekly-method.md`, `news-method.md`, and `table-spec.md`.
10. Create Markdown and audit files with `apply_patch` only. Manage
    `run-metadata.json` delivery status exactly as specified in
    `weekly-method.md`.
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
12. Export the validated Markdown to the mandatory Word path:

    ```bash
    pandoc "$OUT_MD" -o "$OUT_DOCX"
    python3 -m zipfile -t "$OUT_DOCX"
    ```

    Confirm both files exist and are non-empty. On any export or package failure,
    keep the metadata non-successful and do not send email. After success, set
    `delivery_status: successful` with `apply_patch`. Generate the binary DOCX
    only through Pandoc.
13. When `email` is non-empty, follow `references/email-spec.md`.

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

Report the period and cutoff, membership and country/change/news counts, status
transitions and counts, key source dates or failures, Brave query counts,
validation results, absolute output paths, and any requested email result.

## Examples

```text
$sci-research:crd-vi-transposition --week-ending 2026-08-02
$sci-research:crd-vi-transposition --country Germany,France,Netherlands
$sci-research:crd-vi-transposition --week-ending 2026-08-02 --email "team@example.com" --email-dry-run
```
