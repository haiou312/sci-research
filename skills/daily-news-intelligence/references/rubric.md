# Rubric — Source Tiers, Authority & Impact, Date Verification, Category Coverage

Loaded by the per-category Scanner (tier + date + coverage + Pass-B legitimacy), the Merger (cross-category dedup + routing), and the Verifier (authority + impact + source legitimacy). Not needed by the Writer.

## Source Tier Rules

| Tier | Type | Examples |
|------|------|----------|
| T1 | Wire services and flagship English newspapers | Reuters, AP, AFP, Bloomberg, FT, NYT, BBC, The Guardian, WSJ, The Economist |
| T2 | National / regional flagships and quality dailies | CNBC, CNN, Politico, Axios, NPR, SCMP, Nikkei Asia, Le Monde, Der Spiegel, Folha, Times of India |
| T3 | Specialist and trade publications | TechCrunch, Wired, The Verge, Euractiv, Semafor, Finextra |
| T4 | Primary institutional releases | Central banks, statistics bureaus, parliaments, regulators (official `.gov` / `.gov.uk` / `.europa.eu` domains) |

Exclude entirely: personal blogs, Wikipedia, link aggregators, forums, SEO farms, content mills, unattributed rewrites (this is enforced by § Source Legitimacy below for any Pass-B source).

## Source Discovery Model

The Scanner runs **two passes** per category:

- **Pass A — Source Matrix seed (authoritative)**: `site:`-anchored queries down the T4→T1-wire→T1-flagship→T2→T3 ladder against matrix domains. The matrix is the high-authority **seed pool + authority-calibration baseline + structural red-line carrier** (the China external-view design is implemented by the matrix simply not containing Chinese domestic/government rows). It is **not** a hard wall.
- **Pass B — free discovery (recall expansion)**: bare-keyword sweep (no `site:`). Always for `ipo_ma` and `china_nexus`; on-demand for the other five (category below `min_per_category` after Pass A, or a Pass-A hard-paywall Lead with no free Pass-A alternative). Every Pass-B hit passes, in order: (1) the China red-line denylist (China report: drop Chinese domestic-media + `*.gov.cn` domains — a rule, never a judgement), (2) the date gate, (3) § Source Legitimacy below, (4) the authority cap. **Candidates that clear (1)–(3) but fail (4) are NOT discarded** — they are written to the Scanner's `## Reserve Pool` (`held: below-authority-cap`) so the Verifier can promote them via Fallback 1.5 if the category is short. See § Three-Step Coverage Fallback below and `references/schemas.md` § Scanner Output Schema for the reserve-pool format.

Tradeoff accepted by design: Pass B introduces day-to-day source-pool drift (slightly lower reproducibility) in exchange for materially higher recall on paywalled, wire-relay-lagged, and non-whitelist-but-legitimate stories.

## Source Legitimacy Rubric

Applies to **every Pass-B source**. Pass-A matrix sources are pre-cleared (the matrix is the whitelist). Classify each Pass-B outlet into exactly one bucket:

- **`auto-accept`** — a recognized global/national wire or flagship newspaper-of-record that simply is not in the matrix yet (Reuters/AP/AFP/Bloomberg/Kyodo/Yonhap/PTI/Reuters-equivalents; a country's paper of record). **Also** a free **full-text** syndication of a hard-paywalled wire/flagship original (Yahoo Finance carrying full Reuters/Bloomberg, AP News, MSN partner copy): admissible as Lead, the paywalled original recorded under `Corroborated by`. Authority = the original's real tier.
- **`conditional-accept`** — admit only if **ALL** hold: (1) an identifiable independent newsroom / masthead with named editorial staff; (2) a bylined human reporter (not "staff"/"admin"/anonymous); (3) original reporting OR clearly-attributed syndication of a wire/flagship; (4) a corrections/ethics policy or an established multi-year track record; (5) the article sits on the outlet's own primary domain (not an aggregator path or content-mill subdomain). **Authority cap: T2** (T3 for trade/niche outlets). Never T1 unless it is itself a recognized wire/flagship (that is `auto-accept`).
- **`hard-reject`** — discard regardless of how important the story seems: press-release / PR-wire as primary source (PRNewswire, BusinessWire, GlobeNewswire, ACCESSWIRE), SEO or AI-generated content farm, unbacked blog / Substack / Medium / personal site, social-media post, forum or Q&A or link-aggregator (Reddit, Yahoo/Google answers, Investing.com reposts), state-propaganda front, "pink-slime" partisan pseudo-local-news network, scraped-content mill.

**Authority cap rule**: a Pass-B story may be the sole Lead of its category only if Pass A surfaced nothing on that event; otherwise it is recorded as corroboration of the Pass-A Lead. The Verifier enforces this rubric as its Source-legitimacy check and may DROP with reason `Illegitimate-source`.

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

## Three-Step Coverage Fallback

If the Verifier's primary pass leaves any category below `min_per_category`, apply the steps below **in order**. Stop as soon as the category reaches `min_per_category`. Each step records its own marker; markers compose (e.g. `fallback_1+1.5+gap`).

### Fallback 1 — Relax impact tier within the shortfall category

- Reconsider items dropped on **impact** grounds only.
- Accept them under the **`Regional-structural`** impact tier if they carry structural significance at a regional or sub-national scope.
- Never reconsider items dropped on date, T1-T4 tier, originality (Syndicated), source legitimacy (Illegitimate-source), or categorical reject grounds.

Mark `Fallback used: fallback_1` in the Verifier report header.

### Fallback 1.5 — Relax authority cap from Reserve Pool

If Fallback 1 still leaves the category below `min_per_category`, draw from the Merged Bundle's `## Reserve Pool` (the Scanner-produced holding zone defined in `references/schemas.md` § Scanner Output Schema and `skills/daily-news-intelligence/agents/daily-news-scanner.md` § Pass B). The reserve pool contains date-verified candidates that passed the China red-line denylist and the Source Legitimacy rubric but were held back at the Scanner stage for **one of two reasons**:

- **`held: below-authority-cap`** — Pass-B `conditional-accept` outlets whose real tier is at or below the cap (T3 trade / niche / smaller national outlets — e.g. The Register, UKTN, Sifted, Tech.eu, Electronics Weekly, City A.M. tech section, niche industry trades). The cap is the floor for ordinary KEEP eligibility; these candidates are admissible only via this fallback.
- **`held: below-ipo-ma-floor`** — `ipo_ma` deals that satisfy the **soft band** of the materiality scale (USD 50M ≤ value < primary floor) per § Conditional & Topical Categories below. Below USD 50M still hard-DROP at the Scanner.

Rules for what Fallback 1.5 may do:

- Promote held candidates to KEEP at their **real tier** (`Authority score: T3-extended` for `below-authority-cap`; `Authority score` carried verbatim for `below-ipo-ma-floor`). Mark `Dedup role: Lead`.
- Apply only to the shortfall category; never to a category that already met `min_per_category` in Fallback 1.
- Promote in **best-first** order: prefer (a) hits closer to T2 over deep-T3 niche; (b) `Original` over `Unclear`; (c) higher Impact tier when known; (d) `auto-accept` over `conditional-accept`.
- Stop promoting as soon as the category reaches `min_per_category` — do NOT over-fill at the expense of report compactness.
- Never relax date, China red-line denylist, originality (Syndicated drops stay dropped), or Source Legitimacy (`Illegitimate-source` DROPs stay dropped).
- Hard-paywall candidates are **never** Fallback 1.5-promotable (the Writer needs ≥200 words of body; the Step 3.5 paywall workaround already handled the legitimate cases at Scanner time).

Mark `Fallback used: fallback_1+1.5` in the Verifier report header.

### Fallback 2 — Record the gap

If Fallback 1 and Fallback 1.5 together still leave the category below `min_per_category`:

- Leave the category underfilled.
- Emit a `Post-Verification Coverage Gap` block for that category.
- Do NOT reach for low-tier or off-date stories to fill the hole.

Mark `Fallback used: fallback_1+1.5+gap` (or `fallback_1+gap` if 1.5 did not need to run because the reserve pool was empty) in the Verifier report header.

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

### `china_nexus` — China-Nexus Finance & Investment (China report only)

- **Presence**: appears **only** when `country == China`. It is absent from every non-China report. Do not emit a `china_nexus` heading for Japan, the US, the UK, etc.
- **Cross-border requirement (hard)**: a story is eligible only if China **and at least one foreign party** interact through an **economic / financial channel** — inbound or outbound investment & FDI, goods/technology flow, commercial & industrial policy, tariffs, export controls, sanctions, trade measures, or investment-screening actions that cross China's border. A purely domestic Chinese item (PBoC reserve-ratio cut, a provincial stimulus, an onshore-only regulatory action with no foreign counterparty) is **not** eligible — it stays in `econ`.
- **Finance scope, not diplomacy (hard)**: `china_nexus` is the **economic / commercial** thread only. Pure diplomacy with no concrete economic transaction — bilateral summits, joint statements, foreign-ministry rhetoric, ambassadorial actions, treaty signings with no commercial core — belongs in `politics` (the China report's Politics & Diplomacy category at position 2 already covers it), **not** here. Tariffs, sanctions, export controls and investment-screening are NOT treated as diplomacy: they carry concrete economic substance and stay in `china_nexus`. This keeps `china_nexus` disjoint from both `econ` and `politics` within the same China report.
- **Region scope**: the foreign counterparty may be **any country / region** — `china_nexus` is a global topical sweep, NOT country-scoped. The Scanner does not anchor it to a single country the way `econ`/`politics` are anchored to the report country.
- **Exclusion (hard DROP)**: Chinese aid, concessional loans, or development/infrastructure finance directed to Africa or to small developing economies is **dropped** (Verifier reason `China-aid-smallcountry-excluded`). "Small developing economy" = a low- or lower-middle-income economy that is not a G20 member and not a major economy.
  - **Carve-out (overrides the exclusion)**: KEEP if the transaction is itself a **China key-industry play** — e.g. a lithium / rare-earth / cobalt / nickel mine stake, a semiconductor or chip-equipment deal, a port or rail asset that is a strategic logistics node for a key-industry supply chain. Strategic key-industry positioning outranks the aid exclusion.
- **Key-industry list** (drives both the carve-out and priority): semiconductors & chip-making equipment; AI / compute / data centres; electric vehicles & power batteries; rare earths & critical minerals; advanced manufacturing & robotics; biotech & pharmaceuticals; aerospace & commercial aviation; clean energy (solar / wind / nuclear / grid); telecom / 5G / networking; shipbuilding.
- **Priority**: when eligible candidates exceed `min_per_category`, rank stories that touch a key industry **above** stories that do not.

### `ipo_ma` — Corporate IPO & M&A (every report)

- **Presence**: appears in **every** report regardless of `country`.
- **Scope**: IPO or M&A where a **company of the report's country** is a principal — the listing entity, the acquirer, or the target. Country-scoped exactly like `econ`/`politics` (anchored to the report country's companies; the counterparty may be foreign, e.g. a domestic champion acquiring or being acquired by an overseas firm).
- **Materiality scale (three bands)**: classify each candidate against the value bands below. Bands (a)–(d) define the **primary floor**; (e) defines the **soft band**.
  - **Primary band (KEEP-eligible at the Scanner stage)**: any of — (a) an IPO whose priced offering is ≥ USD 300M; (b) an M&A / takeover / buyout with disclosed value ≥ USD 500M; (c) any cross-border deal under national-security or antitrust review; (d) any deal touching a China key industry (per the list above), regardless of size. Goes into the Scanner's main bundle, evaluated normally by the Verifier.
  - **(e) Soft band (Reserve Pool, Fallback-1.5-eligible only)**: an IPO priced USD 50M ≤ value < USD 300M, or an M&A / takeover / buyout USD 50M ≤ value < USD 500M, with **no** primary-band qualifier (no review-trigger, no China-key-industry touch). The Scanner writes these to `## Reserve Pool` with `held: below-ipo-ma-floor` (per `references/schemas.md`); the Verifier may promote them via Fallback 1.5 if the category is short. Outside that fallback path they are never KEEP.
  - **Below USD 50M** (and no primary-band qualifier): hard DROP at the Scanner with reason `Below-IPO-MA-threshold`. Not reserve-pool eligible; not Fallback-1.5-promotable.

### China-report routing tie-break (`china_nexus` ↔ `ipo_ma`)

**Applied at the Merge stage, not by the Scanner.** Each per-category Scanner only judges whether an item is in-scope for its own category and may leave a `Reroute hint`; the Merger owns this tie-break and all cross-category dedup. A single Chinese company's cross-border deal can match both categories. One story, one category — resolve by dominant frame:

- Dominant frame is China's **external economic / industrial strategy, key-industry positioning, or triggering a foreign security / antitrust / investment-screening review** → `china_nexus`.
- Dominant frame is a **corporate-finance event** (offering price, listing venue, ownership change) with no strategic/policy overlay → `ipo_ma`.
- A purely domestic Chinese listing (STAR Market / ChiNext / Shanghai / Shenzhen main board, no foreign party) → always `ipo_ma` (it fails the `china_nexus` cross-border test anyway).
