---
name: weekly-report
description: "Generate a global macro & market weekly report (周报, weekly research report, market weekly) in zh/en/ja. Reads the previous 7 days of /daily-news-intelligence reports for the Market event section and pulls live market data: FRED for Money Market and FX, Bank of England + Bank of Japan + FRED for Fixed Income, yfinance ETF proxy for KR, yfinance futures for Commodity. Three-stage pipeline (aggregator + market-data-collector + writer) with optional pandoc docx export and Gmail SMTP delivery."
origin: sci-research-plugin
---

# Weekly Macro & Market Report

Produce a dated weekly report covering Market event + Money Market + Fixed Income + Foreign Exchange + Commodity for a configurable country set (default `CN, US, UK, EU, JP, KR`). News input is the prior week of `/daily-news-intelligence` outputs, not fresh web scans.

## Quick Reference (Orchestrator Checklist)

```
0. Pre-check: ensure FRED_API_KEY in env; pip install -q -r requirements.txt
1. Validate params → compute derived fields (start_date, end_date, country_display, out_md)
2. Stage A & Stage B IN PARALLEL (single message, two Task tool calls):
     • weekly-news-aggregator   → WeeklyEventsBundle JSON
     • market-data-collector    → MarketDataBundle JSON
3. Stage C: weekly-report-writer (consumes A+B verbatim) → Write to out_md
4. mkdir -p out_dir → pandoc export (skip if pandoc missing)
5. IF --email → send via scripts/send-report-email.py (dry-run honored)
6. Verify: ls out_md, grep section count, surface data gaps
```

## Operating Principle

- **News evidence**: Stage A reads ONLY existing `~/Desktop/daily-news-reports/*.md` files in the window. No web search, no re-verification.
- **Market data evidence**: Stage B calls FRED / BOE / BOJ / yfinance via local Python scripts. Each script returns either valid JSON or an error envelope; failures become Data Gaps, not silent zeros.
- **Authoritative source order** for Fixed Income: BOE for UK, BOJ for JP, FRED for US, yfinance ETF proxy for KR. Use FRED proxies (UK/JP rows in `fred_fixed_income.py`) only when the authoritative source returns empty.

## Input Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `end_date` | No | today | ISO `YYYY-MM-DD`; anchors the 7-day window |
| `start_date` | No | `end_date - 6d` | ISO; lets you override the window |
| `countries` | No | `CN,US,UK,EU,JP,KR` | Comma-separated country codes; drives Market event scope and Fixed Income KR row |
| `lang` | No | `zh` | Output language: `zh` / `en` / `ja` |
| `out_dir` | No | `~/Desktop/weekly-reports/{end_date}/` | `~` and `{end_date}` expanded at runtime; auto-created |
| `news_dir` | No | `~/Desktop/daily-news-reports` | Source folder for Stage A |
| `commodity_symbols` | No | `GC=F,SI=F,CL=F` | yfinance tickers for Commodity section |
| `kr_bond_symbol` | No | `148070.KS` | yfinance ticker for KR Fixed Income row |
| `boe_tenors` / `boj_tenors` | No | `2Y,5Y,10Y,30Y` | Tenors filter for BOE / BOJ |
| `email` | No | empty | Comma-separated recipients; non-empty triggers Step 5 |
| `email_subject` / `email_body` / `email_attach` / `email_dry_run` | No | auto / auto / `both` / `false` | Same semantics as `/daily-news-intelligence` |

Derived fields (`country_display` per country, `out_md` path) come from `references/language-spec.md`.

## Required Environment

- `FRED_API_KEY` (required for Money Market / Fixed Income US block / FX). If missing, those scripts return error envelopes and their data flows into the Data Gaps section.
- `GOOGLE_EMAIL_USERNAME` / `GOOGLE_EMAIL_APP_PASSWORD` (only when `--email` is non-empty). Same as `/daily-news-intelligence`.

## Workflow

### Step 0: Pre-check

```bash
python3 -c "import yfinance, fredapi, openpyxl, requests" 2>/dev/null || \
  pip install -q -r "${CLAUDE_PLUGIN_ROOT}/skills/weekly-report/scripts/requirements.txt"

[ -n "$FRED_API_KEY" ] || echo "WARNING: FRED_API_KEY not set — Money Market / Fixed Income US / FX will become Data Gaps"
```

### Step 1: Validate scope and compute derived fields

Default `end_date` to `date +%Y-%m-%d`. Default `start_date` to `end_date - 6 days`. Read `references/language-spec.md` for the H1 title template and filename pattern. Compute:

- `out_dir` (with `~` and `{end_date}` substitutions)
- `out_md` and `out_docx` per `lang`

Print a confirmation block:

```
📊 Weekly Report: {start_date} → {end_date}
🌍 Countries: {countries}
🌐 Language: {lang}
📁 Output: {out_md}
📰 News source: {news_dir}
📧 Email: {email or "(skipped)"}{dry-run hint}
```

### Step 2: Run Stages A and B in parallel

**CRITICAL — issue both Task calls in a single assistant message** so the platform runs them in parallel. Sequential dispatch wastes wall time and cache.

- **Task → `weekly-news-aggregator`** with prompt containing `start_date`, `end_date`, `lang`, `countries`, `news_dir`. Capture the returned `WeeklyEventsBundle` JSON.
- **Task → `market-data-collector`** with prompt containing `start_date`, `end_date`, `lang`, `kr_bond_symbol`, `commodity_symbols`, `boe_tenors`, `boj_tenors`. Capture the returned `MarketDataBundle` JSON.

If either bundle is empty/error, do NOT abort — pass an empty bundle through and let Stage C surface gaps.

### Step 3: Stage C — Writer

Launch the **`weekly-report-writer`** agent in a single Task call. Prompt must include:

1. Full `WeeklyEventsBundle` JSON verbatim (do not summarise).
2. Full `MarketDataBundle` JSON verbatim.
3. Runtime parameters: `start_date`, `end_date`, `lang`, `out_md`.

The writer reads `references/language-spec.md`, `references/output-spec.md`, `references/verification.md`, then issues exactly one `Write` call to `out_md`.

The PostToolUse `weekly-report-format-check.js` hook validates the result. On failure, the writer must re-issue the `Write` (not Edit).

### Step 4: pandoc export

```bash
mkdir -p "$(dirname "{out_md}")"
if command -v pandoc >/dev/null 2>&1; then
  pandoc --extract-media=./media "{out_md}" -o "{out_docx}"
else
  echo "pandoc not found — skipping docx export"
fi
```

### Step 5: Email (only if `--email` non-empty)

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/send-report-email.py" \
  --to "{email}" \
  --subject "{email_subject_or_default}" \
  --body-file /tmp/weekly-report-email-body.txt \
  --attach "{out_md}" "{out_docx}" \
  ${email_dry_run:+--dry-run}
```

The `email-send-guard.js` PreToolUse hook permits this Bash invocation; do NOT call smtplib inline.

### Step 6: Verify and report

```bash
ls -la "{out_md}" "{out_docx}" 2>/dev/null
grep -c '^## ' "{out_md}"   # expect 6 (or 7 if Data Gaps emitted)
grep -E '^# .*'"$start_date"'.*'"$end_date" "{out_md}" || echo "WARN: H1 missing date range"
```

Print a final summary listing the file paths, the count of Market event countries, and any Data Gaps the writer surfaced.

## Examples

```
/weekly-report
/weekly-report --end-date 2026-04-26 --lang zh
/weekly-report --end-date 2026-04-26 --countries "CN,US,UK,EU,JP,KR" --lang en
/weekly-report --end-date 2026-04-26 --lang ja --email "you@gmail.com" --email-dry-run
/weekly-report --start-date 2026-04-14 --end-date 2026-04-20 --commodity-symbols "GC=F,SI=F,CL=F,BZ=F"
```

## Related References

- `references/language-spec.md` — H1/H2/H3 strings per language
- `references/output-spec.md` — exact Markdown structure + table columns
- `references/tool-mapping.md` — which script feeds which section
- `references/schemas.md` — JSON I/O for every script
- `references/verification.md` — Writer self-check
