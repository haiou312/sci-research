# Output Spec — Required Markdown Structure, Syntax Contract, and APA Format

Loaded by the Writer. Not needed by Scanner or Verifier.

## Required Output (Markdown)

Return only the final Markdown report. Use the `h1_pattern` for the target language and the five `section_*` H2 headings in the exact order `1 → 5` (see `references/language-spec.md` for the Localisation Table).

Each story must use this exact block structure (markers come from the Localisation Table; narrative content is in the target language):

```md
### <Story title in target language>

{summary_marker}

<Factual paragraph in the target language, 200-300 CJK characters or 150-220 English words. Must embed specific numbers, named officials with titles, direct quotes translated into the target language and wrapped with the target language's quote_marks, and explicit time references. No speculation.>

{analysis_marker}

<Analysis paragraph in the target language, 100-200 CJK characters or 80-150 English words. Must be drawn verbatim from analyst / official / institutional commentary found in the source article. Omit this entire block when the source carries no commentary — never write "no commentary available".>

{references_marker}

<Surname>, <Initial>. (<Year>, <Month> <Day>). <Original English title>. <Outlet name>. <full https URL>

---
```

Between consecutive stories use a standalone `---` separator line.
Do not emit a trailing global references or sources section.

If a category has fewer kept stories than `min_per_category` after the Scanner gap pass, keep the section heading and append exactly one italic `gap_note` line before the next `---`.

## Markdown Syntax Contract

Markdown heading markers are syntax tokens, not natural language.

- The tokens `#`, `##`, `###`, and emphasis markers `**` are never translated, removed, merged, or restyled.
- Every heading token must be followed by exactly one ASCII space.
- The H1 line must match `h1_pattern` exactly for the chosen language — single ASCII space after `#`, single em-spaced ` — ` between label and date.
- Every section heading line must match the chosen language's `section_n` string exactly — numbering and punctuation are part of the heading text.
- Every story heading line must be exactly `### <story title>`.
- No prose, emphasis, URL, or citation may appear on the same line as any heading.
- The `summary_marker`, `analysis_marker`, and `references_marker` each occupy their own line; paragraph body starts on the next line.
- URLs must appear verbatim in the `References` line, never wrapped as `[text](url)`.

### Invalid examples

```md
#Japan Daily News Intelligence — April 14, 2026
##1. Economy & Markets###BoJ holds rates
**Summary**The Bank of Japan held…
**References** Reuters (2026, April 14). Title. https://…
[Reuters: BoJ holds rates](https://example.com)
```

### Valid example (`lang=en`)

```md
# Japan Daily News Intelligence — April 14, 2026

## 1. Economy & Markets

### Bank of Japan holds benchmark rate at 0.5%

**Summary**

Governor Kazuo Ueda confirmed at an April 14 press conference that the Bank of Japan will keep its policy rate unchanged at 0.5%. He said, "We will adjust monetary policy if needed."

**Analysis**

Mizuho Securities chief economist Shunsuke Kobayashi described the decision as "confirmation of the central bank's confidence in the inflation path."

**References**

Reuters. (2026, April 14). Bank of Japan keeps benchmark rate at 0.5%. Reuters. https://www.reuters.com/...

---
```

### Valid example (`lang=zh`)

```md
# 日本每日热点新闻 — 2026年4月14日

## 一、经济与市场

### 日本央行维持基准利率在 0.5%

**摘要**

日本央行行长植田和男在 4 月 14 日的新闻发布会上宣布……「我们将在必要时调整货币政策」。

**分析**

瑞穗证券首席经济学家小林俊介表示，此次决议「确认了央行对通胀路径的信心」……

**References**

Reuters. (2026, April 14). Bank of Japan keeps benchmark rate at 0.5%. Reuters. https://www.reuters.com/...

---
```

## APA 7th Reference Format

- Pattern: `<Author surname>, <Given-name initials>. (<Year>, <Month> <Day>). <Original English title>. <Outlet>. <URL>`
- Reference lines are always rendered in English regardless of `lang`.
- When the byline is an organisation (Reuters, Bloomberg, GOV.UK, ECB), write the organisation name in place of the author.
- The title stays in the original English — do not translate.
- The date segment uses English month names, e.g. `(2026, April 14)`.
- URLs are bare — never wrap in `[text](url)`.
- Exactly one reference per story, colocated in the story's references block. Do not emit a global sources list.
