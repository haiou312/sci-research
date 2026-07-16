---
name: china-outbound-opportunity-briefing
description: "Generate a Chinese-language commercial opportunity briefing for Chinese enterprises expanding into the United Kingdom and Europe. Use for UK economic signals, China outbound investment, cross-border M&A, UK/Europe investment footprints, important Companies House registrations and entity changes, business-development implications, next-step watch items, source-backed images, branded Markdown/DOCX output, and optional controlled email delivery."
---

# China Outbound Opportunity Briefing

Generate an institutional Chinese-language briefing for relationship managers, corporate bankers, transaction bankers, and investment-banking teams. Cover the requested date range, identify only material developments, translate them into potential banking opportunities, and distinguish evidence from inference.

## Parameters

| Parameter | Required | Default | Description |
|---|---|---|---|
| `date_to` | No | today | End date in `YYYY-MM-DD` |
| `date_from` | No | `date_to - 6 days` | Start date in `YYYY-MM-DD` |
| `total` | No | `12` | Target number of selected developments |
| `lang` | No | `zh` | Output language; version 1 supports `zh` |
| `out_dir` | No | `~/.sci-research/reports/china-opportunity-briefings/{date_to}/` | Output directory |
| `companies_house` | No | `auto` | `auto`, `required`, or `off` |
| `watchlist` | No | `~/.sci-research/config/china-company-watchlist.json` | Optional Chinese parent/entity watchlist |
| `previous_ch_snapshot` | No | auto-discover | Optional prior compatible Companies House snapshot |
| `images` | No | `prefer` | `prefer` or `none` |
| `email` | No | empty | Comma-separated recipients |
| `email_subject` | No | `中资企业商机拓展简报 - {date_from}至{date_to}` | Email subject |
| `email_dry_run` | No | `false` | Preview without sending |

Derived paths:

```text
OUT_MD={OUT_DIR}/中资企业商机拓展简报-{date_from}-{date_to}.md
OUT_DOCX={OUT_DIR}/中资企业商机拓展简报-{date_from}-{date_to}.docx
AUDIT_DIR={OUT_DIR}/audit
SCANNER_AUDIT={AUDIT_DIR}/scanner-batch.txt
CH_SNAPSHOT={AUDIT_DIR}/companies-house-snapshot.json
CH_DIFF={AUDIT_DIR}/companies-house-diff.json
CH_ANALYSIS={AUDIT_DIR}/companies-house-analysis.txt
VERIFIER_AUDIT={AUDIT_DIR}/verifier-report.txt
FACT_MANIFEST={AUDIT_DIR}/fact-manifest.yaml
```

## Runtime Paths

Set `SKILL_DIR` to this skill directory and derive `PLUGIN_ROOT` once:

```bash
SKILL_DIR=<absolute skills/china-outbound-opportunity-briefing path>
PLUGIN_ROOT="$(cd "$SKILL_DIR/../.." && pwd)"
RUNTIME_SYNC="$PLUGIN_ROOT/skills/setup-sci-research-runtime/scripts/sync_runtime.py"
```

Before starting, run:

```bash
python3 "$RUNTIME_SYNC" --project-root "$PWD" --check
```

If it fails, stop and ask the user to run `$sci-research:setup-sci-research-runtime`, then start a new Codex task.

## Required References

Read these files before their corresponding stage:

- Scanner, Companies House Analyst, and Verifier: `references/rubric.md`
- Every agent and the orchestrator: `references/schemas.md`
- Companies House collection and interpretation: `references/companies-house-method.md`
- Writer, Editor, Hook, and DOCX export: `references/output-spec.md`
- Any image selection or embedding: `references/image-policy.md`
- Writer, Editor, and DOCX export: `references/layout-benchmarks.md`

## Custom-Agent Dispatch

Use the exact installed role with `fork_turns="none"`:

- `sci-research-opportunity-scanner`
- `sci-research-companies-house-analyst`
- `sci-research-opportunity-verifier`
- `sci-research-opportunity-fact-extractor`
- `sci-research-opportunity-writer`
- `sci-research-opportunity-editor`

Do not pass model overrides. Start each prompt with absolute `plugin_root` and `skill_root`. Pass upstream output verbatim. Capture and validate every result, then call `close_agent`. For a parallel Scanner group, capture all results, persist the batch, and close every child before the next stage. Close failed or invalid attempts before retrying. Stop if an agent cannot be closed.

## Workflow

1. **Resolve parameters and paths.**
   - Validate `date_from <= date_to`.
   - Reject `lang != zh`.
   - Expand `~` and `{date_to}`.
   - Create `OUT_DIR` and `AUDIT_DIR`.
   - Remove stale audit/output files for the same date range with `apply_patch`.

2. **Scan five lanes in parallel.**
   Launch one `sci-research-opportunity-scanner` per lane:

   ```text
   uk_economy
   outbound_europe
   cross_border_ma
   investment_footprint
   companies_house_discovery
   ```

   Each Scanner receives only `date_from`, `date_to`, one `lane`, `images`, and the runtime-path header. It searches freely within its lane and emits the Category Scanner Output in `references/schemas.md`. It must open every URL used as evidence.

   Retry one invalid or failed lane once. Mechanically assemble the five complete outputs in lane order into the Scanner Batch schema. Do not deduplicate, score, rewrite, or reroute. Persist the batch verbatim to `SCANNER_AUDIT` with `apply_patch`, then close all Scanner agents.

3. **Collect Companies House data.**
   Apply `references/companies-house-method.md`.

   - Extract any company numbers explicitly returned by the `companies_house_discovery` Scanner.
   - If `companies_house=off`, create a skipped-status JSON record and continue.
   - If `companies_house=required`, require `COMPANIES_HOUSE_API_KEY`; stop when absent.
   - If `companies_house=auto`, run the collector when the API key exists; otherwise record `status=unavailable` and continue without fabricating registry findings.
   - Pass the optional watchlist when it exists.

   Run:

   ```bash
   python3 "$SKILL_DIR/scripts/collect-companies-house.py" \
     --start-date "$DATE_FROM" \
     --end-date "$DATE_TO" \
     --output "$CH_SNAPSHOT" \
     [--watchlist "$WATCHLIST"] \
     [--company-number NUMBER ...]
   ```

   Resolve `PREVIOUS_CH_SNAPSHOT` before diffing:

   - use `previous_ch_snapshot` when explicitly supplied;
   - otherwise search earlier sibling report directories for the newest
     `audit/companies-house-snapshot.json` whose report end date is before
     `DATE_FROM`;
   - require the prior and current snapshots to carry the same watchlist scope
     fingerprint;
   - if no compatible snapshot exists, pass explicit `not_available` to the
     Analyst.

   When a compatible previous snapshot exists, run:

   ```bash
   python3 "$SKILL_DIR/scripts/diff-company-snapshots.py" \
     --previous "$PREVIOUS_CH_SNAPSHOT" \
     --current "$CH_SNAPSHOT" \
     --output "$CH_DIFF"
   ```

   The diff script rejects overlapping report periods and mismatched watchlist
   fingerprints. Do not treat company name, director nationality, address, or
   a Chinese-sounding name as proof of Chinese ownership.

4. **Analyse Companies House results.**
   Spawn `sci-research-companies-house-analyst` with:

   - Scanner Batch verbatim
   - `CH_SNAPSHOT` content
   - `CH_DIFF` content or explicit `not_available`
   - Date range

   The Analyst applies `confirmed`, `probable`, or `unverified` Chinese-nexus labels and explains material entity changes. Persist its complete output to `CH_ANALYSIS`, then close the agent. Unverified entities do not enter the final briefing as Chinese-backed companies.

5. **Verify, deduplicate, and prioritise.**
   Spawn `sci-research-opportunity-verifier` with the Scanner Batch and Companies House Analysis verbatim, the date range, and `total`.

   The Verifier:

   - revalidates dates, source support, geography, transaction stage, and Chinese nexus;
   - merges same-event coverage and selects the strongest primary source;
   - ranks `high`, `medium`, or `monitor`;
   - identifies plausible banking angles without asserting an existing client relationship;
   - separates confirmed facts from analyst inference;
   - selects the final set and records a complete DROP audit.

   Persist output verbatim to `VERIFIER_AUDIT`, then close the agent. Stop if the KEEP set is empty.

6. **Extract a locked fact manifest.**
   Spawn `sci-research-opportunity-fact-extractor` with the Verifier output, Companies House Analysis, date range, and `FACT_MANIFEST`.

   It writes one YAML entry per selected item, including names, dates, amounts, currencies, percentages, transaction stages, company numbers, registry changes, quotations, image provenance, and source excerpts. Confirm the file exists, then close the agent.

7. **Write the Chinese Markdown.**
   Spawn `sci-research-opportunity-writer` with:

   - Verifier output verbatim
   - Fact Manifest path
   - Companies House Analysis verbatim
   - `OUT_MD`, date range, `total`, and `images`

   The Writer follows `references/output-spec.md`, writes `OUT_MD` using one `apply_patch`, and uses only facts permitted by the manifest. Business implications must be phrased as opportunities, hypotheses, or recommended follow-up, never as confirmed client demand.

8. **Edit and validate.**
   Spawn `sci-research-opportunity-editor` with `OUT_MD`, `FACT_MANIFEST`, Verifier output, Companies House Analysis, and date range.

   It performs sequential passes for factual fidelity, transaction-stage language, Companies House identity, opportunity framing, citations/images, and Chinese fluency. It patches only `OUT_MD` with `apply_patch`.

   Close the Editor, then run the blocking format gate:

   ```bash
   node "$PLUGIN_ROOT/scripts/hooks/opportunity-briefing-format-check.js" --file "$OUT_MD"
   ```

9. **Generate the institutional DOCX.**
   Preflight `python3 -c "import docx"`. If missing, stop and report:

   ```text
   python3 -m pip install --user --upgrade -r {PLUGIN_ROOT}/requirements.txt
   ```

   Generate:

   ```bash
   python3 "$SKILL_DIR/scripts/generate-opportunity-docx.py" \
     --input "$OUT_MD" \
     --output "$OUT_DOCX"
   ```

   The generator attempts to embed eligible images. Image download or format failure must not abort the report; retain the caption and source URL as text.

10. **Email only when explicitly requested.**
    Use only:

    ```bash
    python3 "$PLUGIN_ROOT/scripts/send-report-email.py" \
      --to "$EMAIL" \
      --subject "$EMAIL_SUBJECT" \
      --body "请查收中资企业商机拓展简报（${DATE_FROM}至${DATE_TO}）。" \
      --attach "$OUT_DOCX" "$OUT_MD" \
      [--dry-run]
    ```

    Never implement SMTP inline or use `sendmail` / `mail -s`.

11. **Verify deliverables.**
    Confirm `OUT_MD` and `OUT_DOCX` exist and are non-empty. Report selected-item count, Companies House status, image count, paths, and email status.

## Companies House Boundary

Companies House does not expose a reliable nationality-of-parent-company filter. This skill monitors:

- entities explicitly identified by company number;
- aliases and known UK entities in the optional watchlist;
- company numbers discovered from current reporting and official pages.

Never claim exhaustive discovery of every Chinese-backed UK company. State the monitored universe and any API/watchlist coverage gap in the final report.

## Invocation Examples

```text
$sci-research:china-outbound-opportunity-briefing
$sci-research:china-outbound-opportunity-briefing --date-from 2026-07-06 --date-to 2026-07-12
$sci-research:china-outbound-opportunity-briefing --companies-house required --watchlist ~/.sci-research/config/china-company-watchlist.json
$sci-research:china-outbound-opportunity-briefing --images none --email-dry-run --email "team@example.com"
```
