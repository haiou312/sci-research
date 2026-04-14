# Language Spec — Localisation Table, Language Rules, Title Length, Writing Standard

Loaded by the Writer. Not needed by Scanner or Verifier.

## Localisation Table

Target-language tokens used by the Writer. Scanner and Verifier output stays English in all cases.

| Token | `lang=en` | `lang=zh` | `lang=ja` |
|-------|-----------|-----------|-----------|
| `title_label` | `Daily News Intelligence` | `每日热点新闻` | `デイリーニュース` |
| `h1_pattern` | `# {country_display} Daily News Intelligence — {date_display}` | `# {country_display}每日热点新闻 — {date_display}` | `# {country_display}デイリーニュース — {date_display}` |
| `section_1` | `## 1. Economy & Markets` | `## 一、经济与市场` | `## 1. 経済と市場` |
| `section_2` | `## 2. Politics & Diplomacy` | `## 二、政治与外交` | `## 2. 政治と外交` |
| `section_3` | `## 3. Technology & Industry` | `## 三、科技与产业` | `## 3. テクノロジーと産業` |
| `section_4` | `## 4. Society & Livelihood` | `## 四、社会与民生` | `## 4. 社会と生活` |
| `section_5` | `## 5. Other Notable Events` | `## 五、其他重要事件` | `## 5. その他の重要事項` |
| `summary_marker` | `**Summary**` | `**摘要**` | `**要約**` |
| `analysis_marker` | `**Analysis**` | `**分析**` | `**分析**` |
| `references_marker` | `**References**` | `**References**` | `**References**` |
| `gap_note` | `*Note: only N story/stories met T1-T4 standards for this category today.*` | `*注：本分类当日仅检索到 N 条符合 T1-T4 标准的新闻。*` | `*注：このカテゴリで本日 T1-T4 基準を満たした記事は N 件のみでした。*` |
| `quote_marks` | `""` | `「」` | `「」` |

## Derived Display Fields

- `date_en` — English display form, e.g. `April 14, 2026`.
- `date_display` — date rendered in the target language. `2026年4月14日` for `lang=zh` and `lang=ja`; `April 14, 2026` for `lang=en`.
- `country_display` — country name in the target language. Examples:
  - `lang=en`: `Japan`, `United Kingdom`, `Germany`, `China`.
  - `lang=zh`: `日本`, `英国`, `德国`, `中国`.
  - `lang=ja`: `日本`, `英国`, `ドイツ`, `中国`.

## Filename Pattern

- `out_md`:
  - `lang=en` → `{out_dir}{country_display}-daily-news-{date}.md`
  - `lang=zh` → `{out_dir}{country_display}每日热点新闻-{date}.md`
  - `lang=ja` → `{out_dir}{country_display}デイリーニュース-{date}.md`
- `out_docx` — same as `out_md` with `.docx` extension.

## Language Rules

- Search queries: English only, regardless of `lang`.
- Scanner output: English raw data, regardless of `lang`.
- Verifier output: English raw data, regardless of `lang`.
- Writer output: rendered in the target language `lang`, with the following kept in original English:
  - URLs, which stay verbatim.
  - Institutional shortforms already recognised in financial press (FTSE 100, BoE, ECB, BoJ, Fed, Nasdaq, S&P 500, Dow Jones).
  - Proper nouns without a widely used target-language form — keep the English form in parentheses after a target-language gloss on first mention.
  - APA 7th reference lines — see `references/output-spec.md`.
- Direct quotations: translate into the target language and wrap with the `quote_marks` for that language; preserve speaker attribution (name + title translated where appropriate).

## Title Length Rules

- The H1 is fixed to `h1_pattern` for the chosen language. Do not add subtitles, qualifiers, or parenthetical context.
- Story titles read as newsroom headlines:
  - `lang=zh` or `lang=ja`: 12-22 CJK characters, single line, no terminal punctuation.
  - `lang=en`: 8-16 words, single line, no terminal punctuation.
- Do not compress the summary into the title. Detail lives in the `summary_marker` block.

## Writing Standard

### `summary_marker` block — pure reporting

- Rewrite the Scanner's factual excerpt into a single flowing paragraph in `lang`.
- Must contain: concrete numbers (amounts, percentages, dates), named officials with titles, at least one direct quote translated into `lang` wrapped with the language's `quote_marks`, and explicit time anchors.
- No speculation, no hedged language ("could", "might"), no Writer-added interpretation.
- Length: 200-300 CJK characters for `zh`/`ja`; 150-220 words for `en`.

### `analysis_marker` block — source-only commentary

- Draw exclusively from the source article's analyst, official, or institutional commentary, as carried verbatim in the Verifier bundle's `Commentary:` field.
- Translate the commentary into `lang`, preserving attribution (name + affiliation) and quotation marks.
- Do NOT synthesize, extrapolate, or introduce your own viewpoint.
- If the Verifier bundle shows `Commentary: No analyst commentary in source`, omit the entire `analysis_marker` block — no placeholder, no "no commentary available".
- Length: 100-200 CJK characters for `zh`/`ja`; 80-150 words for `en`.

### Global tone

- Institutional, declarative, testable against the cited URL.
- No event merging. Each story tracks a single event thread.
- No filler. If the category finishes with two stories, stop at two — do not inflate.
