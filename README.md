# sci-research

> A Claude Code plugin with **six independent multi-agent pipelines** for research, news intelligence, branded briefings, reputation monitoring, and weekly macro & market reports.

Given a topic, a country, a company, or a date, this plugin orchestrates specialised agents to produce a polished, sourced deliverable — academic article, news briefing, branded Word document, reputational risk email, or weekly research report.

---

## Six Pipelines

| | `/sci-research` | `/news-scan` | `/daily-news-intelligence` | `/daily-briefing` | `/reputation-track` | `/weekly-report` |
|---|---|---|---|---|---|---|
| **Purpose** | Multi-entity comparison research article | Real-time news briefing | Single-country daily news briefing | Multi-country branded briefing (SPD Bank) | Company reputation risk monitor | Weekly macro & market report |
| **Time focus** | Historical + current | Last 7/30/90 days | Single date | Single date (reads existing reports) | Single date | Trailing 7 days |
| **Sources** | Academic, official, T1 media | Wires, financial, industry press | T1-T4 graded (per-URL date verification) | Country reports from Pipeline C | News (T1-T4) + Reddit + X | Pipeline C reports + FRED/BOE/BOJ/yfinance |
| **Output** | ≤5000-word article with APA refs | 1000-3000-word briefing + images | Five-section Markdown + docx (+email) | 13-15-story branded Word document (+email) | Inline HTML email (only when negative) | Multi-section Markdown + docx (+email) |
| **Default lang** | `zh` | `zh` | `zh` | `zh` | `zh` | `zh` |
| **Languages** | zh / en / ja | zh / en / ja | zh / en / ja | zh / en | zh / en | zh / en / ja |

All six pipelines are **completely independent** — they don't share agents and changes to one don't affect the others.

---

## Why This Plugin

- **18 specialised agents** across six pipelines, each agent narrowly scoped
- **Parallel retrieval** — one researcher / scanner per entity, running simultaneously
- **Credibility-first** — three independent grading systems (academic five-star, news five-star, T1-T4 date-verified)
- **Per-URL date verification** in `/daily-news-intelligence` and `/weekly-report` — neighbouring days are discarded
- **Editorial second-pass filter** (`news-verifier`) for daily news — originality / authority / impact / dedup
- **External-view China matrix** — `/daily-news-intelligence --country "China"` uses only Western media + international organisations + external governments by structural design (no Chinese-domestic outlets, no Chinese government domains)
- **Free-prose Writer** (1.9.0+) — daily news Writer composes explanatory prose in the target language, not a mechanical translation
- **Branded Word output** via SPD Bank template (`/daily-briefing`)
- **Gmail SMTP email delivery** built into three pipelines (daily-news-intelligence, daily-briefing, reputation-track, weekly-report)
- **8 quality hooks** enforce word limits, entity coverage, reference integrity, news freshness, daily-news Markdown format, weekly-report format, and email-send safety
- **Multilingual** — Chinese / English / Japanese output

---

## Installation

### Option 1: From GitHub Marketplace

```bash
# In Claude Code, add this repo as a marketplace
/plugin marketplace add haiou312/sci-research

# Install the plugin
/plugin install sci-research@haiou312-sci-research
```

### Option 2: Local Development

```bash
git clone https://github.com/haiou312/sci-research.git
claude --plugin-dir /path/to/sci-research
```

After modifying plugin files, reload without restarting:
```
/reload-plugins
```

### Verify Installation

```
/plugin
```
You should see `sci-research` listed with its version.

### Email Delivery (optional)

For pipelines C / D / E / F that support `--email`, configure Gmail SMTP via `.env`:

```bash
cp .env.example .env
# Edit .env with your Gmail address + app password
```

See `.env.example` for the required variables.

---

## Usage

### Pipeline A — `/sci-research` (Deep Research Article)

```
/sci-research <topic> --entities "Entity1,Entity2,..." --lang zh|en|ja
```

```bash
# Compare nuclear fusion progress across 4 countries
/sci-research 核聚变能源最新进展 --entities "中国,美国,EU,日本"

# mRNA vaccine landscape in English
/sci-research mRNA vaccine technology landscape --entities "US,EU,China" --lang en
```

### Pipeline B — `/news-scan` (Real-Time News Briefing)

```
/news-scan <topic> --entities "Entity1,Entity2,..." --period 7d|30d|90d --lang zh|en|ja
```

```bash
# Recent Open Banking news, UK and China focus, 7 days
/news-scan 开放银行最新进展 --entities "中国,英国" --period 7d --lang zh

# Broad scan without entity filter
/news-scan AI regulation --period 90d --lang en
```

### Pipeline C — `/daily-news-intelligence` (Single-Country Daily Briefing)

```
/daily-news-intelligence --country "<name>" [--date YYYY-MM-DD] [--lang zh|en|ja] \
  [--out-dir <path>] [--min-per-category <N>] \
  [--email <a@x.com,b@y.com>] [--email-attach both|docx|md|none] [--email-dry-run]
```

```bash
# Today's UK briefing in Chinese, dry-run the email
/daily-news-intelligence --country "United Kingdom" --email you@gmail.com --email-dry-run

# China briefing — external-view by design (Western media + international orgs + external govs only)
/daily-news-intelligence --country "China" --date 2026-05-11 --lang zh

# Japanese briefing for Japan, English output
/daily-news-intelligence --country "Japan" --lang en
```

**Note on `--country "China"`**: Pipeline C scans China from an outside-observer perspective. Chinese-domestic outlets (Xinhua, People's Daily, Caixin, China Daily, SCMP, TechNode, etc.) and Chinese government domains (`gov.cn`, `pbc.gov.cn`, `stats.gov.cn`, …) are **not queried**. Source pool is Reuters / AP / AFP / Bloomberg / DJ Newswires (T1-wire); FT / WSJ / NYT / WaPo / Guardian / BBC / Telegraph / Times / Economist / Le Monde / Spiegel / FAZ / El País / Nikkei Asia (T1-flagship); NHK World / ABC Australia / Straits Times / Korea Herald / The Hindu (T2 regional); IMF / World Bank / WTO / OECD / BIS / IEA / US Treasury / USTR / State Dept / Commerce-BIS / White House / EU Commission / UK Gov / METI / MOFA Japan (T4 external institutions).

### Pipeline D — `/daily-briefing` (Multi-Country Branded Word Document)

```
/daily-briefing [--date YYYY-MM-DD] [--countries "中国,英国,美国,欧洲,日本,韩国"] [--total 14] \
  [--source-dir <path>] [--email <a@x.com>] [--email-subject <text>] [--email-dry-run] [--no-wait]
```

Reads existing Pipeline C reports from a directory, curates the most impactful 13-15 stories across countries, and emits a branded Word document via the SPD Bank template.

```bash
# Today's multi-country briefing with default countries and 14 stories
/daily-briefing --email you@gmail.com

# Specific date with custom country selection
/daily-briefing --date 2026-05-11 --countries "中国,日本,韩国" --total 12
```

### Pipeline E — `/reputation-track` (Company Reputation Risk Monitor)

```
/reputation-track --company "<name|ticker>" [--date YYYY-MM-DD] [--lang zh|en] \
  [--sources news,reddit,x] [--severity-min low|medium|high] \
  [--email <a@x.com>] [--email-dry-run]
```

Resolves the company + executives, scans News + Reddit + X for adverse content, classifies category and severity. **Silent when clean** — only emails a report if negative findings exist.

```bash
# Scan Tesla for today's negative coverage
/reputation-track --company "TSLA" --email you@gmail.com

# Scan Alibaba for a specific date, low-severity threshold
/reputation-track --company "BABA" --date 2026-05-10 --severity-min low --lang en
```

### Pipeline F — `/weekly-report` (Weekly Macro & Market Report)

```
/weekly-report [--end-date YYYY-MM-DD] [--start-date YYYY-MM-DD] \
  [--countries "CN,US,UK,EU,JP,KR"] [--lang zh|en|ja] [--out-dir <path>] \
  [--news-dir <path>] [--commodity-symbols "GC=F,SI=F,CL=F"] \
  [--kr-bond-symbol 148070.KS] \
  [--email <a@x.com,b@y.com>] [--email-attach both|docx|md|none] [--email-dry-run]
```

Aggregates the previous 7 days of `/daily-news-intelligence` reports for the Market Event section, then pulls live market data (FRED for money market & FX, BoE + BoJ + FRED for fixed income, yfinance for KR ETF proxy and commodities) for the data sections.

```bash
# Weekly report ending today
/weekly-report --email you@gmail.com

# Specific date range and country set
/weekly-report --end-date 2026-05-11 --start-date 2026-05-05 --countries "CN,US,JP" --lang en
```

### Utility Commands

```bash
# Add more entities to an active research session (Pipeline A & B)
/add-entity "韩国,印度"

# Switch output language mid-session
/set-lang en
```

---

## How It Works

### Pipeline A — `/sci-research`

```
User Input (topic, entities, lang)
  │
  ├─→ Researcher(A) ─┐
  ├─→ Researcher(B) ─┼─→ Comparator → Fact-Checker → Writer → Hooks → Article
  └─→ Researcher(C) ─┘    (opus)        (sonnet)      (opus)
       (sonnet, parallel)
```

| Agent | Model | Role |
|---|---|---|
| `researcher` | sonnet | One instance per entity, multi-source retrieval |
| `comparator` | opus | Cross-entity dimension selection + root-cause analysis |
| `fact-checker` | sonnet | Claim verification with confidence labels |
| `writer` | opus | Multilingual article synthesis with APA references |

### Pipeline B — `/news-scan`

```
News-Scanner(×N) → news-imager → news-analyst → Hooks → Briefing
   (parallel)      (sonnet)        (opus)
```

| Agent | Model | Role |
|---|---|---|
| `news-scanner` | sonnet | One per entity, real-time news retrieval (no image extraction) |
| `news-imager` | sonnet | Image extraction and relevance verification for top events |
| `news-analyst` | opus | Dedup, timeline, impact matrix, trend signals |

### Pipeline C — `/daily-news-intelligence`

```
daily-news-scanner → news-verifier → daily-news-writer → pandoc → email (optional) → publish (optional)
   (sonnet)            (sonnet)         (opus)
```

| Agent | Model | Role |
|---|---|---|
| `daily-news-scanner` | sonnet | English WebSearch + per-URL date verification (T4 → T1 → T2 → T3). Paywall fallback (Step 3.5) reroutes Hard-paywall hits as Corroborated, finds free Lead. |
| `news-verifier` | sonnet | Editorial second-pass filter: originality / authority / impact / dedup |
| `daily-news-writer` | opus | Consumes Verifier KEEP set, composes explanatory prose in target language, emits Markdown + APA refs |

### Pipeline D — `/daily-briefing`

```
daily-news-reports/YYYY-MM-DD/*.md  (existing country reports)
  │
  └─→ briefing-curator → generate-branded-docx.py → send-briefing-email.py
      (opus)              (python-docx)              (Gmail SMTP)
```

### Pipeline E — `/reputation-track`

```
reputation-resolver → reputation-scanner × 3 (parallel: news / reddit / x) → reputation-classifier → reputation-writer → email (only if findings)
   (opus)              (sonnet)                                                (sonnet)                 (opus)
```

Silent exit when `total_items_kept == 0`. Reddit and X go through the apidirect MCP (single call per source) to avoid public-endpoint scraping blocks.

### Pipeline F — `/weekly-report`

```
weekly-news-aggregator (Stage A) ─┐
market-data-collector (Stage B) ──┼─→ weekly-report-writer → pandoc → email (optional)
                                   ┘
```

| Agent | Model | Role |
|---|---|---|
| `weekly-news-aggregator` | sonnet | Reads previous 7 days of Pipeline C reports, deduplicates, groups by country |
| `market-data-collector` | sonnet | Runs FRED / BoE / BoJ / yfinance scripts in parallel, aggregates JSON |
| `weekly-report-writer` | opus | Localises section headings per language-spec, composes Markdown |

---

## Source Credibility Systems

### Pipeline A (Academic + Official)

| Grade | Source Type | Examples |
|---|---|---|
| ★★★★★ | Peer-reviewed journals | Nature, Science, The Lancet |
| ★★★★★ | International org reports | WHO, OECD, IPCC, World Bank |
| ★★★★☆ | Government reports | DOE, EU Commission, 国务院白皮书 |
| ★★★★☆ | Wire services | Reuters, AP, AFP, Xinhua |
| ★★★☆☆ | Quality journalism | Scientific American, BBC Science |
| ★★☆☆☆ | Preprints | arXiv, medRxiv (flagged as non-peer-reviewed) |

### Pipeline B (News & Media)

| Grade | Source Type | Examples |
|---|---|---|
| ★★★★★ | Wire services | Reuters, AP, AFP, Xinhua |
| ★★★★☆ | Financial / business media | FT, Bloomberg, CNBC, Caixin, BBC |
| ★★★☆☆ | Industry vertical media | Finextra, TechCrunch, 36氪 |
| ★★☆☆☆ | Think-tank commentary | Brookings, PIIE, VoxEU |
| ★☆☆☆☆ | Social media / blogs | Avoided unless verified expert |

### Pipeline C (T1-T4 Date-Verified)

| Tier | Source Type | Examples |
|---|---|---|
| T1-wire | International wires (Universal) | Reuters, AP, AFP, Bloomberg, DJ Newswires |
| T1-flagship | Global prestige newspapers | FT, WSJ, Economist, NYT, WaPo, Guardian, BBC, Telegraph, Times, Le Monde, Spiegel, FAZ, El País, Nikkei Asia |
| T2 | Regional flagships | NHK World, ABC Australia, Straits Times, Korea Herald, The Hindu, CNBC, Politico Europe, DW, Al Jazeera |
| T3 | Sector verticals | TechCrunch, MIT Tech Review, Finextra, S&P Global, STAT, MLex |
| T4-official | Primary institutional releases | Fed, ECB, BoE, BoJ, Treasury, USTR, State Dept, EU Commission, IMF, World Bank, WTO, OECD, BIS, IEA |

**For `country = China`**: T1-wire is Universal only (no Xinhua / China News Service); T1-flagship Country-of-coverage is empty (no Caixin / People's Daily / SCMP); T3 has no Country: China rows; T4 uses an external-institution table (IMF, World Bank, WTO, OECD, BIS, IEA, US Treasury, USTR, State Dept, US Commerce/BIS, White House, EU Commission, UK Gov, METI, MOFA Japan). Chinese government domains are never queried.

Detailed rules:
- Pipeline A: [`rules/research/source-credibility.md`](./rules/research/source-credibility.md)
- Pipeline B: [`rules/research/news-source.md`](./rules/research/news-source.md)
- Pipeline C: [`skills/daily-news-intelligence/references/rubric.md`](./skills/daily-news-intelligence/references/rubric.md) + [`skills/daily-news-intelligence/agents/daily-news-scanner.md`](./skills/daily-news-intelligence/agents/daily-news-scanner.md) § Source Matrix

---

## Quality Hooks

| Hook | Pipeline | Trigger | What It Does |
|---|---|---|---|
| `word-count-check` | A | PostToolUse:Write | Blocks if Pipeline A article >5000 words / 7500 CJK chars |
| `entity-coverage-check` | A | PostToolUse:Write | Warns if any entity lacks dedicated section / ≥3 mentions |
| `reference-validator` | A | PostToolUse:Write | Warns if inline `[N]` doesn't match references list |
| `news-freshness-check` | B | PostToolUse:Write | Warns if no Pipeline B source from last 7 days |
| `daily-news-format-check` | C | PostToolUse:Write | **Blocks** Pipeline C Markdown if format violates spec (count invariants, `[N]` continuity, URLs, no global refs section) |
| `weekly-report-format-check` | F | PostToolUse:Write | **Blocks** Pipeline F Markdown if format violates spec |
| `email-send-guard` | C / D / E / F | PreToolUse:Bash | **Blocks** inline `smtplib` / `MIMEMultipart` / `sendmail` Bash commands that bypass the sanctioned `send-*-email.py` scripts |
| `research-summary` | A & B | Stop | Logs session metadata (async, non-blocking) |

---

## Project Structure

```
sci-research/
├── .claude-plugin/
│   ├── plugin.json                          # Plugin metadata
│   └── marketplace.json                     # Marketplace manifest
├── commands/                                # 6 main + 2 utility slash commands
│   ├── sci-research.md
│   ├── news-scan.md
│   ├── daily-news-intelligence.md
│   ├── daily-briefing.md
│   ├── reputation-track.md
│   ├── weekly-report.md
│   ├── add-entity.md
│   └── set-lang.md
├── skills/                                  # 6 independent skill workflows; agents/*.md live under each skill as prompt templates (NOT registered as `sci-research:*` subagents — see CLAUDE.md § 项目定位 point 6)
│   ├── sci-research/                        # Pipeline A
│   │   ├── SKILL.md
│   │   └── agents/
│   │       ├── researcher.md                # Per-entity retrieval
│   │       ├── comparator.md                # Cross-entity dimensions
│   │       ├── fact-checker.md              # Claim verification
│   │       └── writer.md                    # Article writer
│   ├── news-scan/                           # Pipeline B
│   │   ├── SKILL.md
│   │   └── agents/
│   │       ├── news-scanner.md              # Per-entity news (no images)
│   │       ├── news-imager.md               # Image extraction + verify
│   │       └── news-analyst.md              # Dedup + timeline + impact
│   ├── daily-news-intelligence/             # Pipeline C
│   │   ├── SKILL.md
│   │   ├── agents/
│   │   │   ├── daily-news-scanner.md        # Single-date scan + date gate + cross-category dedup + Cat5↔Cat6 routing
│   │   │   ├── news-verifier.md             # Editorial second-pass filter
│   │   │   ├── daily-fact-extractor.md      # Verifier KEEP → YAML fact manifest
│   │   │   ├── daily-news-writer.md         # Free-prose target-language writer
│   │   │   └── daily-editor.md              # 5-pass post-Writer editor
│   │   └── references/                      # Pipeline C specs
│   │       ├── email-spec.md
│   │       ├── language-spec.md
│   │       ├── output-spec.md
│   │       ├── rubric.md
│   │       ├── schemas.md
│   │       └── verification.md
│   ├── daily-briefing/                      # Pipeline D
│   │   ├── SKILL.md
│   │   ├── agents/
│   │   │   └── briefing-curator.md          # Multi-country curator
│   │   ├── template/briefing-template.docx  # SPD Bank brand template
│   │   ├── references/email-spec.md
│   │   └── scripts/
│   │       ├── generate-branded-docx.py
│   │       └── send-briefing-email.py
│   ├── reputation-track/                    # Pipeline E
│   │   ├── SKILL.md
│   │   ├── agents/
│   │   │   ├── reputation-resolver.md       # Ticker/name → exec list
│   │   │   ├── reputation-scanner.md        # Per-source (news/reddit/x)
│   │   │   ├── reputation-classifier.md     # Per-item negativity grader
│   │   │   └── reputation-writer.md         # HTML email body composer
│   │   └── references/                      # Pipeline E specs
│   │       ├── entity-resolution.md
│   │       ├── source-matrix.md
│   │       ├── negativity-rubric.md
│   │       ├── html-template.md
│   │       ├── email-spec.md
│   │       └── schemas.md
│   └── weekly-report/                       # Pipeline F
│       ├── SKILL.md
│       └── agents/
│           ├── weekly-news-aggregator.md    # 7-day event aggregator
│           ├── market-data-collector.md     # FRED/BoE/BoJ/yfinance
│           └── weekly-report-writer.md      # Weekly report writer
├── contexts/sci-research.md                 # Research mode behavioral context
├── hooks/hooks.json                         # Hook configuration (8 hooks)
├── scripts/
│   ├── hooks/                               # Hook implementations (Node.js)
│   │   ├── word-count-check.js
│   │   ├── entity-coverage-check.js
│   │   ├── reference-validator.js
│   │   ├── news-freshness-check.js
│   │   ├── daily-news-format-check.js
│   │   ├── weekly-report-format-check.js
│   │   ├── email-send-guard.js
│   │   └── research-summary.js
│   └── send-report-email.py                 # Gmail SMTP (Pipelines C / E / F)
├── rules/research/                          # 3 quality rules
│   ├── source-credibility.md                # Pipeline A grading
│   ├── output-format.md                     # Pipeline A format
│   └── news-source.md                       # Pipeline B grading & dedup
├── examples/                                # Sample outputs
│   ├── nuclear-fusion-zh.md                 # Pipeline A (Chinese)
│   └── mrna-vaccine-en.md                   # Pipeline A (English)
├── .env.example                             # Gmail SMTP environment template
├── CLAUDE.md                                # Project guidance for Claude Code
├── README.md
└── LICENSE
```

---

## Customization

| Goal | Edit |
|---|---|
| Pipeline A word limit | `scripts/hooks/word-count-check.js` (`WORD_LIMIT`, `CHAR_LIMIT_ZH`) |
| Pipeline B news-freshness window | `scripts/hooks/news-freshness-check.js` (7-day constant) |
| Pipeline A comparison dimensions | `skills/sci-research/agents/comparator.md` § Dimension Selection |
| Pipeline A source grading | `rules/research/source-credibility.md` |
| Pipeline B news source rules | `rules/research/news-source.md` |
| Pipeline C source matrix / date verification | `skills/daily-news-intelligence/agents/daily-news-scanner.md` + `skills/daily-news-intelligence/references/rubric.md` |
| Pipeline C external-view China rules | `skills/daily-news-intelligence/agents/daily-news-scanner.md` § Source Matrix § T4-official + Step 2.1 |
| Pipeline C output format / Markdown contract | `skills/daily-news-intelligence/references/output-spec.md` |
| Pipeline C language localisation | `skills/daily-news-intelligence/references/language-spec.md` |
| Pipeline C email delivery | `skills/daily-news-intelligence/references/email-spec.md` + `scripts/send-report-email.py` |
| Pipeline D brand template | `skills/daily-briefing/template/briefing-template.docx` |
| Pipeline D curator rules | `skills/daily-briefing/agents/briefing-curator.md` |
| Pipeline E negativity rubric | `skills/reputation-track/references/negativity-rubric.md` |
| Pipeline E HTML email template | `skills/reputation-track/references/html-template.md` |
| Pipeline E entity resolution | `skills/reputation-track/references/entity-resolution.md` + `skills/reputation-track/agents/reputation-resolver.md` |
| Pipeline F market-data sources | `skills/weekly-report/agents/market-data-collector.md` |
| New output language | `skills/sci-research/agents/writer.md` + `skills/news-scan/agents/news-analyst.md` + `skills/daily-news-intelligence/agents/daily-news-writer.md` + `commands/set-lang.md` + `skills/daily-news-intelligence/references/language-spec.md` |
| Adding hook / changing email-send guard | `scripts/hooks/email-send-guard.js` + the relevant SKILL.md email step |

---

## Examples

See the [`examples/`](./examples/) directory for complete sample outputs:

- **[nuclear-fusion-zh.md](./examples/nuclear-fusion-zh.md)** — Nuclear fusion progress, China / US / EU / Japan comparison (Chinese)
- **[mrna-vaccine-en.md](./examples/mrna-vaccine-en.md)** — mRNA vaccine technology landscape, US / EU / China comparison (English)

---

## Requirements

- [Claude Code](https://claude.ai/code) CLI
- Node.js ≥ 18 (for hook scripts)
- Python 3 (for email delivery scripts; only required when `--email` is used)
- `pandoc` (for Markdown → docx conversion in Pipelines C / F)
- Internet access (for WebSearch / WebFetch)
- Gmail SMTP credentials (only for pipelines that support `--email`; see `.env.example`)

---

## Acknowledgements

Plugin structure inspired by [everything-claude-code](https://github.com/affaan-m/everything-claude-code) by Affaan Mustafa.

---

## License

MIT
