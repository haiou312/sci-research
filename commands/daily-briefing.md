---
description: Generate a branded SPD Bank Word document (新闻简报) from per-country daily news reports and email it. Reads from daily-news-reports directory, curates 13-15 top stories, generates branded docx. Usage: /daily-briefing [--date YYYY-MM-DD] [--countries "中国,英国,..."] [--total 14] [--source-dir <path>] [--email <a@x.com>] [--email-subject <text>] [--email-dry-run] [--no-wait]
---

# Daily Briefing (Multi-Country Branded 新闻简报)

Generate a branded SPD Bank Word document containing 13-15 curated top stories from multiple countries. Reads existing per-country Markdown reports — does not search the web.

## Parameter Parsing

1. `--date` (optional, default: today): Target date in ISO `YYYY-MM-DD`.
2. `--countries` (optional, default: `"中国,英国,美国,欧洲,日本,韩国"`): Comma-separated country/region list. Stories are distributed evenly across these countries.
3. `--total` (optional, default: `14`): Target total number of stories (13-15 range).
4. `--source-dir` (optional, default: `~/Desktop/daily-news-reports/`): Base directory containing `YYYY-MM-DD/` subdirectories with per-country Markdown files.
5. `--email` (optional): Comma-separated recipient email addresses. When set, the branded docx is emailed via Gmail SMTP.
6. `--email-subject` (optional, default: `新闻简报 — {date_display}`): Email subject line.
7. `--email-dry-run` (optional): Preview email without sending.
8. `--no-wait` (optional): If source files not found, fail immediately instead of waiting 5 minutes.

## Execution Pipeline

### Step 1: Confirm Scope

Display:

```
📰 新闻简报
📅 Date: {date} ({date_display})
🌐 Countries: {countries}
📊 Target stories: {total}
📁 Source: {source_dir}/{date}/
📧 Email: {email or "(skipped)"}

Proceed? (Y/n)
```

### Step 2: Delegate to Skill

Invoke the `daily-briefing` skill and pass through all parsed arguments. The skill will:

1. Check for source Markdown files in `{source_dir}/{date}/`.
2. If missing, wait 5 minutes and retry (unless `--no-wait`).
3. If still missing, send "no report" notification email and stop.
4. Launch the `briefing-curator` Agent to read all country reports and select the top stories.
5. Generate a branded docx using the SPD Bank template.
6. Email the docx (if `--email` set).

### Step 3: Deliver

- Print file path and size of the generated docx.
- Print story count and country distribution.
- If email was sent, print confirmation.

## Examples

### Default (today, all 6 countries, 14 stories)

```
/daily-briefing --email "you@gmail.com"
```

### Specific date

```
/daily-briefing --date 2026-04-16 --email "you@gmail.com"
```

### Custom countries and count

```
/daily-briefing --date 2026-04-16 --countries "中国,英国,美国,欧洲" --total 12 --email "you@gmail.com"
```

### Dry-run email preview

```
/daily-briefing --date 2026-04-16 --email "you@gmail.com" --email-dry-run
```

### No wait (for scheduled runs that should fail fast)

```
/daily-briefing --date 2026-04-16 --email "you@gmail.com" --no-wait
```
