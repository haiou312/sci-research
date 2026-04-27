# Language Specification — Weekly Report

The weekly report supports three output languages: `zh` (Simplified Chinese), `en` (English), `ja` (Japanese). The Writer must use **exactly one** language for all body content (headings, prose, table headers); only proper nouns, ticker symbols, FRED series IDs, and URLs may stay in their canonical English form regardless of `lang`.

---

## H1 title and filename templates

Substitute `{start_date}` and `{end_date}` in ISO `YYYY-MM-DD` form.

| Lang | H1 title (in body) | Output filename |
|---|---|---|
| `zh` | `# 全球宏观与市场周报（{start_date} 至 {end_date}）` | `全球宏观与市场周报-{start_date}_至_{end_date}.md` |
| `en` | `# Global Macro & Market Weekly Report ({start_date} to {end_date})` | `Global-Macro-Market-Weekly-{start_date}_to_{end_date}.md` |
| `ja` | `# グローバル・マクロ市場週報（{start_date} から {end_date}）` | `グローバル・マクロ市場週報-{start_date}_から_{end_date}.md` |

---

## H2 section headings (fixed order)

The writer MUST emit these seven `## ` sections in this order; `## Data Gaps` is optional (omit if empty):

| Section ID | en | zh | ja |
|---|---|---|---|
| market_event | `Market event` | `市场事件` | `市場イベント` |
| money_market | `Money Market` | `货币市场` | `マネーマーケット` |
| fixed_income | `Fixed Income` | `固定收益` | `債券市場` |
| foreign_exchange | `Foreign Exchange` | `外汇` | `外国為替` |
| commodity | `Commodity` | `大宗商品` | `コモディティ` |
| sources | `Sources` | `来源` | `出典` |
| data_gaps | `Data Gaps` | `数据缺口` | `データギャップ` |

---

## H3 country sub-section headings (Market event + Fixed Income)

Country sub-sections inside `## Market event` and `## Fixed Income` use H3 with the localised country name from this table.

| Code | en | zh | ja |
|---|---|---|---|
| CN | `China` | `中国` | `中国` |
| US | `United States` | `美国` | `米国` |
| UK | `United Kingdom` | `英国` | `英国` |
| EU | `Europe` | `欧洲` | `欧州` |
| JP | `Japan` | `日本` | `日本` |
| KR | `South Korea` | `韩国` | `韓国` |

---

## Body text conventions

- **Quotes**: zh uses 「」; en uses standard `"…"`; ja uses 「」.
- **Numbers**: keep raw figures; localise units only in the unit column header (e.g. zh `单位: 百分点`, ja `単位: %`).
- **Currency symbols**: keep `USD`, `EUR`, `GBP`, `JPY`, `CNY`, `KRW` as-is. Avoid `¥` for both yen and yuan to prevent ambiguity.
- **Trend icons**: use ▲ for up, ▼ for down, → for flat. Same in all three languages.
- **Ticker symbols / series IDs**: keep raw (e.g. `GC=F`, `SOFR`, `DGS10`, `148070.KS`). Do not translate.

---

## Source registry rendering (`## Sources`)

One bullet per unique source in this format (same across languages):

```
- [S1] {Title} ({YYYY-MM-DD}) — {Outlet} — {URL}
```

If multiple stories share a URL, dedupe and keep one entry. Source IDs must be **continuous** starting from `S1` and referenced inline only inside `## Market event` country bullets, **not** inside the four market-data sections (which carry their own source columns).
