---
description: Launch a scientific popular-science deep research with multi-entity comparison. Usage: /sci-research <topic> --entities "Entity1,Entity2,..." --lang zh|en|ja
---

# Scientific Deep Research

Multi-source deep research with cross-entity comparison, producing a ≤5000-word professional article with authoritative references.

## Parameter Parsing

Parse user input for three parameters:

1. **topic** (required): Everything before the first `--` flag
2. **--entities** (required): Comma-separated list of entities to compare
3. **--lang** (optional, default: "zh"): Output language code

If `--entities` is missing, ask the user:
> "请指定要比较的实体（国家/机构/组织），用逗号分隔。例如：--entities \"中国,美国,EU\""

## Execution Pipeline

### Step 1: Confirm Scope

Display a brief confirmation:

```
📋 研究主题: {topic}
🏢 比较实体: {entity1}, {entity2}, ...
🌐 输出语言: {lang}
⏱️ 预计需要 3-5 分钟

确认开始？(Y/n)
```

### Step 2: Entity Resolution

Resolve each entity to canonical form:
- Normalize aliases ("US" = "USA" = "美国" = "United States")
- Determine search languages per entity
- Flag ambiguous entities for clarification

### Step 3: Parallel Research

Launch **Researcher** agents in parallel (one per entity):

```
For each entity:
  Agent(subagent_type="researcher") with prompt:
    "Research topic: {topic}
     Target entity: {entity}
     Search in languages: {entity_languages}
     Return structured findings with source metadata."
```

### Step 4: Comparison Analysis

Launch **Comparator** agent with aggregated findings:

```
Agent(subagent_type="comparator") with prompt:
  "Topic: {topic}
   Entity findings: {all_researcher_outputs}
   Build comparison table and root-cause analysis."
```

### Step 5: Fact Verification

Launch **Fact-Checker** agent:

```
Agent(subagent_type="fact-checker") with prompt:
  "Verify top 10-15 critical claims from:
   Research findings: {all_researcher_outputs}
   Comparison: {comparator_output}"
```

### Step 6: Article Generation

Launch **Writer** agent:

```
Agent(subagent_type="writer") with prompt:
  "Write article in {lang}:
   Topic: {topic}
   Entities: {entities}
   Research: {all_researcher_outputs}
   Comparison: {comparator_output}
   Fact-check: {fact_checker_output}
   Word limit: 5000"
```

### Step 7: Validation & Delivery

After Writer completes, run validation checks:

1. **Word count**: Count words/characters. If over 5000, ask Writer to trim.
2. **Entity coverage**: Verify each entity has a dedicated section in §3.
3. **Reference integrity**: Verify every inline [N] has a matching reference.
4. **Credibility table**: Verify Appendix B is populated.

If all checks pass:
- Display the full article in chat
- Save to file: `{topic}-research-{date}.md`

If checks fail:
- Report which checks failed
- Re-invoke Writer with correction instructions
