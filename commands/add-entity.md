---
description: Add one or more entities to the current research session. Usage: /add-entity "Japan,Korea"
---

# Add Entity

Add additional comparison entities to an in-progress or completed research session.

## Behavior

1. Parse the comma-separated entity list from user input
2. Resolve each entity to canonical form
3. Launch a new **Researcher** agent for each added entity
4. Re-run **Comparator** with the expanded entity set
5. Re-run **Fact-Checker** on new claims
6. Re-generate article via **Writer** with all entities

## Usage

```
/add-entity "韩国,印度"
```

If no research session is active, prompt:
> "当前没有进行中的研究。请先使用 /sci-research 启动一个研究任务。"
