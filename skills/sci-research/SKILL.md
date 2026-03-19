---
name: sci-research
description: Scientific popular-science deep research with multi-entity comparison. Searches academic papers, news, official reports, and web sources, then produces a structured ≤5000-word article with authoritative references. Supports cross-country/institution/organization comparison with user-specified entities and output language.
origin: sci-research-plugin
---

# Scientific Popular-Science Deep Research

Produce rigorous, accessible, and fully-cited scientific research articles that compare multiple entities (countries, institutions, organizations) on a given topic.

## When to Activate

- User asks to research a scientific or technology topic with entity comparison
- User says "科普研究", "deep research", "比较研究", "科学调研"
- User invokes `/sci-research`
- User wants a structured article with authoritative references on a science topic
- User specifies entities (countries/organizations) to compare on a topic

## Input Parameters

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| `topic` | Yes | The research subject | "核聚变能源进展" |
| `--entities` | Yes | Comma-separated entities to compare | "中国,美国,EU,日本" |
| `--lang` | No (default: zh) | Output language: zh, en, ja | "en" |

## Entity Resolution

Before research begins, resolve each entity to its canonical form:

| Input | Resolved Entity | Search Languages |
|-------|----------------|------------------|
| "中国" / "China" | People's Republic of China | zh, en |
| "美国" / "US" / "USA" | United States of America | en |
| "EU" / "欧盟" | European Union (collective) | en, fr, de |
| "日本" / "Japan" | Japan | ja, en |
| "ITER" | ITER Organization | en, fr |
| "WHO" | World Health Organization | en |

For ambiguous entities, ask the user to clarify:
- "EU" → the EU collectively, or specific member states?
- "中国" → mainland China only, or including Hong Kong/Taiwan?

## Workflow

### Phase 1: Research (Parallel)

Launch one **Researcher** agent per entity, all in parallel:

```
For each entity in [Entity A, Entity B, ...Entity N]:
  → Spawn Researcher agent with (topic, entity)
  → Agent searches across academic, official, and media sources
  → Agent returns structured findings with source metadata
```

**Search Strategy:**
- Generate 4-6 queries per entity, covering: status, policy, funding, milestones, challenges
- Search in the entity's primary language AND English
- Prioritize sources by credibility tier (★★★★★ to ★★☆☆☆)
- Target 15-30 unique sources total across all entities

### Phase 2: Comparison

Launch **Comparator** agent with all entity findings:

```
Comparator receives:
  - Research findings from all Researcher agents
  - Topic category (technology / policy / health / environment)

Comparator produces:
  - 5-8 comparison dimensions (auto-selected by topic type)
  - Structured comparison table with normalized data
  - Root-cause analysis of key differences
  - Competitive landscape narrative
```

**Dimension Auto-Selection by Topic Type:**

| Topic Type | Example Dimensions |
|------------|-------------------|
| Technology | TRL, R&D budget, patents, key facilities, talent pool |
| Policy | Legal framework, enforcement, coverage, timeline, budget |
| Health | Clinical trials, approval status, access, outcomes, capacity |
| Energy/Env | Capacity, cost, carbon impact, incentives, investment |

### Phase 3: Fact-Check

Launch **Fact-Checker** agent:

```
Fact-Checker receives:
  - Combined research findings
  - Comparison analysis

Fact-Checker produces:
  - Verification status for top 10-15 critical claims
  - Confidence classification (Verified / Likely / Unverified / Disputed)
  - Required corrections
  - Additional sources found
```

### Phase 4: Writing

Launch **Writer** agent:

```
Writer receives:
  - All research findings
  - Comparison analysis
  - Fact-check report
  - Target language (zh/en/ja)

Writer produces:
  - Complete article following the professional structure
  - ≤5000 words
  - APA 7th edition references, categorized by source type
  - Appendices (glossary, source credibility table)
```

### Phase 5: Validation (Hooks)

Automated hooks validate the output:
1. **Word count check**: ≤5000 words
2. **Entity coverage check**: every specified entity has substantive content
3. **Reference integrity check**: every [N] citation has a matching reference entry

## Output Structure

```
# {Topic}：多实体比较研究报告

## 摘要 (≤200 words)
## 1. 引言 (背景、范围、方法论)
## 2. 核心概念与技术原理 (术语、原理、里程碑时间线)
## 3. 各实体现状分析 (per-entity: 政策、进展、机构、资金)
## 4. 多维比较分析 (维度说明、对比表、差异成因、竞争格局)
## 5. 趋势研判与前瞻 (短期、中长期、风险、影响)
## 6. 结论 (核心发现、优劣势、开放问题)
## 附录 (术语表、来源可信度表)
## 参考文献 (分类: 论文 → 报告 → 媒体 → 其他)
```

## Source Credibility Grading

| Grade | Source Type | Examples |
|-------|-----------|----------|
| ★★★★★ | Peer-reviewed journals | Nature, Science, The Lancet, Cell |
| ★★★★★ | International org reports | WHO, OECD, World Bank, IPCC |
| ★★★★☆ | National gov reports | 国务院白皮书, US DOE reports, EU Commission |
| ★★★★☆ | Mainstream wire services | Reuters, AP, AFP, 新华社 |
| ★★★☆☆ | Quality journalism | Scientific American, BBC Science, 科技日报 |
| ★★★☆☆ | Industry analysis | McKinsey, Gartner, BloombergNEF |
| ★★☆☆☆ | Preprints | arXiv, medRxiv, bioRxiv (flag as non-peer-reviewed) |
| ★★☆☆☆ | Wikipedia | Context only, never primary source |
| ★☆☆☆☆ | Social media, blogs | Avoid unless from verified domain expert |

## Quality Rules

1. **Every claim needs a source.** No unsourced assertions in the final article.
2. **Cross-reference critical claims.** Key findings must appear in ≥2 independent sources.
3. **Recency matters.** Prefer sources from the last 24 months.
4. **Acknowledge gaps.** If data is unavailable for an entity, state it explicitly.
5. **No hallucination.** If you don't know, say "目前尚无权威数据" / "insufficient data."
6. **Separate fact from inference.** Label projections and opinions clearly.
7. **Balance entity coverage.** Each entity should receive proportional analysis depth.
8. **Respect word limit.** Hard cap at 5000 words. If over, cut outlook section first.

## Examples

### Example 1: Quick Invocation
```
/sci-research 核聚变能源最新进展 --entities "中国,美国,EU,日本" --lang zh
```

### Example 2: English Output
```
/sci-research mRNA vaccine technology landscape --entities "US,EU,China" --lang en
```

### Example 3: Institutional Comparison
```
/sci-research 大语言模型技术路线对比 --entities "OpenAI,Google DeepMind,Anthropic,Meta AI" --lang zh
```

### Example 4: Minimal (Defaults)
```
/sci-research 量子计算商业化进展 --entities "IBM,Google,中国科学院"
```
(Defaults to --lang zh)
