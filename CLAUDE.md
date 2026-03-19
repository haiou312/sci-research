# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with this plugin.

## Project Overview

This is a **Claude Code plugin** for scientific popular-science deep research. Given a topic, comparison entities, and output language, it produces a professionally structured research article (≤5000 words) backed by authoritative sources.

## Architecture

The plugin is organized into the following components:

- **agents/** — Specialized subagents: researcher, comparator, fact-checker, writer
- **skills/** — Core workflow: multi-source retrieval, cross-entity comparison, report generation
- **commands/** — User-facing slash commands: `/sci-research`, `/add-entity`, `/set-lang`
- **contexts/** — Research mode context for behavioral tuning
- **hooks/** — Automated quality gates: word count, entity coverage, reference validation
- **rules/** — Source credibility grading, output format standards
- **scripts/** — Hook implementation scripts (Node.js)
- **examples/** — Complete output samples in Chinese and English

## Key Command

```
/sci-research <topic> --entities "Entity1,Entity2,Entity3" --lang zh|en|ja
```

## Agent Pipeline

```
User Input → Researcher (parallel per entity) → Comparator → Fact-Checker → Writer → Hooks (validation) → Output
```

## Development Notes

- Agent format: Markdown with YAML frontmatter (name, description, tools, model)
- Skill format: Markdown with clear sections (When to Activate, Workflow, Quality Rules)
- Command format: Markdown with description frontmatter
- Hook format: JSON with matcher conditions
- File naming: lowercase with hyphens
