# sci-research

> A Claude Code plugin with two independent pipelines: **deep research** for scientific articles and **news scan** for real-time news analysis.

Given a topic and a set of entities, this plugin orchestrates multi-agent pipelines to produce either a professionally structured research article or a real-time news briefing — with source credibility grading and automated quality gates.

---

## Two Feature Lines

| | `/sci-research` | `/news-scan` |
|---|---|---|
| **Purpose** | Deep research article with multi-entity comparison | Real-time news briefing with impact analysis |
| **Time focus** | Historical + current | Last 7-90 days |
| **Sources** | Academic papers, official reports, authoritative media | Wire services, financial media, industry press |
| **Agents** | 4 (researcher → comparator → fact-checker → writer) | 2 (news-scanner → news-analyst) |
| **Output** | ≤5000-word structured article with APA references | 1000-3000-word briefing with event timeline |
| **Shared agents** | None — completely independent pipelines | None |

---

## Why This Plugin

- **6 specialized agents** across two independent pipelines
- **Parallel retrieval** — one agent per entity, running simultaneously
- **Credibility-first** — five-tier source grading system for both pipelines
- **Automated quality gates** — hooks enforce word limits, entity coverage, reference integrity, and news freshness
- **Multilingual** — Chinese, English, Japanese output

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
# Clone the repo
git clone https://github.com/haiou312/sci-research.git

# Launch Claude Code with the plugin loaded
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

---

## Usage

### Pipeline A: Deep Research

```
/sci-research <topic> --entities "Entity1,Entity2,..." --lang zh|en|ja
```

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `topic` | Yes | — | The research subject |
| `--entities` | Yes | — | Comma-separated entities to compare |
| `--lang` | No | `zh` | Output language code |

**Examples:**
```bash
# Compare nuclear fusion progress across 4 countries (Chinese)
/sci-research 核聚变能源最新进展 --entities "中国,美国,EU,日本"

# mRNA vaccine landscape in English
/sci-research mRNA vaccine technology landscape --entities "US,EU,China" --lang en

# Compare AI companies
/sci-research 大语言模型技术路线对比 --entities "OpenAI,Google DeepMind,Anthropic" --lang zh
```

### Pipeline B: News Scan

```
/news-scan <topic> --entities "Entity1,Entity2,..." --period 7d|30d|90d --lang zh|en|ja
```

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `topic` | Yes | — | News search subject |
| `--entities` | No | (broad search) | Comma-separated entities to focus on |
| `--period` | No | `30d` | Time window: `7d`, `30d`, or `90d` |
| `--lang` | No | `zh` | Output language code |

**Examples:**
```bash
# Recent Open Banking news, UK and China focus
/news-scan 开放银行最新进展 --entities "中国,英国" --lang zh

# Quick 7-day scan in English
/news-scan Open Banking UK --period 7d --lang en

# Broad scan without entity filter
/news-scan AI regulation --period 90d --lang en

# Single entity news
/news-scan 数字人民币 --entities "中国" --period 30d --lang zh
```

### Utility Commands

```bash
# Add more entities to an active research session
/add-entity "韩国,印度"

# Switch output language mid-session
/set-lang en
```

---

## How It Works

### Pipeline A: `/sci-research`

```
User: /sci-research <topic> --entities "A,B,C" --lang zh
  │
  ├─→ Researcher(A) ─┐
  ├─→ Researcher(B) ─┼─→ Comparator ─→ Fact-Checker ─→ Writer ─→ Hooks ─→ Output
  └─→ Researcher(C) ─┘
```

| Agent | Model | Role |
|-------|-------|------|
| **Researcher** | Sonnet | Per-entity multi-source retrieval (academic, official, media) |
| **Comparator** | Opus | Cross-entity dimension analysis and root-cause mapping |
| **Fact-Checker** | Sonnet | Claim verification with confidence classification |
| **Writer** | Opus | Structured article synthesis in target language |

**Output structure:**
```
Abstract → Introduction → Core Concepts → Entity Analysis → Comparative Analysis
→ Trends & Outlook → Conclusion → Glossary → Source Credibility Table → References (APA 7th)
```

### Pipeline B: `/news-scan`

```
User: /news-scan <topic> --entities "A,B" --period 30d --lang zh
  │
  ├─→ News-Scanner(A) ─┐
  │                     ├─→ News-Analyst ─→ Hooks ─→ Output
  └─→ News-Scanner(B) ─┘
```

| Agent | Model | Role |
|-------|-------|------|
| **News-Scanner** | Sonnet | Per-entity real-time news retrieval from wire services and media |
| **News-Analyst** | Opus | Deduplication, timeline, impact analysis, trend signals |

**Output structure:**
```
Key Events Summary → Full Event Timeline → Entity-by-Entity Developments
→ Impact Analysis (per event matrix) → Trend Signals & Risk Alerts → Sources
```

---

## Source Credibility Systems

### For `/sci-research` (Academic & Official)

| Grade | Source Type | Examples |
|-------|-----------|----------|
| ★★★★★ | Peer-reviewed journals | Nature, Science, The Lancet |
| ★★★★★ | International org reports | WHO, OECD, IPCC, World Bank |
| ★★★★☆ | Government reports | DOE, EU Commission, 国务院白皮书 |
| ★★★★☆ | Wire services | Reuters, AP, AFP, 新华社 |
| ★★★☆☆ | Quality journalism | Scientific American, BBC Science |
| ★★☆☆☆ | Preprints | arXiv, medRxiv (flagged as non-peer-reviewed) |

### For `/news-scan` (News & Media)

| Grade | Source Type | Examples |
|-------|-----------|----------|
| ★★★★★ | Wire services | Reuters, AP, AFP, 新华社 |
| ★★★★☆ | Financial/business media | FT, Bloomberg, CNBC, 财新, BBC |
| ★★★☆☆ | Industry vertical media | Finextra, TechCrunch, 36氪 |
| ★★☆☆☆ | Think tank commentary | Brookings, PIIE, VoxEU |
| ★☆☆☆☆ | Social media / blogs | Avoided unless verified expert |

---

## Quality Hooks

| Hook | Pipeline | Trigger | What It Does |
|------|----------|---------|-------------|
| `word-count-check` | A | PostToolUse:Write | Blocks if >5000 words. Supports Chinese character counting. |
| `entity-coverage-check` | A | PostToolUse:Write | Warns if any entity lacks dedicated section and ≥3 mentions. |
| `reference-validator` | A | PostToolUse:Write | Warns if inline citations `[N]` don't match reference entries. |
| `news-freshness-check` | B | PostToolUse:Write | Warns if no sources from the last 7 days in news reports. |
| `research-summary` | A & B | Stop | Logs session metadata (async, non-blocking). |

---

## Project Structure

```
sci-research/
├── .claude-plugin/
│   ├── plugin.json                    # Plugin metadata
│   └── marketplace.json              # Marketplace manifest
├── agents/                            # 6 agents across 2 pipelines
│   ├── researcher.md                  # [A] Per-entity information retrieval
│   ├── comparator.md                  # [A] Cross-entity comparison analysis
│   ├── fact-checker.md                # [A] Claim verification specialist
│   ├── writer.md                      # [A] Multilingual article writer
│   ├── news-scanner.md                # [B] Per-entity real-time news retrieval
│   └── news-analyst.md               # [B] News timeline and impact analysis
├── commands/                          # 4 slash commands
│   ├── sci-research.md                # /sci-research — deep research entry point
│   ├── news-scan.md                   # /news-scan — news analysis entry point
│   ├── add-entity.md                  # /add-entity — add entities mid-session
│   └── set-lang.md                    # /set-lang — switch output language
├── skills/                            # 2 independent skill definitions
│   ├── sci-research/
│   │   └── SKILL.md                   # Deep research workflow
│   └── news-scan/
│       └── SKILL.md                   # News scan workflow
├── contexts/
│   └── sci-research.md                # Research mode behavioral context
├── hooks/
│   └── hooks.json                     # Hook configuration (5 hooks)
├── scripts/hooks/                     # Hook implementations
│   ├── word-count-check.js            # [A] ≤5000 word enforcement
│   ├── entity-coverage-check.js       # [A] Entity coverage validation
│   ├── reference-validator.js         # [A] Citation integrity check
│   ├── news-freshness-check.js        # [B] News recency validation
│   └── research-summary.js            # [A&B] Session logging
├── rules/research/                    # 3 quality rules
│   ├── source-credibility.md          # Academic source grading (Pipeline A)
│   ├── output-format.md               # Article format standards (Pipeline A)
│   └── news-source.md                 # News source grading & dedup (Pipeline B)
├── examples/                          # Sample outputs
│   ├── nuclear-fusion-zh.md           # Full Chinese example (nuclear fusion)
│   └── mrna-vaccine-en.md             # English example (mRNA vaccines)
├── CLAUDE.md                          # Claude Code project guidance
├── AGENTS.md                          # Agent pipeline reference (both pipelines)
└── README.md
```

---

## Examples

See the [`examples/`](./examples/) directory for complete sample outputs:

- **[nuclear-fusion-zh.md](./examples/nuclear-fusion-zh.md)** — 核聚变能源进展，中/美/EU/日本四方比较（中文完整示例）
- **[mrna-vaccine-en.md](./examples/mrna-vaccine-en.md)** — mRNA vaccine technology landscape, US/EU/China comparison (English)

---

## Customization

### Adding a New Language

1. Add language guidelines to `agents/writer.md` and `agents/news-analyst.md`
2. Update `commands/set-lang.md` supported languages table
3. Add an example output in `examples/`

### Adjusting Word Limit (Pipeline A)

Edit `scripts/hooks/word-count-check.js`:
```javascript
const WORD_LIMIT = 5000;      // Change this
const CHAR_LIMIT_ZH = 7500;   // Chinese character equivalent
```

### Adjusting News Freshness Window (Pipeline B)

Edit `scripts/hooks/news-freshness-check.js`:
```javascript
const sevenDaysAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
// Change 7 to your preferred window
```

### Adding Comparison Dimensions (Pipeline A)

Edit `agents/comparator.md` Section 1 (Dimension Selection) to add new topic-type dimension sets.

---

## Requirements

- [Claude Code](https://claude.ai/code) CLI
- Node.js ≥ 18 (for hook scripts)
- Internet access (for WebSearch/WebFetch during research and news scanning)

---

## Acknowledgements

Plugin structure inspired by [everything-claude-code](https://github.com/affaan-m/everything-claude-code) by Affaan Mustafa.

---

## License

MIT
