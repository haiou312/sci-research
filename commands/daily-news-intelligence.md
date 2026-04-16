---
description: Generate a dated single-country daily news briefing in the target language, with optional Gmail SMTP email delivery. Usage: /daily-news-intelligence --country "<name>" [--date YYYY-MM-DD] [--lang zh|en|ja] [--out-dir <path>] [--min-per-category <N>] [--email <a@x.com,b@y.com>] [--email-subject <text>] [--email-body <text>] [--email-attach both|docx|md|none] [--email-dry-run]
---

# Daily News Intelligence (Single Country)

Produce a dated daily news briefing for one country in the target language, using English WebSearch with per-URL WebFetch date verification, five fixed categories, and APA 7th references. Scanner always operates in English; the final report is translated into `lang` at the Writer stage.

## Parameter Parsing

Parse the user input into the following parameters:

1. `--country` (required): Single country or region. Accepts input in any language (e.g. `"Japan"`, `"日本"`, `"United Kingdom"`, `"中国"`, `"Germany"`).
2. `--date` (optional, default: today): Target publication date in ISO `YYYY-MM-DD` format. Used for both the WebFetch date gate and the report filename.
3. `--lang` (optional, default: `zh`): Output language for the final report. Supported values: `zh` (Simplified Chinese), `en` (English), `ja` (Japanese). Scanner always operates in English regardless of this setting.
4. `--out-dir` (optional, default: `~/Desktop/daily-news-reports/{date}/`): Output directory. `{date}` is replaced with the ISO date (e.g. `2026-04-16`). `~` is expanded at runtime. The directory is auto-created if it doesn't exist.
5. `--min-per-category` (optional, default: `2`): Minimum stories per fixed category.
6. `--email` (optional, default: empty): Comma-separated recipient email addresses. When non-empty, the report is sent via Gmail SMTP at the end of the pipeline. Requires `GOOGLE_EMAIL_USERNAME` and `GOOGLE_EMAIL_APP_PASSWORD` environment variables. See `.env.example` at the repo root.
7. `--email-subject` (optional, default: auto-generated): Email subject line. Default pattern is `{country_display} {title_label} — {date_display}` rendered in `lang`.
8. `--email-body` (optional, default: auto-generated): Email body text. Default template includes per-category coverage counts. See `skills/daily-news-intelligence/references/email-spec.md` for templates.
9. `--email-attach` (optional, default: `both`): Attachment selection. Accepts `both` (md + docx), `docx`, `md`, or `none`.
10. `--email-dry-run` (optional, default: `false`): When set, the email stage builds the message and prints a preview but does NOT connect to SMTP. Useful for testing.

Normalize the country name:

- `COUNTRY_EN` — English form used for all WebSearch queries and APA reference fields.
- `country_display` — country name rendered in the target language via the skill's Localisation Table.

Derive date display forms:

- `date_en` — English display form, e.g. `April 14, 2026`.
- `date_display` — date rendered in the target language (e.g. `2026年4月14日` for zh/ja, `April 14, 2026` for en).

Derive output paths (the skill's Localisation Table owns the exact filename pattern per `lang`):

- `out_md` — Markdown output path under `out_dir`.
- `out_docx` — Word output path with `.docx` extension.

## Execution Pipeline

### Step 1: Confirm Scope

Display a brief confirmation:

```
📰 Daily Briefing: {country_display} ({COUNTRY_EN})
📅 Date: {date} ({date_display})
🌐 Language: {lang}
📁 Output: {out_dir}
📊 Min per category: {min_per_category}
📧 Email: {email or "(skipped)"}{email_dry_run hint if set}

Proceed? (Y/n)
```

### Step 2: Delegate to Skill

Invoke the `daily-news-intelligence` skill and pass through all parsed arguments, including `lang`. The skill owns the two-stage Scanner → Writer pipeline and the `pandoc` export step.

The skill will:

1. Run the Scanner stage in English — generate 20-30 candidates across five fixed categories, verify each via WebFetch against `date`, filter to T1-T4 tiers.
2. Run the Verifier stage — apply originality, authority, impact, and dedup filters to the Scanner bundle.
3. Run the Writer stage — consume the Verifier's KEEP set only, translate the narrative into `lang`, and emit Markdown obeying the skill's Markdown Syntax Contract. APA 7th references stay in English.
4. Write the Markdown to `out_md`.
5. Export via `pandoc --extract-media=./media "{out_md}" -o "{out_docx}"`.
6. (Only if `--email` is non-empty) Send the report via Gmail SMTP per `skills/daily-news-intelligence/references/email-spec.md`.

### Step 3: Deliver

- Run `ls -la "{out_md}" "{out_docx}"` to confirm both files exist.
- Print file paths and per-category story counts.
- If the skill recorded category coverage gaps, surface them explicitly.

## Fixed Categories

The skill enforces five H2 sections in fixed order. The actual H2 text is language-dependent; see the `Localisation Table` in `skills/daily-news-intelligence/SKILL.md` for the exact strings per `lang`. Category semantics:

1. Economy & Markets — macro data, central banks, equities, earnings, trade.
2. Politics & Diplomacy — government, legislation, elections, foreign policy, geopolitics.
3. Technology & Industry — AI, semiconductors, clean energy, platform economy, biotech.
4. Society & Livelihood — education, healthcare, employment, housing, immigration, labour.
5. Other Notable Events — environment, sports, culture, judiciary, accidents.

## Examples

### Example 1: Chinese output (default `lang=zh`), Japan

```
/daily-news-intelligence --country "Japan" --date 2026-04-14
```

### Example 2: English output, United Kingdom

```
/daily-news-intelligence --country "United Kingdom" --date 2026-04-14 --lang en --min-per-category 3
```

### Example 3: Japanese output, Germany

```
/daily-news-intelligence --country "Germany" --date 2026-04-14 --lang ja
```

### Example 4: Default date and language

```
/daily-news-intelligence --country "China"
```

### Example 5: Custom output directory

```
/daily-news-intelligence --country "France" --date 2026-04-14 --lang en --out-dir "~/Documents/news-briefings/"
```

### Example 6: Email delivery to yourself

```
/daily-news-intelligence --country "China" --email "you@gmail.com"
```

### Example 7: Email multiple recipients, docx only

```
/daily-news-intelligence --country "Japan" --email "alice@foo.com,bob@bar.com" --email-attach docx
```

### Example 8: Dry-run email to inspect subject, body, and attachments without sending

```
/daily-news-intelligence --country "UK" --lang en --email "you@gmail.com" --email-dry-run
```

## Related Skills

- `skills/daily-news-intelligence/SKILL.md` — canonical skill definition (Scanner + Writer rules, Localisation Table, Markdown Syntax Contract, tier rules, date verification rules).
- `skills/news-scan/SKILL.md` — multi-topic, multi-entity news scan over 7-90 day windows (different use case; not a single-country daily).
