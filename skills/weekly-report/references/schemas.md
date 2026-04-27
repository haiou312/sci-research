# Script I/O Schemas — Weekly Report

All scripts emit one JSON document on stdout, exit 0 on success, non-zero with an `{"error": "..."}` envelope on failure.

---

## `collect_weekly_news.py`

```json
{
  "window": {"start_date": "2026-04-09", "end_date": "2026-04-15"},
  "lang": "zh",
  "countries": ["CN", "US", "UK", "EU", "JP", "KR"],
  "news_dir": "/Users/.../Desktop/daily-news-reports",
  "files_consumed": [
    {"path": "...", "filename": "中国每日热点新闻-2026-04-15.md", "date": "2026-04-15", "country": "CN", "country_display": "中国", "lang": "zh"}
  ],
  "events_by_country": {
    "CN": [
      {
        "country": "CN",
        "country_display": "中国",
        "date": "2026-04-15",
        "section_h2": "一、经济与市场",
        "title": "...",
        "summary": "...",
        "analysis": "...",
        "references": [{"raw": "Author. (2026, ...). Title. Outlet. https://...", "url": "https://..."}],
        "source_file": "..."
      }
    ]
  },
  "summary": {"files_count": 5, "events_count": 17, "events_per_country": {"CN": 7, "US": 3, ...}},
  "data_gaps": ["No daily file found for KR on 2026-04-15"],
  "filter": {"economy_only": true}
}
```

## `fred_money_market.py`

```json
{
  "section": "money_market",
  "source": "FRED",
  "window": {"start_date": "...", "end_date": "..."},
  "rows": [
    {
      "instrument": "USD O/N",
      "selected_series_id": "SOFR",
      "data": {"series_id": "SOFR", "meta": {...}, "summary": {...}, "observations": [{"date": "...", "value": 5.31}]},
      "fallback_errors": []
    }
  ],
  "notes": "...",
  "data_gaps": []
}
```

## `fred_fixed_income.py`

```json
{
  "section": "fixed_income",
  "source": "FRED",
  "window": {...},
  "us_treasuries": [{"instrument": "US 2Y", "selected_series_id": "DGS2", "data": {...}, "fallback_errors": []}],
  "uk_gilts": [...],
  "jp_jgbs": [...],
  "notes": "...",
  "data_gaps": []
}
```

## `fred_fx.py`

```json
{
  "section": "foreign_exchange",
  "source": "FRED",
  "window": {...},
  "rows": [{"instrument": "USDKRW", "selected_series_id": "DEXKOUS", "data": {...}, "fallback_errors": []}],
  "notes": "...",
  "data_gaps": []
}
```

## `boe_yield_curve.py` / `boj_yield_curve.py`

```json
{
  "section": "fixed_income_uk",  // or "fixed_income_jp"
  "source": "Bank of England",   // or "Japan Ministry of Finance"
  "window": {...},
  "unit": "percent",
  "tenors": ["2Y", "10Y", "30Y"],
  "row_count": 27,
  "rows": [{"date": "...", "tenor": "10Y", "value": 4.20}],
  "series": [{"tenor": "10Y", "observations": [{"date": "...", "value": 4.20}]}],
  "sources_used": [...],
  "data_gaps": []
}
```

## `yfinance_commodities.py`

```json
{
  "section": "commodity",
  "source": "Yahoo Finance",
  "window": {...},
  "rows": [
    {
      "instrument": "Gold",
      "symbol": "GC=F",
      "unit": "USD/oz",
      "observations": [{"date": "...", "open": ..., "high": ..., "low": ..., "close": ..., "volume": ..., "value": ...}],
      "summary": {"count": 5, "latest_date": "...", "latest_value": ..., "start_value": ..., "change_abs": ..., "change_pct": ...}
    }
  ],
  "data_gaps": []
}
```

## `yfinance_kr_bond.py`

```json
{
  "section": "fixed_income_kr",
  "source": "Yahoo Finance ETF proxy",
  "window": {...},
  "row": {
    "instrument": "KR 10Y Treasury (KODEX 148070.KS ETF proxy)",
    "symbol": "148070.KS",
    "unit": "KRW",
    "observations": [{"date": "...", "close": 107065.0, "value": 107065.0}],
    "summary": {...}
  },
  "notes": "ETF close price; bond price moves inversely to yield (close ↓ → yield ↑).",
  "data_gaps": []
}
```

## Error envelope (any script)

```json
{"error": "...", "hint": "...", "detail": "..."}
```
Non-zero exit code accompanies error output.
