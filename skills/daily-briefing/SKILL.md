---
name: daily-briefing
description: "Generate a branded SPD Bank Word document (新闻简报, daily briefing, branded docx) from per-country daily news reports. Reads Markdown files from daily-news-reports directory, curates 13-15 top stories across multiple countries, generates branded docx with header logo and footer decoration, and emails the attachment. Supports scheduled/automated execution."
origin: sci-research-plugin
---

# Daily Briefing (Multi-Country Branded 新闻简报)

Generate a branded SPD Bank Word document containing 13-15 curated news stories from multiple countries, then email it. Reads existing per-country Markdown reports as data source — does NOT search the web.

Designed for both interactive and **scheduled/automated** execution.

## Input Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `date` | No | today | Target date in ISO `YYYY-MM-DD` |
| `countries` | No | `中国,英国,美国,欧洲,日本,韩国` | Comma-separated country/region list |
| `total` | No | `14` | Target total number of stories (13-15) |
| `source_dir` | No | `~/.sci-research/reports/daily-news/` | Base directory containing `YYYY-MM-DD/` subdirs produced by `/daily-news-intelligence` |
| `out_dir` | No | `~/.sci-research/reports/daily-briefings/{date}/` | Directory for the generated branded docx. `{date}` is replaced with the ISO date and `~` is expanded at runtime. |
| `email` | No | empty | Comma-separated recipient email addresses |
| `email_subject` | No | `新闻简报 — {date_display}` | Email subject line |
| `email_dry_run` | No | `false` | Preview email without sending |
| `no_wait` | No | `false` | Fail immediately if source files missing |
| `publish` | No | `false` | When `true`, copy this date's branded output into `publish_repo` and commit/push it through the sanctioned publish script. |
| `publish_repo` | Conditional | — | Absolute path or `~`-based path to the target Git repository. Required when `publish=true`. |

Derived fields:
- `date_display` — e.g. `2026年4月16日`
- `date_dir` — `{source_dir}/{date}/`
- `out_docx` — `{out_dir}/{date} 简报.docx`

## Runtime Paths

Before running the workflow, set `SKILL_DIR` to the absolute directory containing this `SKILL.md`, then derive the plugin root once:

```bash
SKILL_DIR=<absolute path to skills/daily-briefing>
PLUGIN_ROOT="$(cd "$SKILL_DIR/../.." && pwd)"
```

Use these absolute paths for every bundled script. Do not rely on the current working directory.

## Workflow

1. **Validate params and bundled resources.** Default `date` to today (`date +%Y-%m-%d`). Parse `countries` into a comma-separated list. Confirm that `SKILL_DIR` is the absolute directory containing this `SKILL.md`, derive every bundled-resource path once, then expand `~` and substitute `{date}` in `source_dir` / `out_dir`. Create `OUT_DIR`. If `publish=true`, require a non-empty `publish_repo` and expand `~` in it to `PUBLISH_REPO`. Compute derived fields:
   ```bash
   if [[ -z "${SKILL_DIR:-}" || ! -f "$SKILL_DIR/SKILL.md" ]]; then
     echo "ERROR: SKILL_DIR must be the absolute skills/daily-briefing directory." >&2
     exit 2
   fi
   PLUGIN_ROOT="$(cd "$SKILL_DIR/../.." && pwd)"
   GENERATOR="$SKILL_DIR/scripts/generate-branded-docx.py"
   TEMPLATE="$SKILL_DIR/template/briefing-template.docx"
   EMAIL_SENDER="$SKILL_DIR/scripts/send-briefing-email.py"
   PUBLISH_SCRIPT="$PLUGIN_ROOT/scripts/publish-reports.sh"
   for REQUIRED_PATH in "$GENERATOR" "$TEMPLATE" "$EMAIL_SENDER" "$PUBLISH_SCRIPT" "$PLUGIN_ROOT/.codex-plugin/plugin.json"; do
     if [[ ! -f "$REQUIRED_PATH" ]]; then
       echo "ERROR: installed sci-research bundle is incomplete: $REQUIRED_PATH" >&2
       exit 2
     fi
   done

   SOURCE_DIR="${source_dir/#\~/$HOME}"
   OUT_DIR="${out_dir/#\~/$HOME}"
   OUT_DIR="${OUT_DIR//\{date\}/$DATE}"
   DATE_DIR="$SOURCE_DIR/$DATE"
   DATE_DISPLAY="$(python3 -c "from datetime import date; d=date.fromisoformat('$DATE'); print(f'{d.year}年{d.month}月{d.day}日')")"
   mkdir -p "$OUT_DIR"
   OUT_DOCX="$OUT_DIR/${DATE} 简报.docx"
   if [[ "$publish" == true ]]; then
     if [[ -z "${publish_repo:-}" ]]; then
       echo "ERROR: --publish requires --publish-repo <git-path>." >&2
       exit 2
     fi
     PUBLISH_REPO="${publish_repo/#\~/$HOME}"
   fi
   ```

2. **Check source directory.** List Markdown files:
   ```bash
   MD_FILES=$(find "$DATE_DIR" -maxdepth 1 -name "*.md" -type f 2>/dev/null)
   MD_COUNT=$(echo "$MD_FILES" | grep -c .)
   ```
   If `MD_COUNT >= 1`, proceed to Step 5. If zero and `--no-wait` is set, jump to Step 4. Otherwise proceed to Step 3. Note: the source directory may not exist yet (e.g. if Pipeline C hasn't run), which is normal — `find` returns empty.

3. **Wait and retry** (5 minutes). Report: "Source files not found. Waiting 5 minutes for upstream pipeline to complete..."
   ```bash
   sleep 300
   find "$DATE_DIR" -maxdepth 1 -name "*.md" -type f 2>/dev/null
   ```
   If files found, proceed to Step 5. If still none, proceed to Step 4.

4. **Send "no report" notification** (fallback path). If `email` is set, send a notification email per `references/email-spec.md` § Body Template (no report available):
   ```bash
   python3 "$EMAIL_SENDER" \
     --to "$EMAIL" \
     --subject "⚠️ 新闻简报未生成 — $DATE_DISPLAY" \
     --body "今日（$DATE）的每日新闻源文件未找到..." \
     ${DRY_RUN_FLAG}
   ```
   Then STOP. Do not proceed further.

5. **Preflight python-docx.** Do **not** install dependencies during a run:
   ```bash
   python3 -c "import docx"
   ```
   If that command fails, stop before curation and report: `Pipeline D requires python-docx. Install or update it once outside the pipeline with: python3 -m pip install --user --upgrade -r $PLUGIN_ROOT/requirements.txt`. The generator prints the exact installed-plugin path in the same error message. Do not invoke `pip` or `pip3 install` from the pipeline.

6. **Curate and rewrite stories.** First, list the source files for the agent:
   ```bash
   MD_FILES=$(find "$DATE_DIR" -maxdepth 1 -name "*.md" -type f | sort)
   ```
   Spawn the `briefing-curator` subagent (`.codex/agents/briefing-curator.toml`; model + reasoning effort come from the TOML) with this prompt:

   ```
   Read all Markdown files listed below and produce a unified briefing.
   
   Countries: {countries}
   Target stories: {total}
   Date: {DATE_DISPLAY}
   
   Files to read (use the Read tool on each):
   {each line of MD_FILES as a full path, one per line}
   
   Create or overwrite /tmp/briefing-curator-output.txt using one `apply_patch` operation.
   
   Output format: TITLE/DATE/TOC/STORIES/REFERENCES/DISCLAIMER
   as specified in your system prompt (.codex/agents/briefing-curator.toml).
   ```

   The Agent reads each MD file via the Read tool, selects and rewrites stories, then writes its structured output to a temp file. The orchestrator uses this file as input to Step 7.
   
   Expected output schema (see `.codex/agents/briefing-curator.toml` for full spec):
   ```
   TITLE: 新闻简报
   DATE: {YYYY年M月D日}
   TOC:
   - {headline 1}
   ...
   STORIES:
   **1.{title}**
   {paragraph} [1]
   ...
   REFERENCES:
   [1]  {URL}
   ...
   DISCLAIMER:
   免责声明：...
   ```
   
   If the Agent output file is empty or missing, stop and report: "Curator agent produced no output."

7. **Generate branded docx.** Use the curator output file from Step 6:
   ```bash
   CURATOR_FILE="/tmp/briefing-curator-output.txt"
   
   python3 "$GENERATOR" \
     --template "$TEMPLATE" \
     --input "$CURATOR_FILE" \
     --output "$OUT_DOCX"
   
   GEN_EXIT=$?
   rm -f "$CURATOR_FILE"
   ```
   Handle exit codes:
   - 0 = success, proceed to email
   - 1 = python-docx not installed → report and stop
   - 2 = template file not found → report and stop
   - 3 = curator output could not be parsed (empty/malformed) → report and stop
   - 4 = docx save failed → report and stop
   
   On any non-zero exit, do NOT proceed to email.

8. **Send email** (optional — only if `email` is non-empty). Build subject and body per `references/email-spec.md`, then:
   ```bash
   BODY_FILE=$(mktemp /tmp/briefing-body.XXXXXX.txt)
   # (write body to $BODY_FILE)
   
   python3 "$EMAIL_SENDER" \
     --to "$EMAIL" \
     --subject "$EMAIL_SUBJECT" \
     --body-file "$BODY_FILE" \
     --attach "$OUT_DOCX" \
     ${DRY_RUN_FLAG}
   
   SEND_EXIT=$?
   rm -f "$BODY_FILE"
   ```
   Email failure never deletes the generated docx.

   **⚠️ Hard rule — sanctioned script only.** The orchestrator MUST invoke `scripts/send-briefing-email.py` via the Bash subprocess above. **Do NOT** implement email delivery inline using `smtplib`, `email.message`, `email.mime`, `MIMEMultipart`, `MIMEText`, `EmailMessage`, or by shelling out to `sendmail` / `mail -s`. Inline implementations skip the dual `Content-Disposition` filename encoding the sanctioned script applies — without both forms, attachments land as `noname` on corporate Exchange / Outlook. A PreToolUse hook (`scripts/hooks/email-send-guard.js`) rejects Bash commands matching inline SMTP patterns. On non-zero script exit, halt and report — do NOT fall back to inline SMTP.

9. **Verify delivery.**
   ```bash
   ls -la "$OUT_DOCX"
   ```
   Report file path, size, and story count.

10. **Publish to GitHub Pages (explicit opt-in).** Skip this step unless `publish=true`. When enabled, `publish_repo` must resolve to an existing Git repository. The sanctioned script copies `OUT_DIR` into `PUBLISH_REPO/<date>/`, then stages, commits, and pushes:
    ```bash
    REPORTS_REPO="$PUBLISH_REPO" bash "$PUBLISH_SCRIPT" \
      --source-dir "$OUT_DIR"
    ```
    Publish failures must be reported but never delete or invalidate the local docx.

## References

| File | Contents |
|------|----------|
| `.codex/agents/briefing-curator.toml` (repo root) | Curator agent definition: selection criteria, writing style, output format schema |
| `references/email-spec.md` | Email subject/body templates, exit code handling |
| `template/briefing-template.docx` | SPD Bank branded docx template (header logo + footer decoration) |
| `scripts/generate-branded-docx.py` | Docx generation from curator output (exit codes 0-4) |
| `scripts/send-briefing-email.py` | Gmail SMTP email sender (exit codes 0-5) |

## Invocation Examples

```
/daily-briefing --email "you@gmail.com"
/daily-briefing --date 2026-04-16 --email "you@gmail.com"
/daily-briefing --date 2026-04-16 --countries "中国,英国,美国,欧洲" --total 12 --email "you@gmail.com"
/daily-briefing --date 2026-04-16 --email "a@x.com,b@y.com" --email-dry-run
/daily-briefing --date 2026-04-16 --email "you@gmail.com" --no-wait
```
