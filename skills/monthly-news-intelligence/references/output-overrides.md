# Monthly Output Overrides

The final report inherits the complete structure, category catalog, language
rules, body-length rules, typography rules, and APA reference contract from:

- `plugin_root/skills/daily-news-intelligence/references/language-spec.md`
- `plugin_root/skills/daily-news-intelligence/references/output-spec.md`

Apply only the explicit monthly overrides below. When a rule is not overridden,
the Pipeline C rule remains authoritative.

## H1 and Filename

| Lang | H1 | Markdown filename |
|---|---|---|
| `zh` | `# {country_display}月度热点新闻 — {YYYY年M月}` | `{country_display}月度热点新闻-{YYYY-MM}.md` |
| `en` | `# {country_display} Monthly News Intelligence — {Month YYYY}` | `{country_display}-monthly-news-{YYYY-MM}.md` |
| `ja` | `# {country_display}月間ニュース — {YYYY年M月}` | `{country_display}月間ニュース-{YYYY-MM}.md` |

Use the same filename with `.docx` for the Word export.

## Required Source-Coverage Note

Place exactly one italic source-coverage note after H1 and before the first H2.
State the number of accepted daily reports, the effective `as_of` boundary, and
the count of missing expected dates. Do not imply that missing dates contained no
news.

Examples:

```md
*资料范围：本报告基于2026年7月现有5份英国每日热点新闻，资料截至7月20日；15个应覆盖日期缺少可用日报。*

*Source coverage: this report uses 5 available United Kingdom daily reports for July 2026, through July 20; 15 expected dates had no usable daily report.*

*資料範囲：本レポートは2026年7月20日までの英国デイリーニュース5件に基づきます。対象日のうち15日分は利用可能な日報がありませんでした。*
```

When coverage is complete, replace the missing-date clause with a natural
statement that all expected dates were covered.

## Monthly Category Gap Note

When a category has fewer final stories than `stories_per_category`, close the
last story with its standalone `---` separator and then place one italic note
before the next H2:

| Lang | Pattern |
|---|---|
| `zh` | `*注：本分类本月仅从现有日报中筛选到 N 条符合标准的月度热点新闻。*` |
| `en` | `*Note: only N qualifying monthly top story/stories could be selected from the available daily reports for this category.*` |
| `ja` | `*注：このカテゴリでは、利用可能な日報から月間主要ニュースを N 件のみ選定しました。*` |

Use `N = 0` directly below the category H2 when no story qualifies.

## Story Construction

- Synthesize one final story from the Verifier-selected evidence story IDs.
- Preserve explicit dates because a monthly story may cover several stages.
- Use only facts locked in the Monthly Fact Manifest.
- Do not use WebSearch or open source URLs.
- Include every unique Manifest reference for the story, deduplicated by exact
  URL, in its colocated `**References**` block.
- Renumber all references continuously from `[1]` across the whole document.
- Keep the Pipeline C hard minimum: 400 Unicode Han characters for each Chinese
  story and 250 English words for each English story. Japanese has no fixed
  minimum. Never pad.
- Keep the same H2 category order, `###` story title, prose, References, and
  standalone `---` separators as Pipeline C.

## Bilingual Mode

Run selection and Fact Extraction once. Run Writer, Editor, format validation,
and pandoc once per language. Both language versions must contain the same final
story IDs, category routing, evidence URLs, and factual meaning.
