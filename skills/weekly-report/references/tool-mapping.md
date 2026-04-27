# Tool Mapping — Weekly Report

Section-by-section data sources. Each Stage B subprocess emits one JSON document; the Writer consumes the bundle as a whole.

| Section | Country/Block | Primary script | Output JSON `section` | Source label in tables |
|---|---|---|---|---|
| Market event | All | `collect_weekly_news.py` | `events_by_country` | `[Sn]` registry from MD references |
| Money Market | USD / EUR / GBP | `fred_money_market.py` | `money_market` | `FRED` |
| Fixed Income | US (2Y/5Y/10Y/30Y) | `fred_fixed_income.py` → `us_treasuries` | `fixed_income` | `FRED` |
| Fixed Income | UK (yield curve) | `boe_yield_curve.py` | `fixed_income_uk` | `Bank of England (spot curve)` |
| Fixed Income | JP (yield curve) | `boj_yield_curve.py` | `fixed_income_jp` | `Japan MOF (jgbcme.csv)` |
| Fixed Income | KR (ETF proxy) | `yfinance_kr_bond.py` | `fixed_income_kr` | `yfinance ETF proxy` |
| Foreign Exchange | All majors + KRW + CNY | `fred_fx.py` | `foreign_exchange` | `FRED` |
| Commodity | Gold / Silver / WTI | `yfinance_commodities.py` | `commodity` | `Yahoo Finance` |

## Fallback policy

- `fred_fixed_income.py` returns FRED proxies for UK and JP. The Writer **prefers the BOE/BOJ outputs** for UK/JP rows when available; FRED proxies are only used if BOE/BOJ both produce empty `series`.
- If a script's `data_gaps` is non-empty, surface those gaps in the report's `## Data Gaps` section, **not silently in the table**.
- If `collect_weekly_news.py` finds zero events for a country, omit that `### Country` sub-section under Market event and add a `## Data Gaps` line.

## Authentication

- `fred_money_market.py` / `fred_fixed_income.py` / `fred_fx.py` require `FRED_API_KEY` in the env.
- All other scripts use public endpoints; no key required.

## What to NOT call

- ❌ Alpha Vantage MCP (removed by user requirement)
- ❌ FRED commodity series (`GOLDAMGBD228NLBM`, `SLVPRUSD`, `DCOILWTICO`) — superseded by yfinance
- ❌ News scanning agents (`news-scanner`, `news-verifier`) — Market event input comes from already-written daily reports, not fresh scans
