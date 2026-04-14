# Rubric — Source Tiers, Authority & Impact, Date Verification, Category Coverage

Loaded by the Scanner (tier + date + coverage) and the Verifier (authority + impact + dedup). Not needed by the Writer.

## Source Tier Rules

| Tier | Type | Examples |
|------|------|----------|
| T1 | Wire services and flagship English newspapers | Reuters, AP, AFP, Bloomberg, FT, NYT, BBC, The Guardian, WSJ, The Economist |
| T2 | National / regional flagships and quality dailies | CNBC, CNN, Politico, Axios, NPR, SCMP, Nikkei Asia, Le Monde, Der Spiegel, Folha, Times of India |
| T3 | Specialist and trade publications | TechCrunch, Wired, The Verge, Euractiv, Semafor, Finextra |
| T4 | Primary institutional releases | Central banks, statistics bureaus, parliaments, regulators (official `.gov` / `.gov.uk` / `.europa.eu` domains) |

Exclude entirely: personal blogs, Wikipedia, link aggregators, forums, SEO farms, content mills, unattributed rewrites.

## Authority & Impact Rubric

The Verifier applies these four independent checks. A story must pass all four to be KEPT.

### 1. Originality

Prefer original reporting over syndicated copies.

- **Original**: outlet broke the story, has its own byline, quotes obtained directly, or is the primary institutional release (T4).
- **Syndicated**: marked "via Reuters/AP/AFP", reproduces another outlet's lede verbatim, or is a near-identical rewrite of an earlier piece.
- **Unclear**: no attribution, no byline, but no evidence of copying either — keep only if no competing original exists.

When multiple candidates cover the same event, keep the most original and drop the rewrites.

### 2. Authority

Grade within T1-T4 using this priority (highest to lowest):

1. `T4-official` — primary institutional release (central bank, regulator, ministry, parliament).
2. `T1-primary` — T1 outlet with named-reporter byline + direct quotes from primary sources.
3. `T1-wire` — T1 wire-service piece (Reuters/AP/AFP/Bloomberg) with organisation byline.
4. `T2-primary` — T2 outlet with named-reporter byline + primary sourcing.
5. `T2-wire` — T2 outlet with organisation byline.
6. `T3` — specialist / trade publication.

Between two candidates on the same event, prefer the higher authority band.

### 3. Impact / Materiality

Accept only stories with demonstrable impact. Match each keep to one tier:

- **Policy** — central bank decisions, legislation passed or tabled, regulatory enforcement, election outcomes, treaty signings.
- **Market** — single-stock or sector moves ≥ 2%, M&A ≥ USD 1B, layoffs ≥ 1000, IPO pricing, sovereign rating changes, large bond auctions.
- **Structural** — technology platform pivots, supply-chain relocations, landmark court rulings, infrastructure approvals/cancellations.
- **Humanitarian** — armed conflict developments, mass-casualty incidents, natural disasters with material regional impact.
- **Regional-structural** (fallback-only) — structural events with regional rather than national scope. Admissible only when Fallback 1 is active for that category.

Reject categorically:

- Lifestyle, celebrity, entertainment, or gossip pieces.
- Routine corporate PR or marketing announcements without material financial impact.
- Op-eds, columns, and pure commentary without new facts.
- Incremental follow-ups that add no new facts to a previously reported story.
- Sports results, unless politically charged (sanctioned athletes, boycotts) or a major championship final (Olympic medal event, World Cup final, Grand Slam title match).

### 4. Deduplication

When two or more candidates cover the same underlying event:

- Keep one `Lead` (the most original + highest authority).
- Mark the rest as `Corroboration-of-#X` in the Verifier schema and drop them from the KEEP set.
- Related consecutive actions on the same policy line (e.g. "central bank announces", "central bank publishes details") collapse to a single story anchored on the most substantive node.

## Two-Step Coverage Fallback

If the Verifier's primary pass leaves any category below `min_per_category`:

### Fallback 1 — Relax impact tier within the shortfall category

- Reconsider items dropped on **impact** grounds only.
- Accept them under the **`Regional-structural`** impact tier if they carry structural significance at a regional or sub-national scope.
- Never reconsider items dropped on date, T1-T4 tier, originality (Syndicated), or categorical reject grounds.

Mark `Fallback used: fallback_1` in the Verifier report header.

### Fallback 2 — Record the gap

- Leave the category underfilled.
- Emit a `Post-Verification Coverage Gap` block for that category.
- Do NOT reach for low-tier or off-date stories to fill the hole.

Mark `Fallback used: fallback_1+gap` in the Verifier report header.

## Date Verification Rules

- Every candidate URL must pass a `web_fetch` round trip.
- The extracted publication date must equal `date` in either the outlet's local timezone or UTC — one match is sufficient.
- Neighbouring days do not qualify. Do not relax the window.
- If the article displays only a relative date (e.g. "2 hours ago") and no absolute date can be recovered from the fetched HTML, drop the candidate.
- If the page is an index, topic hub, or tag listing rather than a single article, drop it.

## Category Coverage Rules

- All five categories must appear as H2 sections in the fixed order, even when a category ends up with zero stories.
- Each category must contain at least `min_per_category` stories when sources allow.
- When short, append the italic `gap_note` rather than inflating with low-tier sources.
- A story belongs to exactly one category — classify by the article's dominant frame, not by topical overlap.
