---
name: monthly-news-intelligence
description: "Generate a single-country or regional monthly top-news report from existing Sci-Research Pipeline C daily Markdown reports (monthly news, monthly country briefing, monthly hotspot news, 月度新闻, 月度热点新闻, 一个月热点新闻, 月間ニュース). Use for a specified YYYY-MM when the source must come only from ~/.sci-research/reports/daily-news, with event-level monthly clustering, cross-category deduplication, the same category/story/APA-reference structure as daily-news-intelligence, multilingual Markdown, optional docx, and optional controlled email delivery. Never searches the web."
---

# Monthly News Intelligence

Generate one country's or region's monthly top-news report from existing
Pipeline C Markdown. Treat the daily reports as the complete evidence boundary:
never use WebSearch, open URLs, or add outside facts.

## Quick Checklist

- Validate `country`, `month`, language, story target, source and output paths.
- Derive localized country names and one canonical source-language priority.
- Run the read-only collector; persist its stdout as the immutable source index.
- Stop on zero reports or malformed selected input; expose partial coverage.
- Run Monthly Curator once per active category, concurrently.
- Mechanically bundle outputs; run Monthly Verifier once.
- Run Monthly Fact Extractor once.
- Run Writer and then Editor once per language, concurrently within each stage.
- Run the monthly format gate, export DOCX, and optionally send one controlled
  email.

## Parameters

| Parameter | Required | Default | Meaning |
|---|---:|---|---|
| `country` | Yes | — | Normalized English country or region used by Pipeline C |
| `month` | Yes | — | ISO `YYYY-MM`; reject a future month |
| `lang` | No | `zh` | `zh`, `en`, `ja`, or any two joined by `+`; first is primary |
| `source_dir` | No | `~/.sci-research/reports/daily-news/` | Pipeline C date-directory root |
| `source_lang` | No | `auto` | `auto`, `zh`, `en`, or `ja`; explicit language disables fallback |
| `stories_per_category` | No | `3` | Target event clusters per category; integer 1–5 |
| `require_complete_month` | No | `false` | Stop unless every expected date through `as_of` has a usable report |
| `as_of` | No | today | Current-month upper bound, ISO `YYYY-MM-DD` |
| `out_dir` | No | `~/.sci-research/reports/monthly-news/{month}/` | Output directory |
| `email` | No | none | Explicit recipient; absence means no email |
| `email_attach` | No | `both` | `both`, `docx`, `md`, or `none` |
| `email_dry_run` | No | `false` | Preview controlled email without SMTP |
| `email_subject` | No | auto | Optional override |
| `email_body` / `email_body_file` | No | auto | Optional body override; mutually exclusive |

Reject duplicate/unsupported language tokens, three-language combinations,
invalid email attachment modes, and `as_of` earlier than the requested month.

## Runtime Paths and Required References

Resolve absolute paths before stage work:

```text
PLUGIN_ROOT=<directory containing .codex-plugin/plugin.json>
SKILL_ROOT=$PLUGIN_ROOT/skills/monthly-news-intelligence
DAILY_SKILL_ROOT=$PLUGIN_ROOT/skills/daily-news-intelligence
```

Confirm all three roots and their `SKILL.md` or plugin manifest exist. Read:

- `references/selection-rubric.md` before Curator/Verifier dispatch;
- `references/schemas.md` before validating any stage output;
- `references/output-overrides.md` before Writer dispatch;
- `references/verification.md` before final validation;
- `references/email-spec.md` only when email is requested.

The monthly output inherits Pipeline C's
`daily-news-intelligence/references/language-spec.md` and `output-spec.md`.

## Custom-Agent Dispatch Rule

For every agent stage:

1. Select the exact namespaced role specified below; `task_name` is only a label.
2. Use `fork_turns="none"`.
3. Let the TOML role supply model and reasoning effort.
4. Pass absolute `plugin_root` and `skill_root` in every prompt.
5. Pass upstream output verbatim or by the exact immutable file path specified.
6. Capture and validate the result and required file, then call `close_agent`.
7. Close all agents in a parallel group before starting the next stage. Close a
   failed or schema-invalid attempt before retrying it once.

If exact custom-role selection, `fork_turns="none"`, or `close_agent` is
unavailable, halt. Never fall back to generic agents or inline TOML instructions.

## Workflow

### 1. Resolve Scope and Output

Parse `langs = lang.split("+")`, preserve order, and derive `primary_lang`.
Resolve the active categories from Pipeline C:

```text
[econ, politics, tech, society]
++ [china_nexus only when country == China]
++ [ipo_ma, other]
```

Derive standard `country_display` values for `en`, `zh`, and `ja`, even when a
language is not requested; the collector needs them for safe fallback. Derive
the month display, filenames, and coverage-note language from
`references/output-overrides.md`.

Expand `~`, replace `{month}`, create `OUT_DIR` and `OUT_DIR/audit`, and set:

```text
SOURCE_INDEX=$OUT_DIR/audit/source-index-{country_slug}-{month}.json
CURATOR_AUDIT=$OUT_DIR/audit/curator-bundle-{country_slug}-{month}.txt
VERIFIER_AUDIT=$OUT_DIR/audit/verifier-report-{country_slug}-{month}.txt
MANIFEST=$OUT_DIR/audit/fact-manifest-{country_slug}-{month}.yaml
```

Use `apply_patch` for every persistent JSON, text, YAML, and Markdown artifact.
Do not write audit artifacts with `.md`.

### 2. Build the Immutable Source Index

Run:

```bash
python3 "$SKILL_ROOT/scripts/collect-monthly-reports.py" \
  --country "$COUNTRY" \
  --month "$MONTH" \
  --source-dir "$SOURCE_DIR" \
  --source-lang "$SOURCE_LANG" \
  --preferred-lang "$PRIMARY_LANG" \
  --country-alias "en=$COUNTRY_DISPLAY_EN" \
  --country-alias "zh=$COUNTRY_DISPLAY_ZH" \
  --country-alias "ja=$COUNTRY_DISPLAY_JA" \
  --as-of "$AS_OF"
```

Capture stdout without shell redirection. Use `apply_patch` to persist it
byte-for-byte at `SOURCE_INDEX`. The collector reads top-level final Markdown
only, selects at most one language version per date, validates H1/category
structure, parses story bodies and APA references, records file hashes, and
reports missing dates.

Stop when the collector fails or `counts.reports == 0`. If
`require_complete_month=true`, stop unless `coverage.coverage_complete=true`.
Otherwise continue and require the final localized coverage note. Never interpret
a missing report as evidence that no news occurred.

### 3. Curate Each Category

Launch one `sci-research-monthly-curator` per active category concurrently. Pass:

- `source_index_path`;
- exactly one category ID;
- `country`, `month`, and `stories_per_category`;
- absolute runtime paths.

Each Curator reads only its category's source-index stories, clusters the same
event across dates, and returns `references/schemas.md` § Category Curator
Output. It may return fewer primaries and up to two alternates. It never writes a
file or uses the web.

Validate status, counts, category, ID existence, one-to-five evidence IDs per
cluster, and absence of duplicate IDs within a cluster. Retry an invalid category
once after closing it.

Mechanically build the Curator Bundle in active-category order without rewriting
agent text. Use `apply_patch` to save the exact bundle to `CURATOR_AUDIT`, then
close every Curator.

### 4. Verify Monthly Selection

Launch `sci-research-monthly-verifier` once with:

- Curator Bundle verbatim;
- `source_index_path`;
- `country`, `month`, active categories, and target count;
- absolute runtime paths.

The Verifier resolves cross-category duplicates, promotes qualified alternates
when needed, fixes final routing, and emits the Monthly Verifier Output schema.
It cannot introduce a source ID absent from the index.

Validate every active category, final count, ID existence, evidence-set size,
and global uniqueness of evidence IDs. Retry once after closing an invalid
attempt. Save the complete output verbatim to `VERIFIER_AUDIT` with
`apply_patch`, then close the Verifier.

### 5. Extract Locked Facts

Launch `sci-research-monthly-fact-extractor` once with the complete Verifier
output verbatim, `source_index_path`, `manifest_path`, and runtime paths. It
writes the YAML schema from `references/schemas.md` using `apply_patch`.

Validate that every final monthly story appears once, evidence IDs match the
Verifier exactly, facts trace to those source blocks, and references equal the
deduplicated URL union from those blocks. Close the Fact Extractor only after the
manifest is valid.

### 6. Write and Edit Per Language

Launch one `sci-research-monthly-writer` per requested language concurrently.
Pass each Writer a single language token, its `out_md`, the Verifier output
verbatim, `source_index_path`, `manifest_path`, coverage data, target count,
country/month displays, and runtime paths.

Each Writer uses `apply_patch` to create one Markdown report matching Pipeline C
plus the explicit monthly overrides. It cannot search or open URLs.

After all Writers finish and their files exist, close them. Then launch one
`sci-research-monthly-editor` per language concurrently with the same evidence
plus `writer_md_path`. Editors run five in-place passes using only `apply_patch`
and the local evidence; they never use the web. Close them after validation.

### 7. Validate and Export

For every language, run:

```bash
node "$PLUGIN_ROOT/scripts/hooks/monthly-news-format-check.js" --file "$OUT_MD"
pandoc "$OUT_MD" -o "$OUT_DOCX"
```

Hard-stop before pandoc when the format gate fails. Confirm Markdown and DOCX
exist, story/category counts match the Verifier, URLs match the Manifest, and
current-month coverage language uses `as_of`.

### 8. Optional Email

Do nothing when `email` is absent. When explicitly requested, follow
`references/email-spec.md` and call only
`plugin_root/scripts/send-report-email.py`. Use one email for bilingual output.
When `email_attach=none`, omit `--attach`. Email failure never deletes or changes
local reports.

## Completion Report

Report:

- requested country, month, and language(s);
- accepted report count, effective period, and missing-date count;
- final story count and per-category counts;
- absolute Markdown/DOCX paths;
- audit paths;
- email result only when requested.
