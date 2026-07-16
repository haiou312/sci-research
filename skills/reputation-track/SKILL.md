---
name: reputation-track
description: "Monitor a company and its current executives for reputation risk (reputation tracking, adverse media, company risk monitoring, 声誉监控, 声誉追踪). A GPT-5.6 Luna Scanner resolves the company and executives through Yahoo Finance, searches exact-date non-mainland-China media and public social media, a Verifier grades genuine findings as low/medium/high, and a Writer creates an HTML alert for controlled email delivery."
---

# Reputation Track

Monitor one company and its current executives for a single date:

```text
Scanner → Verifier → Writer → controlled email script
```

A clean run is silent: no HTML and no email.

## Parameters

| Parameter | Required | Default |
|---|---|---|
| `company` | yes | - |
| `date` | no | today |
| `lang` | no | `zh` (`zh` or `en`) |
| `email` | yes | - |
| `email_dry_run` | no | `false` |

Output is fixed at:

```text
~/.sci-research/reports/reputation/{date}/{company-slug}-reputation-{date}.html
```

## Runtime

Set:

```bash
SKILL_DIR=<absolute path to skills/reputation-track>
PLUGIN_ROOT="$(cd "$SKILL_DIR/../.." && pwd)"
RUNTIME_SYNC="$PLUGIN_ROOT/skills/setup-sci-research-runtime/scripts/sync_runtime.py"
```

Before the pipeline, run:

```bash
python3 "$RUNTIME_SYNC" --project-root "$PWD" --check
```

If it fails, stop and tell the user to run `$sci-research:setup-sci-research-runtime` in this workspace and start a new Codex task.

## Custom-Agent Dispatch

Use the exact custom-agent selector with `fork_turns="none"`:

- `sci-research-reputation-scanner` - `gpt-5.6-luna / medium`
- `sci-research-reputation-verifier` - `gpt-5.6-terra / high`
- `sci-research-reputation-writer` - `gpt-5.6-terra / medium`

Do not pass model overrides, use generic agents, or embed agent bodies in spawn prompts. Every prompt begins with absolute `plugin_root` and `skill_root`.

## Workflow

1. Validate `company`, ISO `date`, `lang`, and recipient `email`. Default `date` to today.

2. Spawn `sci-research-reputation-scanner` with `company_input` and `date`.

   The Scanner:

   - resolves the official company, ticker, and current key executives through Yahoo Finance;
   - searches every identified subject across non-mainland-China media and public social media;
   - excludes mainland Chinese media, mainland Chinese government domains, and mainland Chinese social platforms;
   - admits only opened pages with evidence and a publication time matching `date`;
   - chooses its own queries, languages, sources, platforms, depth, and follow-up paths;
   - does not judge negativity, severity, or duplicate events.

   If `status: needs-clarification`, stop and report `resolution_note`.

3. Spawn `sci-research-reputation-verifier` with the full Scanner output verbatim.

   The Verifier:

   - keeps only content directly concerning the company or an identified executive;
   - removes positive, neutral, irrelevant, promotional, or unverifiable content;
   - grades genuine reputation risk as `high`, `medium`, or `low`;
   - merges duplicate coverage of the same event;
   - preserves allegations as allegations and labels social content as posts, complaints, or discussions.

   There is no T1-T4 system, source matrix, risk-category taxonomy, `critical` level, confidence score, source-based severity adjustment, or minimum-severity filter.

4. If the Verifier returns `findings: []`, exit silently. Do not create the output directory, write HTML, or send email.

5. For a non-empty finding set:

   - derive `company_display` from the Scanner's official Yahoo Finance name;
   - derive `date_display` in `lang`;
   - create `~/.sci-research/reports/reputation/{date}/`;
   - derive `out_html` using a lowercase ASCII slug where possible while preserving CJK characters.

6. Spawn `sci-research-reputation-writer` with the complete Verifier output plus `company_display`, `date_display`, `lang`, and absolute `out_html`.

   The Writer uses one `apply_patch` operation and renders findings in `high`, `medium`, `low` order under `references/html-template.md`.

7. Verify that `out_html` starts with `<!DOCTYPE html>` and contains `company_display`. If invalid, retry the Writer once; never email malformed HTML.

8. Build the automatic subject from `references/email-spec.md`, then send with:

   ```bash
   python3 "$PLUGIN_ROOT/scripts/send-report-email.py" \
     --to "$email" \
     --subject "$subject" \
     --body-html-file "$out_html"
   ```

   Add `--dry-run` only when `email_dry_run=true`.

   The controlled script is mandatory. Do not implement SMTP inline or use `sendmail` / `mail -s`. Email failure must not delete the HTML file.

## References

| File | Purpose |
|---|---|
| `references/schemas.md` | Scanner and Verifier handoff |
| `references/severity-rules.md` | Verifier low/medium/high judgement |
| `references/html-template.md` | Minimal HTML requirements |
| `references/email-spec.md` | Subject and controlled delivery |

## Examples

```text
$sci-research:reputation-track --company "AAPL" --email "risk@example.com"
$sci-research:reputation-track --company "Tesla" --date 2026-07-16 --lang en --email "risk@example.com"
$sci-research:reputation-track --company "9988.HK" --email "risk@example.com" --email-dry-run
```
