---
description: Generate a dated single-country daily news briefing in the target language. Usage: /daily-news-intelligence --country "<name>" [--date YYYY-MM-DD] [--lang zh|en|ja] [--out-dir <path>] [--min-per-category <N>]
---

# Daily News Intelligence (Single Country)

Produce a dated daily news briefing for one country in the target language, using English WebSearch with per-URL WebFetch date verification, five fixed categories, and APA 7th references. Scanner always operates in English; the final report is translated into `lang` at the Writer stage.

## Parameter Parsing

Parse the user input into the following parameters:

1. `--country` (required): Single country or region. Accepts input in any language (e.g. `"Japan"`, `"日本"`, `"United Kingdom"`, `"中国"`, `"Germany"`).
2. `--date` (optional, default: today): Target publication date in ISO `YYYY-MM-DD` format. Used for both the WebFetch date gate and the report filename.
3. `--lang` (optional, default: `zh`): Output language for the final report. Supported values: `zh` (Simplified Chinese), `en` (English), `ja` (Japanese). Scanner always operates in English regardless of this setting.
4. `--out-dir` (optional, default: `/Users/peterwang/Desktop/deep-research/`): Absolute output directory with trailing slash.
5. `--min-per-category` (optional, default: `2`): Minimum stories per fixed category.

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

Proceed? (Y/n)
```

### Step 2: Delegate to Skill

Invoke the `daily-news-intelligence` skill and pass through all parsed arguments, including `lang`. The skill owns the two-stage Scanner → Writer pipeline and the `pandoc` export step.

The skill will:

1. Run the Scanner stage in English — generate 20-30 candidates across five fixed categories, verify each via WebFetch against `date`, filter to T1-T4 tiers. Scanner output is always English raw data, regardless of `lang`.
2. Run the Writer stage — consume the full Scanner bundle without re-summarising, translate the narrative into `lang`, and emit Markdown obeying the skill's Markdown Syntax Contract. APA 7th references stay in English.
3. Write the Markdown to `out_md`.
4. Export via `pandoc --extract-media=./media "{out_md}" -o "{out_docx}"`.

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
/daily-news-intelligence --country "France" --date 2026-04-14 --lang en --out-dir "/Users/peterwang/Desktop/reports/"
```

## Related Skills

- `skills/daily-news-intelligence/SKILL.md` — canonical skill definition (Scanner + Writer rules, Localisation Table, Markdown Syntax Contract, tier rules, date verification rules).
- `skills/news-scan/SKILL.md` — multi-topic, multi-entity news scan over 7-90 day windows (different use case; not a single-country daily).
