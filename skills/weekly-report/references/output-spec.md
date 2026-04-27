# Output Specification — Weekly Report

The Writer produces **one Markdown file** under `out_md`. The file MUST conform to the schema below; the `weekly-report-format-check.js` hook will block writes that violate the structure.

---

## Top-level structure

```
# {H1 title from language-spec.md}

## {Market event}
### {Country: CN}
- [S1] {Story headline} — {YYYY-MM-DD}: one-paragraph factual summary, then optional analyst quote in 「」.
- [S2] ...
### {Country: US}
- [S3] ...
...

## {Money Market}
{intro paragraph — 2-3 sentences}

| Instrument | Series ID | Start ({start_date}) | End ({end_date}) | Δ (abs) | Δ (%) | Unit | Source |
|---|---|---|---|---|---|---|---|
| USD O/N | SOFR | 5.32 | 5.31 | -0.01 | -0.19% | % | FRED |
| EUR O/N | ECBDFR | ... | ... | ... | ... | % | FRED |
| GBP O/N | IUDSOIA | ... | ... | ... | ... | % | FRED |

{1-2 sentence interpretation, e.g. policy stance / liquidity tone}

## {Fixed Income}

### {Country: US}
| Tenor | Series ID | Start | End | Δ bp | Source |
|---|---|---|---|---|---|
| 2Y | DGS2 | 4.62 | 4.55 | -7 | FRED |
| 10Y | DGS10 | 4.18 | 4.20 | +2 | FRED |
| 30Y | DGS30 | 4.32 | 4.35 | +3 | FRED |

### {Country: UK}
| Tenor | Start | End | Δ bp | Source |
|---|---|---|---|---|
| 2Y | 4.10 | 4.05 | -5 | Bank of England (spot curve) |
| 10Y | 4.32 | 4.30 | -2 | Bank of England (spot curve) |

### {Country: JP}
| Tenor | Start | End | Δ bp | Source |
|---|---|---|---|---|
| 2Y | 0.71 | 0.74 | +3 | Japan MOF (jgbcme.csv) |
| 10Y | 1.43 | 1.48 | +5 | Japan MOF (jgbcme.csv) |

### {Country: KR}
| Instrument | Symbol | Start | End | Δ % | Source |
|---|---|---|---|---|---|
| KR 10Y Treasury (KODEX 148070.KS ETF proxy) | 148070.KS | 106500 | 107065 | +0.53% | yfinance ETF proxy |

> Note: KR row reports ETF closing **price**; bond price moves inversely to yield (price ↑ → yield ↓).

## {Foreign Exchange}
{intro — 1 sentence on USD index direction}

| Pair | Series ID | Start | End | Δ (abs) | Δ (%) | Direction | Source |
|---|---|---|---|---|---|---|---|
| USD broad index | DTWEXBGS | ... | ... | ... | ... | ▲/▼/→ | FRED |
| EURUSD | DEXUSEU | ... | ... | ... | ... | ▲/▼/→ | FRED |
| GBPUSD | DEXUSUK | ... | ... | ... | ... | ▲/▼/→ | FRED |
| USDJPY | DEXJPUS | ... | ... | ... | ... | ▲/▼/→ | FRED |
| USDKRW | DEXKOUS | ... | ... | ... | ... | ▲/▼/→ | FRED |
| USDCNY | DEXCHUS | ... | ... | ... | ... | ▲/▼/→ | FRED |

> Note: DEXUSEU / DEXUSUK are USD-per-foreign (USD ↑ when value ↑). DEXJPUS / DEXKOUS / DEXCHUS are foreign-per-USD (USD ↑ when value ↑). Do not flip pairs.

## {Commodity}

| Instrument | Symbol | Start | End | Δ (abs) | Δ (%) | High | Low | Unit | Source |
|---|---|---|---|---|---|---|---|---|---|
| Gold | GC=F | ... | ... | ... | ... | ... | ... | USD/oz | Yahoo Finance |
| Silver | SI=F | ... | ... | ... | ... | ... | ... | USD/oz | Yahoo Finance |
| WTI Oil | CL=F | ... | ... | ... | ... | ... | ... | USD/bbl | Yahoo Finance |

## {Sources}
- [S1] {Title} ({YYYY-MM-DD}) — {Outlet} — https://...
- [S2] ...
...

## {Data Gaps}   ← only emit when at least one item present
- {country/section}: {reason}
```

---

## Hard rules (enforced by hook)

1. H1 must contain both `start_date` and `end_date` in ISO form.
2. The seven section IDs above must appear in order. `## Data Gaps` may be omitted only when truly empty.
3. Each market-data section (Money Market / Fixed Income / FX / Commodity) must contain at least one Markdown table with a header row.
4. Every market-data table row's `Source` column must reference one of: `FRED`, `Bank of England (spot curve)`, `Japan MOF (jgbcme.csv)`, `yfinance ETF proxy`, `Yahoo Finance`.
5. `[S\d+]` reference tags must appear ONLY inside the Market event section; the data sections never use them. Sources section is the registry.
6. Sources section must contain at least one bullet matching `^- \[S\d+\] .+ \(\d{4}-\d{2}-\d{2}\) — .+ — https?://`.
7. No raw `>` blockquotes outside the explicit "Note:" lines documented above. No global italic citation shortcut. No empty placeholder bullets in Data Gaps.

---

## Soft rules (Writer should follow but hook does not enforce)

- Each Market event country sub-section: **3–6 bullets**, ranked by impact (policy > macro data > corporate). Drop bullets that don't have at least one source.
- Money Market intro: name the policy direction (cut/hold/hike) of the dominant central bank that week.
- FX intro: name the strongest and weakest major vs USD.
- Commodity intro: name the largest weekly mover in absolute % terms.
- Each market-data table: 1-2 sentences of interpretation directly underneath.
- Maximum 3 Data Gap bullets — fold related gaps together.
