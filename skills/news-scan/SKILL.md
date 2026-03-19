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
  → Agent searches official/regulatory sources, wire services, financial media, industry press
  → Agent returns structured news items with metadata
  → Agent does NOT extract images
```

**Search Strategy:**
- 6-8 queries per entity, covering official announcements, legislation, market impact, data releases
- Search in entity's primary language AND English
- Prioritize: official/regulatory > wire services > financial media > industry press > commentary
- Target 8-12 unique news events per entity

### Phase 2: Image Extraction

Launch **News-Imager** agent with the top 3-5 events from Phase 1:

```
News-Imager receives:
  - List of top 3-5 events with their primary source URLs

News-Imager produces:
  - Image URL + alt text for each event (or "No image available")
  - Does NOT analyze news content — only extracts images
```

### Phase 3: Analysis & Report

Launch **News-Analyst** agent with scanner results + image data:

```
News-Analyst receives:
  - All news items from all scanners (Phase 1)
  - Image data from imager (Phase 2)
  - Topic, entities, period, target language

News-Analyst produces:
  - Deduplicated event list with inline citations [N]
  - Chronological timeline with source references [N]
  - Top 3-5 key events with impact analysis, every fact cited [N]
  - Images embedded for events where available (skipped if not)
  - Trend signals and risk alerts with evidence citations [N]
  - Numbered reference list with full URLs (same format as /sci-research)
  - Source credibility assessment table
```

## Output Structure

```
# {Topic} 实时新闻分析报告

> 时间范围 | 关注实体 | 生成日期 | 事件总数 | 来源数

## 术语速查（缩写 → 全称 → 一句话解释，表格形式）

## 1. 核心事件摘要（3-5条，每个事实标注 [N] 引用）
## 2. 完整事件时间线（表格，来源列用 [N] 编号）
## 3. 分领域动态（正文内每个事实标注 [N]）
   ### 监管层 / 行业层 / TPP生态层 / 消费者端
## 4. 核心事件影响分析
   - 每个核心事件标题下方嵌入新闻配图（来自 og:image），标注图片来源
   - 自然段落叙述，禁止使用"发生了什么/为什么重要"标签
   - 第一段陈述事实，第二段自然过渡到意义分析
   - 每个核心事件附影响矩阵表格
   | 维度 | 短期影响 | 长期影响 | 受影响方 | 确定性 | 来源 [N] |
## 5. 趋势信号与风险提示（每个趋势/风险标注证据 [N]）
## 参考文献（编号对应正文 [N]，每条含 URL，分类排列）
## 附录：来源可信度评级
```

**写作风格要求：**
- 影响分析部分使用自然流畅的段落叙述，禁止使用"发生了什么""为什么重要"等机械标签
- 用过渡性表达衔接事实与分析（如"这份文件的分量在于""这直接威胁到""两者叠加的意义在于"）
- 所有专有名词/缩写首次出现时附全称和一句话解释
- 报告开头设置术语速查表

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
8. **Cite every fact with [N].** Every factual claim in the report must have an inline citation [N] linking to the References section. Same standard as `/sci-research`.
9. **Every reference must have a URL.** No URL = cannot be cited. Readers must be able to click through to verify.
10. **Reference integrity.** Every [N] in text maps to one entry in References. No orphans, no gaps.

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
