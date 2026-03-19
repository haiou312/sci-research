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
        │    Raw news items per entity
        │         │
        ▼         ▼
   [News-Analyst] ← aggregated news items
        │
        ▼
   Deduplicated timeline + impact analysis
        │
        ▼
   News briefing (1000-3000 words)
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
| news-scanner | sonnet | WebSearch, WebFetch, Read, Grep, Glob | Per-entity real-time news retrieval |
| news-analyst | opus | Read, Write, Edit, Grep | News dedup, timeline, impact analysis |

---

## When to Use Which Agent

### Pipeline A (`/sci-research`)
- **researcher**: Always first. One instance per entity, run in parallel.
- **comparator**: After all researchers complete. Needs aggregated data.
- **fact-checker**: After comparator. Verifies critical claims.
- **writer**: Last. Produces the final article in the target language.

### Pipeline B (`/news-scan`)
- **news-scanner**: Always first. One instance per entity, run in parallel.
- **news-analyst**: After all scanners complete. Produces the final briefing.

### Key Difference
Pipelines A and B are **completely independent**. They share no agents. A `/sci-research` run never invokes news-scanner or news-analyst, and a `/news-scan` run never invokes researcher, comparator, fact-checker, or writer.
