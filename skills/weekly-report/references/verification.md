# Writer Self-Verification — Weekly Report

Before issuing the `Write` call, the Writer must mentally tick this checklist. The `weekly-report-format-check.js` hook re-checks the file after write and blocks on violations.

## Structure

- [ ] H1 starts with `#` followed by the localised title from `language-spec.md` and contains both `start_date` and `end_date` in `YYYY-MM-DD` form.
- [ ] Six required H2 sections present in order: `Market event` → `Money Market` → `Fixed Income` → `Foreign Exchange` → `Commodity` → `Sources`.
- [ ] `Data Gaps` H2 either omitted entirely OR has at least one substantive bullet.
- [ ] All H2 / H3 strings use the exact localisation from `language-spec.md` (no English fallbacks in zh/ja outputs).

## Tables

- [ ] Money Market: one table with columns Instrument / Series ID / Start / End / Δ / Δ% / Unit / Source.
- [ ] Fixed Income: one H3+table per country present in the data bundle (US, UK, JP, KR at minimum).
- [ ] FX: one table covering at least USD broad index + EURUSD + GBPUSD + USDJPY + USDKRW + USDCNY (when data available).
- [ ] Commodity: one table covering Gold + Silver + WTI Oil.
- [ ] Every Source column entry is one of the labels in `tool-mapping.md`.

## Sources & references

- [ ] `[S1]`, `[S2]`, ... appear ONLY inside the `Market event` section, never in market-data tables.
- [ ] Sources section has continuous numbering starting at S1.
- [ ] Each Sources bullet matches the `[Sn] Title (YYYY-MM-DD) — Outlet — URL` form.
- [ ] No duplicate URLs in Sources.

## Numbers

- [ ] Every Δ% is computed from start/end values in the data bundle (do not invent).
- [ ] Trend icons ▲ / ▼ / → match the sign of Δ.
- [ ] No mixing of yield basis points and percentage points (Fixed Income tables: Δ is in bp; Money Market / FX in %).

## Localisation

- [ ] zh body uses 「」 quotes; en uses `"…"`; ja uses 「」.
- [ ] Country H3 names match the language-spec table for the active `lang`.
- [ ] Tickers / series IDs / URLs left in canonical English form.

## Negative checks

- [ ] No `> blockquote` lines except the documented "Note:" lines under FX and KR tables.
- [ ] No global italic citation lines (`*Source: ...*`).
- [ ] No empty placeholder bullets in Data Gaps (e.g. just `- 数据缺口` or `- TBD`).
- [ ] No surplus H1 lines after the first one.

## Self-correction

If any check fails after writing, re-issue the `Write` call with the corrected content rather than amending via Edit — the hook re-runs only on Write events.
