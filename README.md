# sci-research

> A Claude Code plugin for scientific popular-science deep research with multi-entity comparison.

Given a topic and a set of entities (countries, institutions, organizations), this plugin orchestrates a multi-agent pipeline to produce a professionally structured, fully-cited research article — with cross-entity comparison tables, source credibility grading, and automated quality gates.

---

## Why This Plugin

Writing a rigorous popular-science research article typically requires hours of source retrieval, cross-referencing, and structuring. This plugin automates the entire pipeline:

- **4 specialized agents** work in sequence — researcher, comparator, fact-checker, writer
- **Parallel retrieval** — one researcher agent per entity, running simultaneously
- **Credibility-first** — five-tier source grading system ensures authoritative backing
- **Automated quality gates** — hooks enforce word limits, entity coverage, and reference integrity before output

## Features

| Feature | Description |
|---------|-------------|
| Multi-entity comparison | Compare any combination of countries, institutions, or companies |
| Parallel research | One agent per entity, all searching simultaneously |
| Source credibility grading | ★★★★★ (peer-reviewed) to ★☆☆☆☆ (blogs), graded in appendix |
| Fact verification | Cross-references top 10-15 claims against independent sources |
| Multilingual output | `zh` (Chinese), `en` (English), `ja` (Japanese) |
| Quality hooks | Word count, entity coverage, reference integrity — all automated |
| Professional structure | Abstract, methodology, comparison tables, APA 7th references |

---

## Installation

### Option 1: From GitHub Marketplace

```bash
# In Claude Code, add this repo as a marketplace
/plugin marketplace add haiou312/sci-research

# Install the plugin
/plugin install sci-research@haiou312-deep-research-report
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

### Basic Command

```
/sci-research <topic> --entities "Entity1,Entity2,..." --lang zh|en|ja
```

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `topic` | Yes | — | The research subject |
| `--entities` | Yes | — | Comma-separated entities to compare |
| `--lang` | No | `zh` | Output language code |

### Examples

```bash
# Compare nuclear fusion progress across 4 countries (Chinese)
/sci-research 核聚变能源最新进展 --entities "中国,美国,EU,日本"

# mRNA vaccine landscape in English
/sci-research mRNA vaccine technology landscape --entities "US,EU,China" --lang en

# Compare AI companies
/sci-research 大语言模型技术路线对比 --entities "OpenAI,Google DeepMind,Anthropic,Meta AI" --lang zh

# Quantum computing commercialization
/sci-research quantum computing commercialization --entities "IBM,Google,中国科学院" --lang en
```

### Additional Commands

```bash
# Add more entities to an active research session
/add-entity "韩国,印度"

# Switch output language mid-session
/set-lang en
```

---

## How It Works

### Agent Pipeline

```
User Input: topic + entities + lang
       │
       ├──→ Researcher(Entity A) ─┐
       ├──→ Researcher(Entity B) ─┼──→ Comparator ──→ Fact-Checker ──→ Writer ──→ Output
       └──→ Researcher(Entity C) ─┘
                                        │                 │               │
                                  Compare across    Verify top      Generate article
                                  5-8 dimensions    10-15 claims    in target language
                                                                         │
                                                                    ┌────┴────┐
                                                                    │  Hooks  │
                                                                    ├─────────┤
                                                                    │ ≤5000w? │
                                                                    │ Entities│
                                                                    │  Refs?  │
                                                                    └─────────┘
```

| Agent | Model | Role |
|-------|-------|------|
| **Researcher** | Sonnet | Per-entity multi-source retrieval (academic, official, media) |
| **Comparator** | Opus | Cross-entity dimension analysis and root-cause mapping |
| **Fact-Checker** | Sonnet | Claim verification with confidence classification |
| **Writer** | Opus | Structured article synthesis in target language |

### Output Structure

The generated article follows a professional academic-popular format:

```
# {Topic}: Multi-Entity Comparative Research Report

  Abstract                          ← 200 words max
  1. Introduction                   ← background, scope, methodology
  2. Core Concepts                  ← terminology, principles, milestone timeline
  3. Entity-by-Entity Analysis      ← policy, progress, institutions, funding (per entity)
  4. Multi-Dimensional Comparison   ← comparison table, root-cause analysis, competitive landscape
  5. Trends & Outlook               ← short/long-term, risks, societal impact
  6. Conclusion                     ← key findings, open questions
  Appendix A: Glossary
  Appendix B: Source Credibility Table
  References                        ← categorized by type, APA 7th format
```

---

## Source Credibility System

Every source is graded and disclosed in Appendix B:

| Grade | Source Type | Examples |
|-------|-----------|----------|
| ★★★★★ | Peer-reviewed journals | Nature, Science, The Lancet |
| ★★★★★ | International org reports | WHO, OECD, IPCC, World Bank |
| ★★★★☆ | Government reports | DOE, EU Commission, 国务院白皮书 |
| ★★★★☆ | Wire services | Reuters, AP, AFP, 新华社 |
| ★★★☆☆ | Quality journalism | Scientific American, BBC Science |
| ★★★☆☆ | Industry analysis | McKinsey, Gartner, BloombergNEF |
| ★★☆☆☆ | Preprints | arXiv, medRxiv (flagged as non-peer-reviewed) |
| ★☆☆☆☆ | Social media / blogs | Avoided unless verified domain expert |

**Rules:**
- Minimum 10 unique sources per article
- At least 40% must be ★★★★☆ or higher
- At least 60% published within last 24 months

---

## Quality Hooks

Automated validation runs after every article write:

| Hook | Trigger | What It Does |
|------|---------|-------------|
| `word-count-check` | PostToolUse:Write | Blocks output if >5000 words. Supports Chinese character counting. |
| `entity-coverage-check` | PostToolUse:Write | Warns if any specified entity lacks a dedicated section and ≥3 mentions. |
| `reference-validator` | PostToolUse:Write | Warns if inline citations `[N]` don't match reference entries. |
| `research-summary` | Stop | Logs session metadata to `~/.sci-research/sessions/` (async, non-blocking). |

---

## Project Structure

```
sci-research/
├── .claude-plugin/
│   └── plugin.json                 # Plugin metadata
├── agents/
│   ├── researcher.md               # Multi-source retrieval (per entity)
│   ├── comparator.md               # Cross-entity comparison analysis
│   ├── fact-checker.md             # Claim verification specialist
│   └── writer.md                   # Multilingual article writer
├── commands/
│   ├── sci-research.md             # /sci-research — main entry point
│   ├── add-entity.md              # /add-entity — add entities mid-session
│   └── set-lang.md                # /set-lang — switch output language
├── skills/
│   └── sci-research/
│       └── SKILL.md                # Core skill: full workflow definition
├── contexts/
│   └── sci-research.md             # Research mode behavioral context
├── hooks/
│   └── hooks.json                  # Hook configuration (4 hooks)
├── scripts/hooks/
│   ├── word-count-check.js         # Word limit enforcement
│   ├── entity-coverage-check.js    # Entity coverage validation
│   ├── reference-validator.js      # Citation integrity check
│   └── research-summary.js        # Session logging
├── rules/research/
│   ├── source-credibility.md       # Source grading standards
│   └── output-format.md           # Article format standards
├── examples/
│   ├── nuclear-fusion-zh.md        # Full Chinese example (nuclear fusion)
│   └── mrna-vaccine-en.md          # English example (mRNA vaccines)
├── CLAUDE.md                       # Claude Code project guidance
├── AGENTS.md                       # Agent pipeline reference
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

1. Add language guidelines to `agents/writer.md` Section 3 (Language-Specific Guidelines)
2. Update `commands/set-lang.md` supported languages table
3. Add an example output in `examples/`

### Adjusting Word Limit

Edit `scripts/hooks/word-count-check.js`:
```javascript
const WORD_LIMIT = 5000;      // Change this
const CHAR_LIMIT_ZH = 7500;   // Chinese character equivalent
```

### Adding Comparison Dimensions

Edit `agents/comparator.md` Section 1 (Dimension Selection) to add new topic-type dimension sets.

---

## Requirements

- [Claude Code](https://claude.ai/code) CLI
- Node.js ≥ 18 (for hook scripts)
- Internet access (for WebSearch/WebFetch during research)

---

## Acknowledgements

Plugin structure inspired by [everything-claude-code](https://github.com/affaan-m/everything-claude-code) by Affaan Mustafa.

---

## License

MIT
