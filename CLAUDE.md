# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with this plugin.

## Project Overview

This is a **Claude Code plugin** with two independent feature lines:

1. **Deep Research** (`/sci-research`) — Given a topic, comparison entities, and output language, produces a professionally structured research article (≤5000 words) backed by authoritative academic and official sources.
2. **News Scan** (`/news-scan`) — Given a topic and time window, retrieves real-time news and produces a structured briefing with event timeline, impact analysis, and trend signals.

## Architecture

The plugin is organized into the following components:

- **agents/** — 7 specialized subagents across two pipelines:
  - Pipeline A (deep research): researcher, comparator, fact-checker, writer
  - Pipeline B (news scan): news-scanner, news-imager, news-analyst
- **skills/** — Core workflow definitions for each pipeline
- **commands/** — User-facing slash commands: `/sci-research`, `/news-scan`, `/add-entity`, `/set-lang`
- **contexts/** — Research mode context for behavioral tuning
- **hooks/** — Automated quality gates: word count, entity coverage, reference validation, news freshness
- **rules/** — Source credibility grading, output format standards, news source rules
- **scripts/** — Hook implementation scripts (Node.js)
- **examples/** — Complete output samples in Chinese and English

## Key Commands

```
# Deep research article
/sci-research <topic> --entities "Entity1,Entity2" --lang zh|en|ja

# Real-time news briefing
/news-scan <topic> --entities "Entity1,Entity2" --period 7d|30d|90d --lang zh|en|ja
```

## Agent Pipelines

```
Pipeline A (/sci-research):
  User Input → Researcher (parallel) → Comparator → Fact-Checker → Writer → Hooks → Output

Pipeline B (/news-scan):
  User Input → News-Scanner (parallel) → News-Imager (top events) → News-Analyst → Hooks → Output
```

The two pipelines are **completely independent** and share no agents.

## Development Notes

- Agent format: Markdown with YAML frontmatter (name, description, tools, model)
- Skill format: Markdown with clear sections (When to Activate, Workflow, Quality Rules)
- Command format: Markdown with description frontmatter
- Hook format: JSON with matcher conditions
- File naming: lowercase with hyphens
