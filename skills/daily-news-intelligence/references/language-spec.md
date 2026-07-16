# Language Spec — Localisation Table, Language Rules, Title Length, Writing Standard

Loaded by the Writer. Not needed by Scanner or Verifier.

## Localisation Table

Target-language tokens used by the Writer. Scanner and Verifier output stays English in all cases.

| Token | `lang=en` | `lang=zh` | `lang=ja` |
|-------|-----------|-----------|-----------|
| `title_label` | `Daily News Intelligence` | `每日热点新闻` | `デイリーニュース` |
| `h1_pattern` | `# {country_display} Daily News Intelligence — {date_display}` | `# {country_display}每日热点新闻 — {date_display}` | `# {country_display}デイリーニュース — {date_display}` |
| `references_marker` | `**References**` | `**References**` | `**References**` |
| `gap_note` | `*Note: only N credible, date-verified story/stories were available for this category today.*` | `*注：本分类当日仅检索到 N 条来源可信且日期经核验的新闻。*` | `*注：このカテゴリで本日確認できた、信頼でき日付検証済みの記事は N 件のみでした。*` |
| `quote_marks` | `""` (U+0022) | `""` (U+201C / U+201D) | `「」` (U+300C / U+300D) |

Section H2 headings are **not** Localisation tokens — they are composed at render time from the **Category Catalog** below, because the active category set and its numbering depend on `country`.

## Category Catalog & Selection

The report's H2 sections are **not** a fixed list. They are derived from `country` at render time. This section is the **single source of truth** for category identity, naming, ordering, and numbering. Scanner, Verifier, Writer, and the email body all resolve categories through this catalog.

### Catalog (stable IDs + target-language names)

Names below are **bare** — they carry no leading number. The number is positional and assigned by the selection rule, not stored here.

| `id` | `lang=en` | `lang=zh` | `lang=ja` |
|---|---|---|---|
| `econ` | Economy & Markets | 经济与市场 | 経済と市場 |
| `politics` | Politics & Diplomacy | 政治与外交 | 政治と外交 |
| `tech` | Technology & Industry | 科技与产业 | テクノロジーと産業 |
| `society` | Society & Livelihood | 社会与民生 | 社会と生活 |
| `china_nexus` | China-Nexus Finance & Investment | 海外涉华财经 | 海外の対中経済・投資 |
| `ipo_ma` | Corporate IPO & M&A | 企业IPO与并购 | 企業のIPO・M&A |
| `other` | Other Notable Events | 其他重要事件 | その他の重要事項 |

### Selection rule (depends on `country`)

```
active(country) = [econ, politics, tech, society]
                  ++ (country == China ? [china_nexus] : [])
                  ++ [ipo_ma, other]
```

- **Non-China report** → 6 categories: `econ, politics, tech, society, ipo_ma, other`.
- **China report** → 7 categories: `econ, politics, tech, society, china_nexus, ipo_ma, other`.

`china_nexus` appears **only** in a `--country China` report. `ipo_ma` appears in **every** report (always, regardless of country). `other` is always the final catch-all. Scanner receives only the one-line discovery directions in its TOML; Verifier applies final eligibility and the `china_nexus`↔`ipo_ma` routing tie-break from `references/rubric.md` § Conditional and Topical Categories. This file owns only identity, naming, order, and numbering.

### H2 numbering convention

The H2 line is composed as `## ` + position number + separator + bare name, where the position number is the 1-based index of the category in `active(country)`:

| `lang` | Number form | Separator | Example (position 5) |
|---|---|---|---|
| `zh` | CJK numerals `一 二 三 四 五 六 七` | `、` (no space) | `## 五、海外涉华财经` |
| `en` | Arabic `1`–`7` | `. ` (period + ASCII space) | `## 5. China-Nexus Finance & Investment` |
| `ja` | Arabic `1`–`7` | `. ` (period + ASCII space) | `## 5. 海外の対中経済・投資` |

Resulting H2 sequence:

- **China, `lang=zh`**: `## 一、经济与市场` · `## 二、政治与外交` · `## 三、科技与产业` · `## 四、社会与民生` · `## 五、海外涉华财经` · `## 六、企业IPO与并购` · `## 七、其他重要事件`
- **Japan (or any non-China), `lang=zh`**: `## 一、经济与市场` · `## 二、政治与外交` · `## 三、科技与产业` · `## 四、社会与民生` · `## 五、企业IPO与并购` · `## 六、其他重要事件`
- **China, `lang=en`**: `## 1. Economy & Markets` … `## 5. China-Nexus Finance & Investment` · `## 6. Corporate IPO & M&A` · `## 7. Other Notable Events`

The same category may carry a different number across countries (`ipo_ma` is `## 5.` for Japan but `## 6.` for China). This is expected — number follows position, not identity.

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

## Bilingual Mode (multi-lang `--lang`)

`--lang` accepts a **single language** (`zh` / `en` / `ja`) — the legacy mode — **OR** a **two-language combination** joined by `+` (`zh+en`, `en+zh`, `zh+ja`, `ja+zh`, `en+ja`, `ja+en`) — the bilingual mode introduced in 1.18.0. Three-language combos are NOT supported in 1.18.0.

### Parsing

```
langs = lang.split('+')                       # e.g. "zh+en" → ["zh", "en"]
primary_lang   = langs[0]                     # drives subject + email-body lead section
secondary_lang = langs[1] if len(langs) > 1 else None
is_bilingual   = len(langs) == 2
```

The **primary language is the first token**. `zh+en` and `en+zh` are distinct intents: same files produced, but the subject and email-body lead change.

### Derived fields per lang

In bilingual mode, the orchestrator computes every per-lang derived field **once per lang**:

| Per-lang field | Source |
|---|---|
| `country_display_{lang}` | the Localisation rule above applied with `lang` |
| `date_display_{lang}` | the Localisation rule above applied with `lang` |
| `out_md_{lang}` | the Filename Pattern above applied with `lang` and `country_display_{lang}` |
| `out_docx_{lang}` | same as `out_md_{lang}` with `.docx` extension |
| `title_label_{lang}` | the Localisation Table token above resolved with `lang` |

`date_en` stays singular (English form is language-agnostic; Scanner / Verifier / Fact-Extractor use it regardless of `--lang`).

### Concrete example (`--country "Japan" --date 2026-05-21 --lang zh+en`)

```
primary_lang        = zh
secondary_lang      = en
is_bilingual        = true

country_display_zh  = 日本
country_display_en  = Japan
date_display_zh     = 2026年5月21日
date_display_en     = May 21, 2026

out_md_zh           = {out_dir}日本每日热点新闻-2026-05-21.md
out_docx_zh         = {out_dir}日本每日热点新闻-2026-05-21.docx
out_md_en           = {out_dir}Japan-daily-news-2026-05-21.md
out_docx_en         = {out_dir}Japan-daily-news-2026-05-21.docx
```

### Pipeline behaviour

- **Upstream (category Scanner fan-out / Verifier / Fact-Extractor)**: the complete Scanner fan-out runs **once per report** regardless of `is_bilingual`, followed by one Verifier and one Fact-Extractor. These stages are English language-agnostic; their output is the same for `zh` / `en` / `ja` / `zh+en`.
- **Per-lang (Writer / Editor / pandoc)**: fans out **once per lang** in `langs` order. The orchestrator invokes the Writer subagent for each lang separately, then Editor for each lang separately, then pandoc for each lang separately. Each Writer/Editor invocation still sees a single `lang` — the agents themselves are unchanged.
- **Email (Step 10)**: collects every per-lang file into a single email per § email-spec.md § Bilingual Subject + Body Templates.
- **Self-check (filename)**: the rule `lang is zh or ja and country segment is ASCII` is checked **per generated file**, not on the combined `--lang` string.

### Backward compatibility

Single-lang `--lang zh` / `en` / `ja` behaviour is preserved unchanged: `is_bilingual` is `false`, only one Writer / Editor / pandoc cycle runs, the email body uses the existing single-lang template.

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
- Fact Manifest values lock factual identity and meaning, not English spelling. Localize weekdays, dates, times, currencies, titles, people, institutions, and products into the standard form for `lang` while preserving the same fact. Do not add an English parenthetical solely to reproduce a Manifest value.

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
- Story titles are single-line newsroom headlines without terminal punctuation. Let the event determine the natural length; clarity and native phrasing matter more than a fixed character or word count.
- Do not compress the body into the title. Detail lives in the body paragraph(s) that follow the `### title` line directly (no `**摘要**` / `**Summary**` / `**要約**` marker is used).

## Body Length Guidance

Use the following as planning targets, not validity bands:

| `lang` | Typical target | Unit |
|---|---:|---|
| `en` | about 300 | English words |
| `zh` | about 500 | Unicode Han characters |
| `ja` | story-dependent | — |

When measuring, count only the story body between its `### <title>` and `**References**` marker. Exclude the title, category headings, References lines, URLs, separators, gap notes, and all other document structure.

- **English word count**: count ASCII alphanumeric lexical tokens. Internal apostrophes or hyphens and a decimal or currency-number suffix do not split a token (`central-bank`, `investor's`, `3.5`, and `US$3.5` each count as one word).
- **Chinese character count**: count only characters with Unicode Script property `Han`. Punctuation, Arabic numerals, Latin letters, whitespace, and Markdown syntax do not count.
- A simple event may be shorter; a complex event may be longer. Completeness, relevance, and natural pacing decide the final length.
- Never add background, repetition, generic significance claims, or source-language glosses to reach a target.
- Never cut necessary explanation or distort a fact to reduce a count.
- The format hook may report length statistics, but length alone does not fail export or email.
- Paragraph count remains flexible in all languages.

## Writing Standard

The goal is concise, complete, opinion-free newsroom writing that feels originally composed in `lang`. The Writer TOML defines the operative editorial standard; the rules below keep language and formatting conventions consistent without forcing every event into one narrative template.

### Story body (between `### title` and `**References**`)

- Body prose follows `### title` directly with one blank line between. **No `**摘要**` / `**Summary**` / `**要約**` / `**分析**` / `**Analysis**` marker is used** — these markers are prohibited and the format-check hook reports any output containing them after the edit.
- **No fixed paragraph count** — let the story decide its own length and structure. Use paragraph breaks as a tool for clarity: at narrative shifts (e.g. disclosure → market reaction), when introducing background context, when separating multi-party reactions. A simple announcement may need just one paragraph; a complex story with rich historical background may need three or four.
- Prefer a direct news lead, but let the event determine the most natural opening and ending. Avoid empty setup and formulaic significance conclusions such as "折射出", "凸显了", "标志着", or "this signals..." when they add no information.
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
