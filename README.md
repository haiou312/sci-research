# sci-research

> A **Codex plugin** with **three independent multi-agent pipelines** for daily news intelligence, branded briefings, and company reputation monitoring.

Given a country, a company, or a date, this plugin orchestrates specialised agents to produce a polished, sourced deliverable — daily news briefing, branded Word document, or reputational risk email.

*(The plugin name is a historical artifact — the original `/sci-research` deep-research pipeline has been removed; the name is kept for marketplace identity and install-path stability.)*

---

## Three Pipelines

| | `/daily-news-intelligence` | `/daily-briefing` | `/reputation-track` |
|---|---|---|---|
| **Purpose** | Single-country daily news briefing | Multi-country branded briefing (SPD Bank) | Company reputation risk monitor |
| **Time focus** | Single date | Single date (reads existing reports) | Single date |
| **Sources** | T1-T4 graded (per-URL date verification) | Country reports from Pipeline C | News (T1-T4) + Reddit + X |
| **Output** | 6/7-section Markdown + docx (+email); mono- or bilingual | 13-15-story branded Word document (+email) | Inline HTML email (only when negative) |
| **Default lang** | `zh` | `zh` | `zh` |
| **Languages** | zh / en / ja + 6 bilingual combos (`zh+en` …) | zh / en | zh / en |

All three pipelines are **completely independent** — they don't share agents and changes to one don't affect the others.

---

## Why This Plugin

- **10 specialised agents** across three pipelines, each agent narrowly scoped
- **Credibility-first** — T1-T4 date-verified source grading
- **Per-URL date verification** in `/daily-news-intelligence` — neighbouring days are discarded
- **Editorial second-pass filter** (`news-verifier`) for daily news — originality / authority / impact / source legitimacy / dedup
- **Fact Manifest + 5-pass Editor** — numbers / names / dates / quotes locked to a verbatim YAML manifest, then fact-checked and style-repaired post-Writer
- **External-view China matrix** — `/daily-news-intelligence --country "China"` uses only Western media + international organisations + external governments by structural design (no Chinese-domestic outlets, no Chinese government domains)
- **Free-prose Writer** — daily news Writer composes explanatory prose in the target language, not a mechanical translation
- **Bilingual mode (1.18.0+)** — `--lang zh+en` runs upstream once, fans Writer/Editor out per language in parallel, ships one email with a stacked bilingual body + up to 4 attachments
- **Branded Word output** via SPD Bank template (`/daily-briefing`)
- **Gmail SMTP email delivery** built into all three pipelines
- **Quality hooks** enforce daily-news Markdown format and email-send safety
- **Multilingual** — Chinese / English / Japanese output

---

## Installation

### Option 1: From a marketplace

```bash
# Add this repo as a Codex plugin marketplace, then install
codex plugin marketplace add haiou312/sci-research
codex plugin marketplace list
```

### Option 2: Local Development

```bash
git clone https://github.com/haiou312/sci-research.git
codex plugin marketplace add ./sci-research
```

Subagents live in `.codex/agents/*.toml`; skills in `skills/*/SKILL.md`; the manifest is `.codex-plugin/plugin.json`. See `PORTING-NOTES.md` for current runtime-validation status.

### Verify Installation

```
/plugin
```
You should see `sci-research` listed with its version.

### Email Delivery (optional)

For the `--email` option in any pipeline, configure Gmail SMTP via `.env`:

```bash
cp .env.example .env
# Edit .env with your Gmail address + app password
```

See `.env.example` for the required variables.

---

## Usage

### Pipeline C — `/daily-news-intelligence` (Single-Country Daily Briefing)

```
/daily-news-intelligence --country "<name>" [--date YYYY-MM-DD] \
  [--lang zh|en|ja|zh+en|en+zh|zh+ja|ja+zh|en+ja|ja+en] \
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

# Bilingual (1.18.0+) — Chinese primary, ships 4 attachments (zh+en md+docx) + stacked zh+en email body
/daily-news-intelligence --country "China" --lang zh+en --email boss@company.com
```

**Note on `--country "China"`**: Pipeline C scans China from an outside-observer perspective. Chinese-domestic outlets (Xinhua, People's Daily, Caixin, China Daily, SCMP, TechNode, etc.) and Chinese government domains (`gov.cn`, `pbc.gov.cn`, `stats.gov.cn`, …) are **not queried**. Source pool is Reuters / AP / AFP / Bloomberg / DJ Newswires (T1-wire); FT / WSJ / NYT / WaPo / Guardian / BBC / Telegraph / Times / Economist / Le Monde / Spiegel / FAZ / El País / Nikkei Asia (T1-flagship); NHK World / ABC Australia / Straits Times / Korea Herald / The Hindu (T2 regional); IMF / World Bank / WTO / OECD / BIS / IEA / US Treasury / USTR / State Dept / Commerce-BIS / White House / EU Commission / UK Gov / METI / MOFA Japan (T4 external institutions).

### Pipeline D — `/daily-briefing` (Multi-Country Branded Word Document)

```
/daily-briefing [--date YYYY-MM-DD] [--countries "中国,英国,美国,欧洲,日本,韩国"] [--total 14] \
  [--source-dir <path>] [--out-dir <path>] [--email <a@x.com>] [--email-subject <text>] \
  [--email-dry-run] [--no-wait]
```

Reads existing Pipeline C reports from a directory, curates the most impactful 13-15 stories across countries, and emits a branded Word document via the SPD Bank template.

By default, local output is independent of the plugin install location and any Git checkout:

| Pipeline | Default location |
|---|---|
| C daily news | `~/.sci-research/reports/daily-news/{date}/` |
| D source reports | `~/.sci-research/reports/daily-news/{date}/` |
| D branded briefing | `~/.sci-research/reports/daily-briefings/{date}/` |
| E reputation report | `~/.sci-research/reports/reputation/{date}/` |

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

---

## How It Works

### Pipeline C — `/daily-news-intelligence`

```
daily-news-scanner → news-verifier → daily-fact-extractor → daily-news-writer → daily-editor → pandoc → email (optional)
   (Luna / medium)      (Terra / high)  (5.4 mini / medium)    (Sol / high, ×langs) (Sol / high, ×langs)

Bilingual mode (--lang zh+en …): Scanner/Verifier/Fact-Extractor run ONCE; Writer ×langs in parallel → Editor ×langs in parallel → pandoc ×langs
```

| Agent | Codex configuration | Role |
|---|---|---|
| `daily-news-scanner` | gpt-5.6-luna / medium | Single agent scanning all active categories sequentially. English WebSearch + per-URL date verification (T4 → T1 → T2 → T3), Pass A matrix + Pass B free discovery, paywall fallback (Step 3.5), then internal cross-category dedup + Cat5↔Cat6 routing (§ Step 6) → unified Scanner Bundle |
| `news-verifier` | gpt-5.6-terra / high | Editorial second-pass filter: originality / authority / impact / source legitimacy / dedup-validation + Three-Step Coverage Fallback |
| `daily-fact-extractor` | gpt-5.4-mini / medium | Extracts every number / name / date / quote from the Verifier KEEP set into a locked-values YAML Fact Manifest (no web access) |
| `daily-news-writer` | gpt-5.6-sol / high | Consumes Verifier KEEP set + Fact Manifest, composes explanatory prose in target language with 1-3 background searches per story, emits Markdown + APA refs. One instance per language in bilingual mode |
| `daily-editor` | gpt-5.6-sol / high | 5-pass post-Writer editor: manifest-fact drift / search-fact backing / quote verbatim / quote-mark normalization / local fluency repair. `apply_patch`-only. One instance per language in bilingual mode |

### Pipeline D — `/daily-briefing`

```
daily-news-reports/YYYY-MM-DD/*.md  (existing country reports)
  │
  └─→ briefing-curator → generate-branded-docx.py → send-briefing-email.py
      (Sol / high)          (python-docx)              (Gmail SMTP)
```

`briefing-curator` uses gpt-5.6-sol / high.

### Pipeline E — `/reputation-track`

```
reputation-resolver → reputation-scanner × requested sources (parallel; default: news / reddit / x) → reputation-classifier → reputation-writer → email (only if findings)
   (Terra / high)      (Luna / medium)                                                              (Terra / high)          (Terra / medium)
```

Silent exit when `total_items_kept == 0`. Reddit and X use Codex WebSearch `search` to discover publicly indexed posts and `open_page` to inspect canonical threads. Unindexed, login-gated, or unopenable content is recorded as a coverage gap.

| Agent | Codex configuration |
|---|---|
| `reputation-resolver` | gpt-5.6-terra / high |
| `reputation-scanner` | gpt-5.6-luna / medium |
| `reputation-classifier` | gpt-5.6-terra / high |
| `reputation-writer` | gpt-5.6-terra / medium |

---

## Source Credibility System

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
- Pipeline C: [`skills/daily-news-intelligence/references/rubric.md`](./skills/daily-news-intelligence/references/rubric.md) + [`.codex/agents/daily-news-scanner.toml`](./.codex/agents/daily-news-scanner.toml) § Source Matrix
- Pipeline E news tiering: [`rules/research/news-source.md`](./rules/research/news-source.md)

---

## Quality Hooks

| Hook | Pipeline | Trigger | What It Does |
|---|---|---|---|
| `daily-news-format-check` | C | PostToolUse:apply_patch | **Blocks** Pipeline C Markdown if format violates spec (count invariants, `[N]` continuity, URLs, canonical quote marks, no global refs section) |
| `email-send-guard` | C / D / E | PreToolUse:Bash | **Blocks** inline `smtplib` / `MIMEMultipart` / `sendmail` Bash commands that bypass the sanctioned `send-*-email.py` scripts |

---

## Project Structure

```
sci-research/
├── .codex-plugin/
│   └── plugin.json                          # Codex plugin manifest (skills + hooks + interface)
├── .agents/plugins/
│   └── marketplace.json                     # Codex install manifest
├── .codex/agents/                           # Native Codex subagents (TOML — dispatched by the skills)
│   ├── daily-news-scanner.toml              # Pipeline C: single-date scan + dedup + Cat5↔Cat6 routing
│   ├── news-verifier.toml                   # Pipeline C: editorial second-pass filter
│   ├── daily-fact-extractor.toml            # Pipeline C: Verifier KEEP → YAML fact manifest
│   ├── daily-news-writer.toml               # Pipeline C: free-prose target-language writer
│   ├── daily-editor.toml                    # Pipeline C: 5-pass post-Writer editor
│   ├── briefing-curator.toml                # Pipeline D: multi-country curator
│   ├── reputation-resolver.toml             # Pipeline E: ticker/name → exec list
│   ├── reputation-scanner.toml              # Pipeline E: per-source (news/reddit/x)
│   ├── reputation-classifier.toml           # Pipeline E: per-item negativity grader
│   └── reputation-writer.toml               # Pipeline E: HTML email body composer
├── skills/                                  # 3 independent skill workflows (SKILL.md = orchestration; agents/openai.yaml = metadata)
│   ├── daily-news-intelligence/             # Pipeline C
│   │   ├── SKILL.md
│   │   ├── agents/openai.yaml               # skill metadata (display_name, default_prompt)
│   │   └── references/                      # Pipeline C specs
│   │       ├── email-spec.md
│   │       ├── language-spec.md
│   │       ├── output-spec.md
│   │       ├── rubric.md
│   │       ├── schemas.md
│   │       └── verification.md
│   ├── daily-briefing/                      # Pipeline D
│   │   ├── SKILL.md
│   │   ├── agents/openai.yaml
│   │   ├── template/briefing-template.docx  # SPD Bank brand template
│   │   ├── references/email-spec.md
│   │   └── scripts/
│   │       ├── generate-branded-docx.py
│   │       └── send-briefing-email.py
│   └── reputation-track/                    # Pipeline E
│       ├── SKILL.md
│       ├── agents/openai.yaml
│       └── references/                      # Pipeline E specs
│           ├── entity-resolution.md
│           ├── source-matrix.md
│           ├── negativity-rubric.md
│           ├── html-template.md
│           ├── email-spec.md
│           └── schemas.md
├── hooks.json                               # Codex hook config (PreToolUse Bash + PostToolUse apply_patch)
├── scripts/
│   ├── hooks/                               # Hook implementations (Node.js)
│   │   ├── daily-news-format-check.js
│   │   └── email-send-guard.js
│   └── send-report-email.py                 # Gmail SMTP (Pipelines C / E)
├── rules/research/
│   └── news-source.md                       # T1-T4 news tiering (Pipeline E dependency)
├── .env.example                             # Gmail SMTP environment template
├── requirements.txt                         # Pipeline D dependency (latest at install time)
├── AGENTS.md                                # Project guidance for Codex
├── PORTING-NOTES.md                         # Runtime-validation status and open checks
├── README.md
└── LICENSE
```

---

## Customization

| Goal | Edit |
|---|---|
| Pipeline C source matrix / date verification | `.codex/agents/daily-news-scanner.toml` + `skills/daily-news-intelligence/references/rubric.md` |
| Pipeline C external-view China rules | `.codex/agents/daily-news-scanner.toml` § Source Matrix § T4-official + Step 2.1 |
| Pipeline C output format / Markdown contract | `skills/daily-news-intelligence/references/output-spec.md` |
| Pipeline C language localisation / bilingual mode | `skills/daily-news-intelligence/references/language-spec.md` (§ Bilingual Mode) |
| Pipeline C email delivery / bilingual email | `skills/daily-news-intelligence/references/email-spec.md` + `scripts/send-report-email.py` |
| Pipeline D brand template | `skills/daily-briefing/template/briefing-template.docx` |
| Pipeline D curator rules | `.codex/agents/briefing-curator.toml` |
| Pipeline E negativity rubric | `skills/reputation-track/references/negativity-rubric.md` |
| Pipeline E news source tiering | `rules/research/news-source.md` |
| Pipeline E HTML email template | `skills/reputation-track/references/html-template.md` |
| Pipeline E entity resolution | `skills/reputation-track/references/entity-resolution.md` + `.codex/agents/reputation-resolver.toml` |
| New output language (Pipeline C) | `.codex/agents/daily-news-writer.toml` + `skills/daily-news-intelligence/references/language-spec.md` |
| Adding hook / changing email-send guard | `scripts/hooks/email-send-guard.js` + the relevant SKILL.md email step |

---

## Requirements

- [Codex](https://developers.openai.com/codex) CLI
- Node.js ≥ 18 (for hook scripts)
- Python 3 (for email delivery scripts + Pipeline D docx generation; only required when `--email` or Pipeline D is used)
- Pipeline D dependency (install or update from the plugin root): `python3 -m pip install --user --upgrade -r requirements.txt`
- `pandoc` (for Markdown → docx conversion in Pipeline C)
- Internet access (for WebSearch `search` / `open_page`)
- Gmail SMTP credentials (only when `--email` is used; see `.env.example`)
- No separate social-media MCP configuration is required. Pipeline E's Reddit/X coverage is limited to publicly indexed, openable content.

---


## License

MIT
