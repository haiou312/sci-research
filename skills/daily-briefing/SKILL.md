---
name: daily-briefing
description: "Generate a branded SPD Bank Word document (新闻简报, daily briefing, branded docx) from per-country Pipeline C Markdown reports. Curates 13-15 top stories across multiple countries, generates a branded docx with header logo and footer decoration, and optionally emails the attachment. Supports scheduled/automated execution."
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
| `source_dir` | No | `~/.sci-research/reports/daily-news/` | Base directory containing `YYYY-MM-DD/` subdirs produced by `$sci-research:daily-news-intelligence` |
| `out_dir` | No | `~/.sci-research/reports/daily-briefings/{date}/` | Directory for the generated branded docx. `{date}` is replaced with the ISO date and `~` is expanded at runtime. |
| `email` | No | empty | Comma-separated recipient email addresses |
| `email_subject` | No | `新闻简报 — {date_display}` | Email subject line |
| `email_dry_run` | No | `false` | Preview email without sending |
| `no_wait` | No | `false` | Fail immediately if source files missing |

Derived fields:
- `date_display` — e.g. `2026年4月16日`
- `date_dir` — `{source_dir}/{date}/`
- `out_docx` — `{out_dir}/{date} 简报.docx`

## Runtime Paths

Before running the workflow, set `SKILL_DIR` to the absolute directory containing this `SKILL.md`, then derive the plugin root once:

```bash
SKILL_DIR=<absolute path to skills/daily-briefing>
PLUGIN_ROOT="$(cd "$SKILL_DIR/../.." && pwd)"
RUNTIME_SYNC="$PLUGIN_ROOT/skills/setup-sci-research-runtime/scripts/sync_runtime.py"
```

Use these absolute paths for every bundled script. Do not rely on the current working directory. Before Step 1, run `python3 "$RUNTIME_SYNC" --project-root "$PWD" --check`. If it fails, stop and tell the user to run `$sci-research:setup-sci-research-runtime` in this workspace, then start a new Codex task.

## Subagent Dispatch Rule

Pipeline D uses the installed `sci-research-briefing-curator` custom agent. Select that exact role through the spawn tool's agent-type/role selector; `task_name` is only a thread label. Set `fork_turns="none"`, do not pass model or reasoning overrides, and start the prompt with absolute `plugin_root: {PLUGIN_ROOT}` and `skill_root: {SKILL_DIR}`.

If the active Codex surface exposes no custom-agent selector, rejects the role as unknown, or cannot start it with `fork_turns="none"`, halt. Do not substitute a generic agent or embed the curator TOML instructions in the prompt.

After the curator result and output file have been captured and validated, call `close_agent` before continuing. If the curator fails, close its thread before stopping or retrying; halt if the completed child cannot be closed.

## Workflow

1. **Validate params and bundled resources.** Default `date` to today (`date +%Y-%m-%d`). Parse `countries` into a comma-separated list. Confirm that `SKILL_DIR` is the absolute directory containing this `SKILL.md`, derive every bundled-resource path once, then expand `~` and substitute `{date}` in `source_dir` / `out_dir`. Create `OUT_DIR`. Compute derived fields:
   ```bash
   if [[ -z "${SKILL_DIR:-}" || ! -f "$SKILL_DIR/SKILL.md" ]]; then
     echo "ERROR: SKILL_DIR must be the absolute skills/daily-briefing directory." >&2
     exit 2
   fi
   PLUGIN_ROOT="$(cd "$SKILL_DIR/../.." && pwd)"
   GENERATOR="$SKILL_DIR/scripts/generate-branded-docx.py"
   TEMPLATE="$SKILL_DIR/template/briefing-template.docx"
   EMAIL_SENDER="$SKILL_DIR/scripts/send-briefing-email.py"
   RUNTIME_SYNC="$PLUGIN_ROOT/skills/setup-sci-research-runtime/scripts/sync_runtime.py"
   for REQUIRED_PATH in "$GENERATOR" "$TEMPLATE" "$EMAIL_SENDER" "$RUNTIME_SYNC" "$PLUGIN_ROOT/.codex-plugin/plugin.json"; do
     if [[ ! -f "$REQUIRED_PATH" ]]; then
       echo "ERROR: installed sci-research bundle is incomplete: $REQUIRED_PATH" >&2
       exit 2
     fi
   done
   python3 "$RUNTIME_SYNC" --project-root "$PWD" --check || exit 2

   SOURCE_DIR="${source_dir/#\~/$HOME}"
   OUT_DIR="${out_dir/#\~/$HOME}"
   OUT_DIR="${OUT_DIR//\{date\}/$DATE}"
   DATE_DIR="$SOURCE_DIR/$DATE"
   DATE_DISPLAY="$(python3 -c "from datetime import date; d=date.fromisoformat('$DATE'); print(f'{d.year}年{d.month}月{d.day}日')")"
   mkdir -p "$OUT_DIR"
   OUT_DOCX="$OUT_DIR/${DATE} 简报.docx"
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
   Spawn `sci-research-briefing-curator` (`.codex/agents/sci-research-briefing-curator.toml`) per § Subagent Dispatch Rule with this prompt:

   ```
   plugin_root: {PLUGIN_ROOT}
   skill_root: {SKILL_DIR}

   Read all Markdown files listed below and produce a unified briefing.
   
   Countries: {countries}
   Target stories: {total}
   Date: {DATE_DISPLAY}
   
   Files to read (use the Read tool on each):
   {each line of MD_FILES as a full path, one per line}
   
   Create or overwrite /tmp/briefing-curator-output.txt using one `apply_patch` operation.
   
   Output format: TITLE/DATE/TOC/STORIES/REFERENCES/DISCLAIMER
   as specified in your custom-agent instructions (.codex/agents/sci-research-briefing-curator.toml).
   ```

   The Agent reads each MD file via the Read tool, selects and rewrites stories, then writes its structured output to a temp file. The orchestrator uses this file as input to Step 7.
   
   Expected output schema (see `.codex/agents/sci-research-briefing-curator.toml` for full spec):
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
   
   Check the output path, capture whether it is valid, then close the curator thread. If the Agent output file is empty or missing, stop and report: "Curator agent produced no output." Otherwise continue to Step 7.

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

## References

| File | Contents |
|------|----------|
| `.codex/agents/sci-research-briefing-curator.toml` (plugin payload; installed project-locally by setup) | Curator agent definition: selection criteria, writing style, output format schema |
| `references/email-spec.md` | Email subject/body templates, exit code handling |
| `template/briefing-template.docx` | SPD Bank branded docx template (header logo + footer decoration) |
| `scripts/generate-branded-docx.py` | Docx generation from curator output (exit codes 0-4) |
| `scripts/send-briefing-email.py` | Gmail SMTP email sender (exit codes 0-5) |

## Invocation Examples

```
$sci-research:daily-briefing --email "you@gmail.com"
$sci-research:daily-briefing --date 2026-04-16 --email "you@gmail.com"
$sci-research:daily-briefing --date 2026-04-16 --countries "中国,英国,美国,欧洲" --total 12 --email "you@gmail.com"
$sci-research:daily-briefing --date 2026-04-16 --email "a@x.com,b@y.com" --email-dry-run
$sci-research:daily-briefing --date 2026-04-16 --email "you@gmail.com" --no-wait
```
