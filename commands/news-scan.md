---
description: Scan real-time news for a topic with entity-specific analysis. Usage: /news-scan <topic> --entities "Entity1,Entity2,..." --period 7d|30d|90d --lang zh|en|ja
---

# News Scan

Real-time news retrieval and impact analysis for a given topic, producing a structured news briefing with images.

## Parameter Parsing

Parse user input for four parameters:

1. **topic** (required): Everything before the first `--` flag
2. **--entities** (optional): Comma-separated list of entities to focus on. If omitted, search broadly.
3. **--period** (optional, default: "30d"): Time window — `7d`, `30d`, or `90d`
4. **--lang** (optional, default: "zh"): Output language code

## Execution Pipeline

### Step 1: Confirm Scope

Display a brief confirmation:

```
📰 新闻主题: {topic}
🏢 关注实体: {entity1}, {entity2}, ... (or "全局")
📅 时间范围: 过去 {period}
🌐 输出语言: {lang}

开始扫描？(Y/n)
```

### Step 2: News Scanning (parallel)

Launch **News-Scanner** agents in parallel (one per entity, or one if no entities specified):

```
For each entity:
  Agent(subagent_type="news-scanner") with prompt:
    "Scan news for topic: {topic}
     Target entity: {entity}
     Time window: {period}
     Search in languages: {entity_languages}
     Return structured news items with source metadata.
     Do NOT extract images — a separate agent handles that.
     Target 8-12 unique events."
```

If no `--entities` specified, launch a single News-Scanner with broad search.

### Step 3: Image Extraction

From the Scanner results, identify the top 3-5 events by significance.
Launch **News-Imager** agent with their primary source URLs:

```
Agent(subagent_type="news-imager") with prompt:
  "Extract the main article image for each of these top news events:
   Event 1: {headline} — URL: {primary_source_url}
   Event 2: {headline} — URL: {primary_source_url}
   Event 3: {headline} — URL: {primary_source_url}
   ...
   Return image URL + alt text for each. Report 'No image available' if none found."
```

### Step 4: Analysis & Report Generation

Launch **News-Analyst** agent with all inputs:

```
Agent(subagent_type="news-analyst") with prompt:
  "Analyze news scan results and produce a complete report:
   Topic: {topic}
   Entities: {entities}
   Period: {period}
   Output language: {lang}
   Scanner results: {all_scanner_outputs}
   Image data: {imager_output}

   Embed images in Section 4 for events where images were found.
   Skip images for events marked 'No image available'."
```

### Step 5: Delivery

- Display the full report in chat
- Save to file: `{topic}-news-{date}.md`
- If user requests Word export, use: `pandoc --extract-media=./media {file}.md -o {file}.docx` to ensure remote images are downloaded and embedded
- If user requests PDF export, use: `md-to-pdf` (remote images render natively)
