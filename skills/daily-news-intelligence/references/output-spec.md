# Output Spec — Required Markdown Structure, Syntax Contract, and APA Format

Loaded by the Writer. Not needed by Scanner or Verifier.

## Required Output (Markdown)

Return only the final Markdown report. Use the `h1_pattern` for the target language and the **country-derived active-category H2 headings** in order — 6 for a non-China report, 7 for a China report (which adds `china_nexus` at position 5). Each H2 line is composed (position number + separator + bare name) per `references/language-spec.md` § Category Catalog & Selection — that file is authoritative for category identity, naming, order, and numbering.

Each story must use this exact block structure (`{references_marker}` comes from the Localisation Table; narrative content is in the target language):

```md
### <Story title in target language>

<Body in natural target-language newsroom prose. Preserve the Fact Manifest's factual meaning while localizing names, titles, dates, times, currencies, and other expressions normally; do not retain English strings or add English parentheticals merely to satisfy literal matching. Follow `references/language-spec.md` § Body Length Standard: every `en` body has at least 250 English words and every `zh` body has at least 400 Unicode Han characters; `ja` has no fixed floor and no language has a maximum. Explain the event with relevant sourced detail and context rather than padding or formulaic prose. When the supplied material cannot support a complete body above the floor, open the Lead and relevant corroborating URLs, then use supplemental WebSearch only if those pages remain insufficient. Cite every opened source whose facts enter the body. Every factual claim must trace to the Verifier bundle, Fact Manifest, or an opened source. Wrap direct quotations with the language's canonical `quote_marks` and preserve attribution.>

{references_marker}

[N] <Surname>, <Initial>. (<Year>, <Month> <Day>). <Original English title>. <Outlet name>. <full https URL>
[N+1] <second reference if the story has corroborating sources, same APA format>

---
```

Body prose follows `### title` directly (with one blank line between). **There is no `**摘要**` / `**Summary**` / `**要約**` marker, and no `**分析**` / `**Analysis**` marker.** Both are prohibited — see § Prohibited Markers below.

Between consecutive stories use a standalone `---` separator line.
Do not emit a trailing global references or sources section.

**`[N]` numbering rule**: every reference line starts with `[N] ` where `N` runs **continuously from 1 across the entire document**, not per-story. The first reference of story 1 is `[1]`; if story 1 has 3 references, story 2's first reference is `[4]`. Multiple references per story are allowed and common when the Verifier delivers corroborating or claim-complementary sources.

**Search URLs that supplied a fact in body MUST appear** in the references block. Open the existing Lead and relevant corroborating URLs when the supplied excerpts cannot support a substantive body above the hard floor. Supplemental search is used only when those pages still do not provide enough relevant, verifiable material. Open every result whose facts enter the body. The references block contains: Verifier KEEP URLs (Lead + every Corroborated by URL) ∪ {search URLs whose content backed a body fact}.

If a category has fewer kept stories than `min_per_category` after Verifier Coverage Review, keep the section heading and append exactly one italic `gap_note` line before the next `---`.

## Markdown Syntax Contract

Markdown heading markers are syntax tokens, not natural language.

- The tokens `#`, `##`, `###`, and emphasis markers `**` are never translated, removed, merged, or restyled.
- Every heading token must be followed by exactly one ASCII space.
- The H1 line must match `h1_pattern` exactly for the chosen language — single ASCII space after `#`, single em-spaced ` — ` between label and date.
- Every section heading line must match its composed value from `references/language-spec.md` § Category Catalog & Selection exactly for the chosen language — the position number, separator, and bare name are all part of the heading text.
- Every story heading line must be exactly `### <story title>`.
- No prose, emphasis, URL, or citation may appear on the same line as any heading.
- **Body paragraph(s) start on the line immediately after `### title`** (with one blank line between — no marker line in between). The `references_marker` (`**References**`) line precedes the references block.
- URLs must appear verbatim in the `References` line, never wrapped as `[text](url)`.

## Prohibited Markers

The following markers must NOT appear anywhere in the output:

| Marker | Why prohibited |
|---|---|
| `**摘要**` | Body comes directly after `### title` — no body label needed |
| `**Summary**` | Same as above |
| `**要約**` | Same as above |
| `**分析**` | Analysis block was removed in the new structure — body carries any "so what" inline |
| `**Analysis**` | Same as above |

The PostToolUse hook `scripts/hooks/daily-news-format-check.js` reports these defects after an `apply_patch`; its direct `--file` mode blocks export and email until they are corrected.

## Reference Format Rules (CRITICAL)

Every story MUST end with the `{references_marker}` block containing **one or more** APA 7th formatted references with bare URLs, each prefixed with `[N] ` where `N` is a globally continuous counter across the entire document. The following alternative formats are **strictly prohibited**:

| Prohibited format | Why it's wrong |
|---|---|
| `[来源名](https://...)` | Markdown hyperlink — URL hidden in rendered output, not copyable |
| `来源：\n- 来源名 https://...` | Bullet-list style — not APA format, no date/title metadata |
| `（来源：来源名 https://...）` | Inline parenthetical — breaks story block structure |
| `（*Japan Times*，2026年4月15日）` with refs at bottom | In-text citation + global ref list — user must scroll to find URL |
| `来源：Bloomberg https://...` (indented) | Missing APA fields, breaks block structure |
| `## 参考文献` / `## References` / `## Sources` section at end | **Global** ref list prohibited — refs must be per-story, not aggregated at the bottom |
| `> **来源**: Author. (Year). Title. Outlet. URL` blockquote | Blockquote replacement for `**References**` block — not a recognised format |
| `*来源：Author (Year); Author (Year)*` italic in-text | Shortened in-text citation with a separate global URL list — reader cannot find URL without scrolling |
| Reference line without `[N]` prefix | Mandatory numbering missing — breaks continuous-counter contract |
| Reference line without a bare `https://` URL | Every reference must carry a verifiable URL |

The ONLY acceptable format is the numbered APA 7th reference(s) colocated with each story:

```md
**References**

[1] Reuters. (2026, April 16). Article title here. Reuters. https://www.reuters.com/...
[2] Bloomberg. (2026, April 16). Corroborating title. Bloomberg. https://www.bloomberg.com/...
```

### Invalid examples

```md
#Japan Daily News Intelligence — April 14, 2026
##1. Economy & Markets###BoJ holds rates
**Summary**The Bank of Japan held…
**摘要**
日本央行……
**分析**
分析师指出……
**References** Reuters (2026, April 14). Title. https://…
[Reuters: BoJ holds rates](https://example.com)
来源：
- Reuters https://www.reuters.com/...
（来源：[Reuters](https://www.reuters.com/...)）
```

Every line above is a violation — `**Summary**` / `**摘要**` / `**分析**` markers are prohibited; body must follow `### title` directly with no marker.

### Valid example (`lang=en`)

```md
# Japan Daily News Intelligence — April 14, 2026

## 1. Economy & Markets

### Bank of Japan holds benchmark rate at 0.5%

The Bank of Japan held its policy rate at 0.5% for the third consecutive meeting Tuesday, governor Kazuo Ueda told reporters at an April 14 press conference. "We will adjust monetary policy if needed," Ueda said, brushing off market pressure for an earlier hike with the yen near 34-year lows. Mizuho Securities chief economist Shunsuke Kobayashi described the decision as "confirmation of the central bank's confidence in the inflation path." USD/JPY climbed 80 bps within 30 minutes of the announcement, closing at 153.20.

**References**

[1] Reuters. (2026, April 14). Bank of Japan keeps benchmark rate at 0.5%. Reuters. https://www.reuters.com/...
[2] Bloomberg. (2026, April 14). BOJ holds rates, signals patience on hikes. Bloomberg. https://www.bloomberg.com/...

---
```

### Valid example (`lang=zh`)

```md
# 日本每日热点新闻 — 2026年4月14日

## 一、经济与市场

### 日本央行连续第三次维持基准利率 0.5%

日本央行 4 月 14 日宣布连续第三次将基准利率维持在 0.5%，行长植田和男在记者会上称“我们将在必要时调整货币政策”。决议公布后 30 分钟内，美元兑日元走高 80 个基点，收于 153.20，逼近 34 年低位。瑞穗证券首席经济学家小林俊介评价此次决议“确认了央行对通胀路径的信心”。

**References**

[3] Reuters. (2026, April 14). Bank of Japan keeps benchmark rate at 0.5%. Reuters. https://www.reuters.com/...
[4] Bloomberg. (2026, April 14). BOJ holds rates, signals patience on hikes. Bloomberg. https://www.bloomberg.com/...

---
```

(Note: `[3]`/`[4]` in the `lang=zh` example assumes the previous `lang=en` story consumed `[1]`/`[2]`. `[N]` is a **document-wide** continuous counter, never reset per story or per language. Body prose carries the news directly with no `**摘要**` / `**分析**` marker.)

## Cited Search URLs

When Writer uses supplemental WebSearch for necessary context, it opens every result whose facts enter the body. **Any URL that supplied a fact written in body prose is a first-class citation** and appears in the story's `**References**` block alongside Verifier KEEP URLs:

- One APA reference line per cited search URL, with the next continuous `[N]` counter.
- Outlet name = the URL's actual publisher.
- Title = the source page's `<title>` or H1, preserved in original English.
- Date = the source publication date.

This is **mandatory**. Citing background facts in body without listing the supporting URL in References creates a reference gap visible to readers checking sources. Writer is responsible at write time; Editor verifies at edit time.

Verifier-delivered URLs (Lead + every Corroborated by URL) always appear in References regardless of whether Writer cites them in body — they preserve the report's evidence trail.

The ONLY URLs that may be opened and NOT cited are ones that returned irrelevant content or whose facts duplicate something already cited. When in doubt, cite.

## APA 7th Reference Format

- Pattern: `[N] <Author surname>, <Given-name initials>. (<Year>, <Month> <Day>). <Original English title>. <Outlet>. <URL>`
- Reference lines are always rendered in English regardless of `lang` (only the leading `[N]` prefix is language-neutral).
- When the byline is an organisation (Reuters, Bloomberg, GOV.UK, ECB), write the organisation name in place of the author.
- The title stays in the original English — do not translate.
- The date segment uses English month names, e.g. `(2026, April 14)`.
- URLs are bare — never wrap in `[text](url)`.
- One or more references per story, colocated in the story's references block. Do NOT emit a global sources list.
- `[N]` prefix is mandatory, counter runs continuously from `[1]` at the document's first reference through `[total]` at the last, regardless of story boundaries.
- **References = Verifier KEEP URLs ∪ {search URLs that supplied a fact in body}**. Every Verifier URL (Lead + every Corroborated by URL) MUST appear. Every search URL whose content backed a body fact MUST appear with proper APA and continuous `[N]`. URLs opened but unused are NOT added.

## Self-Check Checksum (Writer must verify before emitting)

Before calling `apply_patch`, count your own output:

1. `count(### ) == count(**References**)` — one `###` and one `**References**` per story.
2. **No `**摘要**` / `**Summary**` / `**要約**` / `**分析**` / `**Analysis**` markers anywhere** — body prose follows `### title` directly.
3. `[N]` runs continuously from 1 to the total number of reference lines — no gaps, no duplicates, no reset per story.
4. Every reference line contains a bare `https://` URL.
5. No `^## 参考文献$` / `^## References$` / `^## Sources$` H2 heading anywhere.
6. No `^> **来源**` / `^> **Source**` blockquote patterns.
7. No `^*\s*来源[:：]` / `^*\s*Sources?[:：]` italic in-text citation patterns.
8. Every URL in the references block is either a Verifier KEEP URL (Lead or Corroborated by) OR a search URL that supplied a fact in body. URLs that were opened but whose content wasn't used MUST NOT appear; URLs whose content was used MUST appear.
9. Every `en` story body contains at least 250 English words and every `zh` story body contains at least 400 Unicode Han characters, counted per `references/language-spec.md` § Body Length Standard. `ja` has no fixed minimum. There is no maximum. Never pad, distort, or repeat content to meet the floor.

If any check fails, regenerate. A PostToolUse hook (`scripts/hooks/daily-news-format-check.js`) checks items 1, 2, 3, 4, 5, 6, and 7 mechanically after each edit and injects correction context into the task. Because PostToolUse runs after the edit, correct the resulting file before continuing. The orchestrator's direct `--file` check exits 2 on a violation and hard-stops export or email.

Item 9 is hook-enforced per story. The hook reports the story title, actual count, and minimum; direct mode exits 2 when any `en` or `zh` body is below the floor.

**Item 8 is not hook-enforced** — verifying "every URL traces to Verifier KEEP OR backed a body fact" requires the Verifier-KEEP set, which the hook does not have. Item 8 is enforced by the Writer's citation contract and verified by Editor Pass 2.
