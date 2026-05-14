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
| `references_marker` | `**References**` | `**References**` | `**References**` |
| `gap_note` | `*Note: only N story/stories met T1-T4 standards for this category today.*` | `*注：本分类当日仅检索到 N 条符合 T1-T4 标准的新闻。*` | `*注：このカテゴリで本日 T1-T4 基準を満たした記事は N 件のみでした。*` |
| `quote_marks` | `""` (U+0022) | `""` (U+201C / U+201D) | `「」` (U+300C / U+300D) |

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

**Never use the raw `--country` input value as the filename slug.** The country segment of the filename is `country_display` (rendered in the target `lang`), not the input string. Common failure modes and the correct output:

| Input | ❌ Wrong (raw slug) | ✅ Correct (`country_display`) |
|---|---|---|
| `--country "China" --lang zh` | `china-2026-04-21.md` | `中国每日热点新闻-2026-04-21.md` |
| `--country "South Korea" --lang zh` | `south-korea-2026-04-21.md` | `韩国每日热点新闻-2026-04-21.md` |
| `--country "Germany" --lang ja` | `germany-2026-04-21.docx` | `ドイツデイリーニュース-2026-04-21.docx` |

If `lang` is `zh` or `ja` and the resolved filename contains only ASCII letters in the country segment, the translation step was skipped — regenerate before writing.

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

## Canonical Quote Marks

Body prose uses exactly one quote-mark style per `lang`. Mixed styles or wrong-language chars are blocked by `scripts/hooks/daily-news-format-check.js`.

| lang | Open | Close | Codepoints |
|---|---|---|---|
| `zh` | `"` | `"` | U+201C / U+201D |
| `en` | `"` | `"` | U+0022 / U+0022 |
| `ja` | `「` | `」` | U+300C / U+300D |

This table is authoritative. The `quote_marks` row in the Localisation Table above mirrors it; if they ever disagree, this table wins. APA reference lines, URLs, fenced code blocks, and inline code spans are exempt from the canonical-char rule.

Rationale: `ja` uses corner brackets because Japanese newsroom convention treats `「」` as the default for direct quotation. Forcing ASCII `""` in Japanese prose reads as a foreign artifact. `zh` uses curly because standard Chinese newsroom practice; ASCII `""` in Chinese prose is a typographic error. `en` uses ASCII as the simplest interoperable form (avoids curly-quote substitution drift across editors and fonts).

## Title Length Rules

- The H1 is fixed to `h1_pattern` for the chosen language. Do not add subtitles, qualifiers, or parenthetical context.
- Story titles read as newsroom headlines:
  - `lang=zh` or `lang=ja`: 12-22 CJK characters, single line, no terminal punctuation.
  - `lang=en`: 8-16 words, single line, no terminal punctuation.
- Do not compress the body into the title. Detail lives in the body paragraph(s) that follow the `### title` line directly (no `**摘要**` / `**Summary**` / `**要約**` marker is used).

## Writing Standard

The goal is a brief that reads like a tight, in-medias-res news piece in `lang` — short, fluid, opinion-free, packed with facts that matter. The full writing standard (in medias res / depth over breadth / 干练 / background context / quote handling) lives in `agents/daily-news-writer.md` § Writing Standard. The items below are the language-specific conventions only.

### Story body (between `### title` and `**References**`)

- Body prose follows `### title` directly with one blank line between. **No `**摘要**` / `**Summary**` / `**要約**` / `**分析**` / `**Analysis**` marker is used** — these markers are prohibited and the format-check hook will block any output containing them.
- **No fixed paragraph count** — let the story decide its own length and structure. Use paragraph breaks as a tool for clarity: at narrative shifts (e.g. disclosure → market reaction), when introducing background context, when separating multi-party reactions. A simple announcement may need just one paragraph; a complex story with rich historical background may need three or four.
- Open in medias res with a concrete fact (number / action / named person doing something). Close on a substantive fact, never a wrap-up ("折射出", "凸显了", "标志着", "this signals…").
- Be specific about numbers, names, titles, dates, and the substance of any quote you keep — these must come from a verifiable source (Verifier KEEP set for Lead facts; verifiable search result for background context). The prose around them is the Writer's own.
- Quote sparingly. Include a direct quote only when the speaker's exact words carry meaning the paraphrase would lose; otherwise summarise and attribute.

### Global tone

- Explanatory and direct, testable against the cited URL.
- No event merging. Each story tracks a single event thread.
- No filler. If the category finishes with two stories, stop at two — do not inflate.

### Native-Language Composition

Write as a journalist of the target language would write — not as a translator. Apply the newsroom conventions of `lang` for quote marks, transliteration of foreign names, headline punctuation, sentence rhythm, paragraph breaks, and idiomatic phrasing. The English bundle is fact source, not draft template; do not preserve its sentence shape.

Goals (apply your own judgement on how to achieve them in `lang`):

- **Easy to read**: short sentences, clear logic, no jargon the reader doesn't need.
- **Logical clarity**: a reader of `lang` should be able to follow the event, the actors, the numbers, and the consequence without re-reading.
- **Native rhythm**: punctuation, clause length, and paragraph breaks follow that language's conventions, not English ones.
- **Native conventions**: quote marks, name transliteration, time formats, official titles, and institution name forms all follow that language's standard newsroom practice.
- **No translationese**: if your output, when reverse-translated, would reproduce the English sentence word-for-word, rewrite it.
