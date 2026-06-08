---
description: Generate a dated single-country daily news briefing in the target language, with optional Gmail SMTP email delivery. Supports bilingual mode (1.18.0+) via --lang zh+en. Usage: /daily-news-intelligence --country "<name>" [--date YYYY-MM-DD] [--lang zh|en|ja|zh+en|en+zh|zh+ja|ja+zh|en+ja|ja+en] [--out-dir <path>] [--min-per-category <N>] [--email <a@x.com,b@y.com>] [--email-subject <text>] [--email-body <text>] [--email-attach both|docx|md|none] [--email-dry-run]
---

# Daily News Intelligence (Single Country)

Produce a dated daily news briefing for one country in the target language, using English WebSearch with per-URL WebFetch date verification, a country-derived active category set (6 categories for most countries; 7 for a China report), and APA 7th references. Scanner always operates in English; the final report is translated into `lang` at the Writer stage.

## Parameter Parsing

Parse the user input into the following parameters:

1. `--country` (required): Single country or region. Accepts input in any language (e.g. `"Japan"`, `"日本"`, `"United Kingdom"`, `"中国"`, `"Germany"`).
2. `--date` (optional, default: today): Target publication date in ISO `YYYY-MM-DD` format. Used for both the WebFetch date gate and the report filename.
3. `--lang` (optional, default: `zh`): Output language for the final report.
   - **Single-language**: `zh` (Simplified Chinese), `en` (English), `ja` (Japanese).
   - **Bilingual (1.18.0+)**: any two of `zh / en / ja` joined by `+` — `zh+en`, `en+zh`, `zh+ja`, `ja+zh`, `en+ja`, `ja+en`. The first token is the **primary language** (drives email subject + body lead section). 3-language combos are not supported in 1.18.0.
   - Scanner always operates in English regardless of this setting (output is language-agnostic, reused across bilingual halves).
4. `--out-dir` (optional, default: `~/Desktop/github/daily-news-reports/{date}/`): Output directory. `{date}` is replaced with the ISO date (e.g. `2026-04-16`). `~` is expanded at runtime. The directory is auto-created if it doesn't exist. Default writes directly into the GitHub Pages publishing repo.
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

Invoke the `daily-news-intelligence` skill and pass through all parsed arguments, including `lang`. The skill owns the multi-stage pipeline — single Scanner → Verifier → Fact-Extractor → Writer (× langs) → Editor (× langs) — and the `pandoc` export step.

The skill will:

1. Run the Scanner stage in English as a **single agent processing all active categories sequentially** (6 for a non-China report, 7 for a China report). It runs Pass A (Source Matrix tier ladder) + Pass B (free discovery under the Source Legitimacy rubric) per category, verifies each URL via WebFetch against `date`, then in § Step 6 performs cross-category dedup + the `china_nexus`↔`ipo_ma` routing tie-break, emitting one unified Scanner Bundle.
2. Run the Verifier stage — originality, authority, impact, source legitimacy, and dedup-validation on the Scanner Bundle.
3. Run the Fact-Extractor stage — extract every number / name / date / quote into a YAML Fact Manifest.
4. **For each language in `langs = lang.split('+')`** (single-lang: 1 iteration; bilingual: 2 iterations): run Writer + Editor for that lang. Writer consumes the shared Verifier KEEP set + shared Fact Manifest, translates the narrative into that lang, and emits Markdown to `out_md_{lang}` obeying the skill's Markdown Syntax Contract. APA 7th references stay in English.
5. Export via `pandoc --extract-media=./media "{out_md_{lang}}" -o "{out_docx_{lang}}"` per lang.
6. (Only if `--email` is non-empty) Send the report via Gmail SMTP per `skills/daily-news-intelligence/references/email-spec.md`. Single-lang: 1-2 attachments + single-lang body. **Bilingual: 2-4 attachments + stacked bilingual body** (primary lang first, divider, secondary lang).

### Step 3: Deliver

- Run `ls -la "{out_md}" "{out_docx}"` to confirm both files exist.
- Print file paths and per-category story counts.
- If the skill recorded category coverage gaps, surface them explicitly.

## Fixed Categories

The skill enforces a **country-derived active category set** as H2 sections in fixed order — **6 categories for a non-China report, 7 for a China report**. The actual H2 text (number + name) is language-dependent and composed per `references/language-spec.md` § Category Catalog & Selection (authoritative for identity, naming, order, numbering). Selection rule: `[econ, politics, tech, society]` ++ (`country == China` ? `[china_nexus]` : `[]`) ++ `[ipo_ma, other]`.

Category semantics:

1. Economy & Markets — macro data, central banks, equities, earnings, trade.
2. Politics & Diplomacy — government, legislation, elections, foreign policy, geopolitics.
3. Technology & Industry — AI, semiconductors, clean energy, platform economy, biotech.
4. Society & Livelihood — education, healthcare, employment, housing, immigration, labour.
5. China-Nexus Finance & Investment — **China report only**. China's cross-border economic/financial activity with a foreign party: inbound/outbound investment & FDI, commercial & industrial policy, tariffs, export controls, sanctions, trade measures, investment-screening, M&A/deals. **Economic channel only — pure diplomacy (summits, joint statements, foreign-ministry rhetoric with no economic transaction) is NOT here; it belongs to category 2 Politics & Diplomacy.** Excludes Chinese aid / infra-loans to Africa & small developing economies unless the deal is itself a China key-industry play; prioritises key industries (semiconductors, AI, EV & batteries, rare earths, biotech, aerospace, clean energy, telecom, advanced manufacturing). Region-unbounded.
6. Corporate IPO & M&A — **every report**. IPOs and M&A where a company of the report's country is a principal (listing entity / acquirer / target). Materiality floor: IPO ≥ USD 300M, M&A ≥ USD 500M, or any deal under security/antitrust review or touching a China key industry.
7. Other Notable Events — environment, sports, culture, judiciary, accidents.

The catch-all *Other* is always last; *China-Nexus* (when present) sits at position 5, so *Corporate IPO & M&A* is position 5 in a non-China report but position 6 in a China report, and *Other* is position 6 / 7 respectively. See `references/rubric.md` § Conditional & Topical Categories for the full eligibility and routing rules.

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

### Example 9: Bilingual zh+en (1.18.0+) — Chinese primary

```
/daily-news-intelligence --country "China" --lang zh+en --email "boss@company.com"
```

Email subject: `中国每日热点新闻 — 2026年4月14日（中英双语）`. Attachments: 4 files (zh.md + zh.docx + en.md + en.docx). Body: Chinese summary first, divider, English summary.

### Example 10: Bilingual en+zh — English primary, docx-only attachments

```
/daily-news-intelligence --country "Japan" --lang en+zh --email "team@company.com" --email-attach docx
```

Email subject: `Japan Daily News Intelligence — April 14, 2026 (Bilingual EN+ZH)`. Attachments: 2 files (en.docx + zh.docx). Body: English summary first, divider, Chinese summary.

## Related Skills

- `skills/daily-news-intelligence/SKILL.md` — canonical skill definition (Scanner + Writer rules, Localisation Table, Markdown Syntax Contract, tier rules, date verification rules).
- `skills/news-scan/SKILL.md` — multi-topic, multi-entity news scan over 7-90 day windows (different use case; not a single-country daily).

## Agent Reference (for debugging / inspection)

The skill dispatches five stages, each as `general-purpose` + embedded `agents/<name>.md` body (see SKILL.md § Subagent Dispatch Rule):

| Stage | Agent file | Model |
|-------|------------|-------|
| Scanner (single agent, all active categories sequentially; § Step 6 cross-category dedup + Cat5↔Cat6 routing) | `skills/daily-news-intelligence/agents/daily-news-scanner.md` | sonnet |
| Verifier | `skills/daily-news-intelligence/agents/news-verifier.md` | sonnet |
| Fact-Extractor | `skills/daily-news-intelligence/agents/daily-fact-extractor.md` | sonnet |
| Writer (**× len(langs)** in bilingual mode) | `skills/daily-news-intelligence/agents/daily-news-writer.md` | opus |
| Editor (**× len(langs)** in bilingual mode) | `skills/daily-news-intelligence/agents/daily-editor.md` | opus |

Reference contracts live in `skills/daily-news-intelligence/references/` — `rubric.md` (source tiers + Three-Step Fallback + Conditional Categories), `schemas.md` (Scanner Bundle + Verifier output formats), `language-spec.md` (Category Catalog + Localisation Table), `output-spec.md` (Markdown Syntax Contract + APA references), `verification.md` (self-check + flow diagram), `email-spec.md` (email subject/body templates + exit-code handling).
