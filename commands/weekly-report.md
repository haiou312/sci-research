---
description: Generate a weekly macro & market report (Market event/Money Market/Fixed Income/FX/Commodity) from the prior 7 days of /daily-news-intelligence reports plus FRED/BOE/BOJ/yfinance live data. Usage: /weekly-report [--end-date YYYY-MM-DD] [--start-date YYYY-MM-DD] [--countries "CN,US,UK,EU,JP,KR"] [--lang zh|en|ja] [--out-dir <path>] [--news-dir <path>] [--commodity-symbols "GC=F,SI=F,CL=F"] [--kr-bond-symbol 148070.KS] [--email <a@x.com,b@y.com>] [--email-attach both|docx|md|none] [--email-dry-run]
---

# Weekly Macro & Market Report

Produce a dated weekly research report fusing news context (from existing daily briefings) with live market data (rates, FX, commodities). Three-stage pipeline runs Market event aggregation and market-data collection in parallel, then a single Writer call composes the localised Markdown.

## Parameter Parsing

1. `--end-date` (optional, default: today): ISO `YYYY-MM-DD`. Anchors the 7-day window and the output filename.
2. `--start-date` (optional, default: `end_date - 6 days`): ISO. Use to override the window.
3. `--countries` (optional, default: `CN,US,UK,EU,JP,KR`): Comma-separated country codes. Drives Market event sub-sections and the KR Fixed Income row.
4. `--lang` (optional, default: `zh`): `zh` / `en` / `ja`.
5. `--out-dir` (optional, default: `~/Desktop/weekly-reports/{end-date}/`): Auto-created. `~` and `{end-date}` are expanded.
6. `--news-dir` (optional, default: `~/Desktop/daily-news-reports`): Source folder for Stage A; must contain the prior week's daily reports.
7. `--commodity-symbols` (optional, default: `GC=F,SI=F,CL=F`): yfinance tickers for the Commodity table.
8. `--kr-bond-symbol` (optional, default: `148070.KS`): yfinance ticker for the KR Fixed Income proxy row.
9. `--email` (optional, default: empty): Comma-separated recipients. Triggers Gmail SMTP send when non-empty. Requires `GOOGLE_EMAIL_USERNAME` and `GOOGLE_EMAIL_APP_PASSWORD`.
10. `--email-subject` / `--email-body` (optional): Override defaults. Defaults are derived from the localised H1 title plus the date range.
11. `--email-attach` (optional, default: `both`): `both` / `docx` / `md` / `none`.
12. `--email-dry-run` (optional, default: `false`): Build email and print preview without connecting to SMTP.

## Execution Pipeline

### Step 1: Confirm Scope

```
📊 Weekly Report: {start_date} → {end_date}
🌍 Countries: {countries}
🌐 Language: {lang}
📁 Output: {out_md}
📰 News source: {news_dir}
📧 Email: {email or "(skipped)"}{dry-run hint}

Proceed? (Y/n)
```

### Step 2: Delegate to Skill

Invoke the `weekly-report` skill with all parsed arguments. The skill owns:

1. The pre-check (`pip install -r requirements.txt` if needed; warn if `FRED_API_KEY` missing).
2. Parallel launch of `weekly-news-aggregator` (Stage A) and `market-data-collector` (Stage B).
3. The `weekly-report-writer` (Stage C) call that consumes both bundles and writes the Markdown.
4. `pandoc` docx export (skipped silently if pandoc absent).
5. Optional Gmail SMTP send via `scripts/send-report-email.py`.

### Step 3: Deliver

- Run `ls -la "{out_md}" "{out_docx}"` to confirm files.
- Print file paths, count of Market event countries with content, and any Data Gaps the Writer surfaced.

## Required Environment

- `FRED_API_KEY` — required for Money Market, Fixed Income US block, and FX. If unset, those sections become Data Gaps; other sections (BOE, BOJ, yfinance, Market event) still work.
- `GOOGLE_EMAIL_USERNAME` + `GOOGLE_EMAIL_APP_PASSWORD` — only when `--email` is non-empty.

## Examples

### Example 1: Default (last 7 days, zh, all six countries)

```
/weekly-report
```

### Example 2: English output with explicit end date

```
/weekly-report --end-date 2026-04-26 --lang en
```

### Example 3: Japanese output, narrow country set

```
/weekly-report --end-date 2026-04-26 --lang ja --countries "JP,US,EU"
```

### Example 4: Dry-run email preview

```
/weekly-report --end-date 2026-04-26 --email "you@gmail.com" --email-dry-run
```

### Example 5: Custom commodity basket

```
/weekly-report --commodity-symbols "GC=F,SI=F,CL=F,BZ=F,HG=F"
```

### Example 6: Custom KR bond proxy (3Y instead of 10Y)

```
/weekly-report --kr-bond-symbol 114820.KS
```

## Related Skills

- `skills/weekly-report/SKILL.md` — orchestrator + workflow detail.
- `skills/daily-news-intelligence/SKILL.md` — produces the daily briefings consumed by Stage A.
- `skills/news-scan/SKILL.md` — multi-topic scan over 7-90 day windows (different use case).
