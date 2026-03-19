# Agent Reference

## Agent Pipeline

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

## Agent Inventory

| Agent | Model | Tools | Role |
|-------|-------|-------|------|
| researcher | sonnet | Read, Grep, Glob, Bash, WebFetch, WebSearch | Per-entity information retrieval |
| comparator | opus | Read, Grep, Glob | Cross-entity dimension analysis |
| fact-checker | sonnet | Read, Grep, Glob, WebFetch, WebSearch | Claim verification |
| writer | opus | Read, Write, Edit, Grep | Article synthesis |

## When to Use Which Agent

- **researcher**: Always first. One instance per entity, run in parallel.
- **comparator**: After all researchers complete. Needs aggregated data.
- **fact-checker**: After comparator. Verifies critical claims.
- **writer**: Last. Produces the final article in the target language.
