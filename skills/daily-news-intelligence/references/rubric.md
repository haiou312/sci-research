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

- The **active category set is derived from `country`** per `references/language-spec.md` § Category Catalog & Selection — 6 categories for a non-China report (`econ, politics, tech, society, ipo_ma, other`), 7 for a China report (the same plus `china_nexus` at position 5). All active categories must appear as H2 sections in that fixed order, even when a category ends up with zero stories.
- Each category must contain at least `min_per_category` stories when sources allow.
- When short, append the italic `gap_note` rather than inflating with low-tier sources. `china_nexus` and `ipo_ma` are legitimately thin on many days — record the gap, never pad.
- A story belongs to exactly one category — classify by the article's dominant frame, not by topical overlap. For the China-report `china_nexus`↔`ipo_ma` overlap, apply the routing tie-break in § Conditional & Topical Categories below.

## Conditional & Topical Categories

This section is the **authoritative ruleset** for the two non-standard categories. The Scanner uses it to decide what to search and admit; the Verifier uses it to decide what to KEEP, DROP, and how to route. `references/language-spec.md` owns identity/naming/numbering; this section owns eligibility, scope, exclusions, and routing.

### `china_nexus` — China-Nexus Finance & Diplomacy (China report only)

- **Presence**: appears **only** when `country == China`. It is absent from every non-China report. Do not emit a `china_nexus` heading for Japan, the US, the UK, etc.
- **Cross-border requirement (hard)**: a story is eligible only if China **and at least one foreign party** interact — investment, goods/technology flow, commercial/industrial policy, sanctions/tariffs, or diplomacy that crosses China's border. A purely domestic Chinese item (PBoC reserve-ratio cut, a provincial stimulus, an onshore-only regulatory action with no foreign counterparty) is **not** eligible here — it stays in `econ` / `politics`. This keeps `china_nexus` disjoint from `econ`/`politics` within the same China report.
- **Region scope**: the foreign counterparty may be **any country / region** — `china_nexus` is a global topical sweep, NOT country-scoped. The Scanner does not anchor it to a single country the way `econ`/`politics` are anchored to the report country.
- **Exclusion (hard DROP)**: Chinese aid, concessional loans, or development/infrastructure finance directed to Africa or to small developing economies is **dropped** (Verifier reason `China-aid-smallcountry-excluded`). "Small developing economy" = a low- or lower-middle-income economy that is not a G20 member and not a major economy.
  - **Carve-out (overrides the exclusion)**: KEEP if the transaction is itself a **China key-industry play** — e.g. a lithium / rare-earth / cobalt / nickel mine stake, a semiconductor or chip-equipment deal, a port or rail asset that is a strategic logistics node for a key-industry supply chain. Strategic key-industry positioning outranks the aid exclusion.
- **Key-industry list** (drives both the carve-out and priority): semiconductors & chip-making equipment; AI / compute / data centres; electric vehicles & power batteries; rare earths & critical minerals; advanced manufacturing & robotics; biotech & pharmaceuticals; aerospace & commercial aviation; clean energy (solar / wind / nuclear / grid); telecom / 5G / networking; shipbuilding.
- **Priority**: when eligible candidates exceed `min_per_category`, rank stories that touch a key industry **above** stories that do not.

### `ipo_ma` — Corporate IPO & M&A (every report)

- **Presence**: appears in **every** report regardless of `country`.
- **Scope**: IPO or M&A where a **company of the report's country** is a principal — the listing entity, the acquirer, or the target. Country-scoped exactly like `econ`/`politics` (anchored to the report country's companies; the counterparty may be foreign, e.g. a domestic champion acquiring or being acquired by an overseas firm).
- **Materiality floor (hard DROP below it)**: admit a story only if **any** of these holds — (a) an IPO whose priced offering is ≥ USD 300M; (b) an M&A / takeover / buyout with disclosed value ≥ USD 500M; (c) any cross-border deal under national-security or antitrust review; (d) any deal touching a China key industry (per the list above), regardless of size. Below the floor → Verifier reason `Below-IPO-MA-threshold`.

### China-report routing tie-break (`china_nexus` ↔ `ipo_ma`)

A single Chinese company's cross-border deal can match both categories. One story, one category — resolve by dominant frame:

- Dominant frame is China's **external strategic posture, key-industry positioning, or triggering a foreign security/antitrust review** → `china_nexus`.
- Dominant frame is a **corporate-finance event** (offering price, listing venue, ownership change) with no strategic/policy overlay → `ipo_ma`.
- A purely domestic Chinese listing (STAR Market / ChiNext / Shanghai / Shenzhen main board, no foreign party) → always `ipo_ma` (it fails the `china_nexus` cross-border test anyway).
