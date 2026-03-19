---
name: news-scan
description: Real-time news scanning and impact analysis. Searches recent news (7-90 days) on any topic, optionally filtered by entities, and produces a structured briefing with event timeline, impact analysis, and trend signals. Independent from the sci-research deep analysis pipeline.
origin: sci-research-plugin
---

# Real-Time News Scan & Analysis

Retrieve and analyze the latest news on any topic, producing an actionable briefing with event timelines and impact assessment.

## When to Activate

- User asks for recent news on a topic
- User says "新闻扫描", "news scan", "最新动态", "热点", "trending", "what's happening with"
- User invokes `/news-scan`
- User wants a quick overview of recent developments (not a deep research article)

## Relationship to /sci-research

This is a **completely independent** feature line:

| | `/sci-research` | `/news-scan` |
|---|---|---|
| Purpose | Deep research article | Real-time news briefing |
| Time focus | Historical + current | Last 7-90 days only |
| Sources | Academic, official reports, media | Wire services, financial media, industry press |
| Agent pipeline | 4 agents (researcher → comparator → fact-checker → writer) | 2 agents (news-scanner → news-analyst) |
| Output length | ≤5000 words | 1000-3000 words |
| Shared agents | None | None |

## Input Parameters

| Parameter | Required | Default | Description | Example |
|-----------|----------|---------|-------------|---------|
| `topic` | Yes | — | News search subject | "Open Banking UK" |
| `--entities` | No | (broad search) | Comma-separated entities | "UK,China" |
| `--period` | No | `30d` | Time window | `7d`, `30d`, `90d` |
| `--lang` | No | `zh` | Output language | `zh`, `en`, `ja` |

## Workflow

### Phase 1: News Scanning (Parallel)

Launch one **News-Scanner** agent per entity (or one for broad search):

```
For each entity in [Entity A, Entity B, ...]:
  → Spawn News-Scanner agent with (topic, entity, period)
  → Agent searches wire services, financial media, industry press
  → Agent returns structured news items with metadata
```

**Search Strategy:**
- 4-6 queries per entity, mixing topic keywords with entity name
- Search in entity's primary language AND English
- Prioritize: wire services > financial media > industry press > commentary
- Target 10-20 unique news events total

### Phase 2: Analysis & Report

Launch **News-Analyst** agent with all scanner results:

```
News-Analyst receives:
  - All news items from all scanners
  - Topic, entities, period, target language

News-Analyst produces:
  - Deduplicated event list
  - Chronological timeline
  - Top 3-5 key events with impact analysis
  - Trend signals and risk alerts
  - Source list with credibility grades
```

## Output Structure

```
# {Topic} 实时新闻分析报告

> 时间范围 | 关注实体 | 生成日期 | 事件总数 | 来源数

## 1. 核心事件摘要（3-5条最重要的）
## 2. 完整事件时间线（表格）
## 3. 分实体动态
   ### Entity A
   ### Entity B
## 4. 影响分析（每个核心事件的影响矩阵）
   | 维度 | 短期影响 | 长期影响 | 受影响方 | 确定性 |
## 5. 趋势信号与风险提示
## 来源列表
```

## News Source Credibility

| Grade | Source Type | Examples |
|-------|-----------|----------|
| ★★★★★ | Wire services | Reuters, AP, AFP, 新华社 |
| ★★★★☆ | Financial/business media | FT, Bloomberg, CNBC, 财新, BBC |
| ★★★☆☆ | Industry vertical media | Finextra, TechCrunch, 36氪 |
| ★★☆☆☆ | Think tank commentary | Brookings, PIIE, VoxEU |
| ★☆☆☆☆ | Social media / blogs | Avoid unless verified expert |

## Quality Rules

1. **Recency is king.** Most recent events first.
2. **Wire services as ground truth.** Always trace stories to original wire service reporting.
3. **Deduplicate aggressively.** Same event from 5 outlets = 1 event with 5 corroborations.
4. **Facts before analysis.** State what happened before interpreting why it matters.
5. **No inflation.** If only 2 significant events occurred, report 2.
6. **Date every event.** Exact publication date required.
7. **Flag single-source claims.** Mark as "[unconfirmed — single source]".

## Examples

### Example 1: Quick 7-day scan
```
/news-scan Open Banking UK --period 7d --lang en
```

### Example 2: Multi-entity with default period
```
/news-scan 开放银行最新进展 --entities "中国,英国" --lang zh
```

### Example 3: Broad scan without entities
```
/news-scan AI regulation --period 90d --lang en
```

### Example 4: Chinese topic
```
/news-scan 数字人民币 --entities "中国" --period 30d --lang zh
```
