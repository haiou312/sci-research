# Agent Reference

This plugin has **two independent pipelines**, each with its own agent set.

---

## Pipeline A: `/sci-research` — Deep Research

```
User Input (topic, entities, lang)
        │
        ├──→ [Researcher] × N (one per entity, parallel)
        │         │
        │         ▼
        │    Structured findings per entity
        │         │
        ▼         ▼
   [Comparator] ← aggregated findings
        │
        ▼
   Comparison table + root-cause analysis
        │
        ▼
   [Fact-Checker] ← findings + comparison
        │
        ▼
   Verification report (confidence levels)
        │
        ▼
   [Writer] ← all inputs + lang
        │
        ▼
   Final article (≤5000 words)
        │
        ▼
   [Hooks] → word count / entity coverage / reference integrity
```

## Pipeline B: `/news-scan` — Real-Time News Analysis

```
User Input (topic, entities, period, lang)
        │
        ├──→ [News-Scanner] × N (one per entity, parallel)
        │         │
        │         ▼
        │    Raw news items per entity (8-12 events, no images)
        │         │
        ▼         ▼
   Identify top 3-5 events by significance
        │
        ▼
   [News-Imager] ← top event URLs
        │
        ▼
   Image URLs + alt text (or "No image available")
        │
        ▼
   [News-Analyst] ← news items + image data
        │
        ▼
   Final briefing with embedded images
        │
        ▼
   [Hooks] → news freshness check
```

---

## Agent Inventory

### Pipeline A: Deep Research

| Agent | Model | Tools | Role |
|-------|-------|-------|------|
| researcher | sonnet | Read, Grep, Glob, Bash, WebFetch, WebSearch | Per-entity information retrieval |
| comparator | opus | Read, Grep, Glob | Cross-entity dimension analysis |
| fact-checker | sonnet | Read, Grep, Glob, WebFetch, WebSearch | Claim verification |
| writer | opus | Read, Write, Edit, Grep | Article synthesis |

### Pipeline B: News Scan

| Agent | Model | Tools | Role |
|-------|-------|-------|------|
| news-scanner | sonnet | WebSearch, WebFetch, Read, Grep, Glob | Per-entity real-time news retrieval (no images) |
| news-imager | sonnet | WebFetch, Read, Grep, Glob | Extract article images for top events |
| news-analyst | opus | Read, Write, Edit, Grep | News dedup, timeline, impact analysis, report generation |

---

## When to Use Which Agent

### Pipeline A (`/sci-research`)
- **researcher**: Always first. One instance per entity, run in parallel.
- **comparator**: After all researchers complete. Needs aggregated data.
- **fact-checker**: After comparator. Verifies critical claims.
- **writer**: Last. Produces the final article in the target language.

### Pipeline B (`/news-scan`)
- **news-scanner**: Always first. One instance per entity, run in parallel. Only finds news, no images.
- **news-imager**: After scanners. Receives top 3-5 event URLs, extracts article images.
- **news-analyst**: Last. Receives news items + image data, produces the final briefing.

### Key Difference
Pipelines A and B are **completely independent**. They share no agents. A `/sci-research` run never invokes news-scanner, news-imager, or news-analyst, and a `/news-scan` run never invokes researcher, comparator, fact-checker, or writer.
