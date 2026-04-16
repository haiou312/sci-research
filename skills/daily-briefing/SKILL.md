---
name: daily-briefing
description: "Generate a branded SPD Bank Word document (新闻简报, daily briefing, branded docx) from per-country daily news reports. Reads Markdown files from daily-news-reports directory, curates 13-15 top stories across multiple countries, generates branded docx with header logo and footer decoration, and emails the attachment. Supports scheduled/automated execution."
origin: sci-research-plugin
---

# Daily Briefing (Multi-Country Branded 新闻简报)

Generate a branded SPD Bank Word document containing 13-15 curated news stories from multiple countries, then email it. Reads existing per-country Markdown reports as data source — does NOT search the web.

Designed for both interactive and **scheduled/automated** execution.

## Quick Reference (Orchestrator Checklist)

```
1. Validate params → expand ~ → compute paths
2. Check source dir for MD files
3. IF no files and --no-wait not set → sleep 300 → recheck
4. IF still no files → send "no report" email → STOP
5. Ensure python-docx installed
6. Launch briefing-curator Agent → capture structured output
7. Write output to temp file → run generate-branded-docx.py
8. IF --email → run send-briefing-email.py
9. Verify: ls docx, report story count
```

## Input Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `date` | No | today | Target date in ISO `YYYY-MM-DD` |
| `countries` | No | `中国,英国,美国,欧洲,日本,韩国` | Comma-separated country/region list |
| `total` | No | `14` | Target total number of stories (13-15) |
| `source_dir` | No | `~/Desktop/daily-news-reports/` | Base directory containing `YYYY-MM-DD/` subdirs |
| `email` | No | empty | Comma-separated recipient email addresses |
| `email_subject` | No | `新闻简报 — {date_display}` | Email subject line |
| `email_dry_run` | No | `false` | Preview email without sending |
| `no_wait` | No | `false` | Fail immediately if source files missing |

Derived fields:
- `date_display` — e.g. `2026年4月16日`
- `date_dir` — `{source_dir}/{date}/`
- `out_docx` — `{source_dir}/{date}/{date} 简报.docx`

## Workflow

1. **Validate params.** Default `date` to today (`date +%Y-%m-%d`). Parse `countries` into a comma-separated list. Expand `~` in `source_dir`. Compute derived fields:
   ```bash
   SOURCE_DIR="${source_dir/#\~/$HOME}"
   DATE_DIR="$SOURCE_DIR/$DATE"
   DATE_DISPLAY="$(python3 -c "from datetime import date; d=date.fromisoformat('$DATE'); print(f'{d.year}年{d.month}月{d.day}日')")"
   OUT_DOCX="$DATE_DIR/${DATE} 简报.docx"
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
   python3 "${SKILL_DIR}/scripts/send-briefing-email.py" \
     --to "$EMAIL" \
     --subject "⚠️ 新闻简报未生成 — $DATE_DISPLAY" \
     --body "今日（$DATE）的每日新闻源文件未找到..." \
     ${DRY_RUN_FLAG}
   ```
   Then STOP. Do not proceed further.

5. **Ensure python-docx.** Install if missing:
   ```bash
   python3 -c "import docx" 2>/dev/null || pip3 install python-docx --user --quiet
   ```
   If `pip3 install` also fails, stop and report: "python-docx installation failed. Install manually: pip3 install python-docx"

6. **Curate and rewrite stories.** First, list the source files for the agent:
   ```bash
   MD_FILES=$(find "$DATE_DIR" -maxdepth 1 -name "*.md" -type f | sort)
   ```
   Launch a `briefing-curator` Agent (opus, subagent_type: `general-purpose`, model: `opus`) with this prompt:

   ```
   Read all Markdown files listed below and produce a unified briefing.
   
   Countries: {countries}
   Target stories: {total}
   Date: {DATE_DISPLAY}
   
   Files to read (use the Read tool on each):
   {each line of MD_FILES as a full path, one per line}
   
   Write the output to /tmp/briefing-curator-output.txt using the Write tool.
   
   Output format: TITLE/DATE/TOC/STORIES/REFERENCES/DISCLAIMER
   as specified in your system prompt (agents/briefing-curator.md).
   ```

   The Agent reads each MD file via the Read tool, selects and rewrites stories, then writes its structured output to a temp file. The orchestrator uses this file as input to Step 7.
   
   If the Agent output file is empty or missing, stop and report: "Curator agent produced no output."

7. **Generate branded docx.** Use the curator output file from Step 6:
   ```bash
   CURATOR_FILE="/tmp/briefing-curator-output.txt"
   
   python3 "${SKILL_DIR}/scripts/generate-branded-docx.py" \
     --template "${SKILL_DIR}/template/briefing-template.docx" \
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
   
   python3 "${SKILL_DIR}/scripts/send-briefing-email.py" \
     --to "$EMAIL" \
     --subject "$EMAIL_SUBJECT" \
     --body-file "$BODY_FILE" \
     --attach "$OUT_DOCX" \
     ${DRY_RUN_FLAG}
   
   SEND_EXIT=$?
   rm -f "$BODY_FILE"
   ```
   Email failure never deletes the generated docx.

9. **Verify delivery.**
   ```bash
   ls -la "$OUT_DOCX"
   ```
   Report file path, size, and story count.

## Stage → Agent Map

| Stage | Agent | Model | Tools |
|-------|-------|-------|-------|
| Curator | `briefing-curator` | opus | Read, Grep, Glob |
| Docx generation | — (Python script) | — | — |
| Email delivery | — (Python script) | — | — |

## References

| File | Contents |
|------|----------|
| `agents/briefing-curator.md` (repo root) | Curator agent definition: selection criteria, writing style, output format schema |
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
