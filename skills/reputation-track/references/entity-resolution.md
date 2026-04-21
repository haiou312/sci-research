# Entity Resolution — Ticker/Name → Company → Executives

Loaded by the Resolver. Describes how to disambiguate the `--company` input and derive the executive list used for mention-matching in the Scanner.

## Input Handling

The `--company` argument can be:

- **Stock ticker** (regex `^[A-Z0-9.]{1,5}$`) — e.g. `AAPL`, `TSLA`, `005930.KS`, `9984.T`
- **Formal company name** — e.g. `Apple Inc.`, `Sony Group Corporation`
- **Short / ambiguous name** — e.g. `Apple` (could be Apple Inc. vs. private)

## Resolution Steps

### Step 1 — Ticker path

If input matches the ticker regex, resolve via Yahoo Finance:

```
WebFetch https://finance.yahoo.com/quote/<TICKER>
```

Extract:
- Official company name (page header)
- Exchange and listing country
- Confirm primary ticker

If Yahoo returns 404, try:

```
WebFetch https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=<TICKER>&type=&dateb=&owner=include&count=10
```

### Step 2 — Name path

If input is not a ticker, search for the company's canonical identifier:

```
WebSearch "<input>" official site investor relations
```

The first result is usually the company's IR page. `WebFetch` it to confirm the official name and derive a ticker if listed.

### Step 3 — Executive list

Primary source (for listed companies): Yahoo Finance profile page.

```
WebFetch https://finance.yahoo.com/quote/<TICKER>/profile
```

Contains a "Key Executives" table with 5-8 named officers (Name, Title, Pay, Age). Extract at minimum:

- Chief Executive Officer (CEO)
- Chief Financial Officer (CFO)
- Chief Operating Officer (COO) if present
- President (if distinct from CEO)
- Chair of the Board
- Chief Technology / Product / Information Officer if present

Fallback 1 — Wikipedia infobox:

```
WebFetch https://en.wikipedia.org/wiki/<Company>
```

Fallback 2 — company website Leadership / About page (derive URL from Step 2 IR search result).

## Output Schema

Emit the Resolver Output Schema from `references/schemas.md`. Every `executives[].source_url` must be a URL that was actually fetched — do not include unverified names.

## Halt Conditions

- **Ambiguous input.** If two or more distinct companies match the input with similar confidence (e.g. "Apple" matches Apple Inc. and Apple Corps), set `resolution_confidence: low` and halt with `resolution_notes` listing the candidates.
- **Delisted / dissolved.** If Yahoo/SEC shows the company is no longer active, halt and report.
- **No executives discoverable.** If three source attempts fail to yield any executive, emit the schema with `executives: []` and `resolution_confidence: low` — the orchestrator will decide whether to proceed.

## Hard Rules

- Every output field traces to a `source_url`.
- Never fabricate an executive name to pad the list.
- Do not include board members who are not operationally active (e.g. past CEOs still on the board) unless they are explicitly named in recent disclosures.
