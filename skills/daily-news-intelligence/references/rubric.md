# Rubric - Verifier Editorial Rules

Loaded by the Verifier, not the category Scanners. The Scanner's complete instructions are intentionally short and live in `.codex/agents/sci-research-daily-news-scanner.toml`; do not apply this document's editorial, deduplication, routing, or materiality rules during discovery.

This document defines final admission rules without an outlet whitelist, source tiers, fixed per-domain query plan, or mechanical impact thresholds.

## Source Eligibility

Classify each Lead into exactly one `Source class`:

| Source class | Meaning |
|---|---|
| `established-media` | Accountable international or national newsroom with an established reporting record |
| `reputable-regional` | Accountable regional or local newsroom with identifiable provenance and direct relevance to the event |
| `reputable-specialist` | Established trade, legal, financial, scientific, technology, or industry publication with subject-matter reporting responsibility |
| `sanctioned-syndication` | Transparent, attributed syndication with enough readable factual body when the original is inaccessible or paywalled |

Eligibility principles:

- A personal byline is useful but not mandatory. An established outlet's organisation byline is acceptable.
- Source authority is claim-specific. Media reporting should clearly attribute official decisions, filings, statistics, and statements; disputed effects, criticism, and broader interpretation require credible reporting support.
- Regional and specialist sources may Lead when they directly report an in-scope event and have accountable editorial provenance.
- A media report may rely on a filing or official statement for what an institution or company announced. Material consequences or contested claims should be corroborated when practical.
- Transparent syndication is eligible when attribution is clear. Prefer the original URL when it is usable; otherwise retain the original under `Corroborated by` when known.
- Scanner admits only media reporting with enough readable factual body. When the original is paywalled, an authoritative free same-event report or transparent attributed syndication must supply the candidate body.

Hard-reject as a Lead:

- PR-wire distribution used as sole reporting;
- SEO/AI content farms, scraped-content mills, fabricated local-news networks, or anonymous unattributed rewrites;
- unsupported personal blogs, Substack/Medium posts, social-media posts, forums, Q&A pages, and link aggregators;
- pages whose provenance, date, or asserted event cannot be verified;
- promotional copy with no substantive reportable fact.

## Geographic Scope Gate

The Verifier applies this gate after revalidating the date and before editorial selection. Coverage Review may never relax it.

For ordinary single-country reports:

- The target country must be the event's primary decision-maker, jurisdiction, location, regulated market, materially affected principal, or direct economic/political counterparty.
- Foreign actors may appear, but the target-country relevance must be concrete rather than incidental.

For `geography_scope = Europe-ex-UK`:

- `Europe` means Europe excluding events whose sole or primary geographic nexus is the United Kingdom.
- Hard-DROP `UK-primary-nexus-excluded` for UK domestic government, parliamentary, judicial, regulatory, central-bank, market, corporate, social, public-health, or other primarily UK events.
- KEEP an event led by an EU/pan-European institution or non-UK European jurisdiction when that side independently carries the material action or impact and remains the dominant frame.
- For a mixed Europe-UK event, removing the UK facts must still leave an independently meaningful non-UK European event.
- Publisher nationality is irrelevant. A UK outlet can report an eligible non-UK European event.

## China External-View Gate

For `country = China`:

- Do not query or admit Chinese domestic media or Chinese government domains as report sources.
- Chinese domestic actions must be reported through eligible foreign media.
- This restriction applies across all categories and cannot be relaxed for coverage.

The Scanner already applies the same foreign-media-only rule. The Verifier revalidates it.

## Editorial Selection Rubric

The Verifier applies five checks. A story must pass all five, except that Coverage Review may broaden only the news-value judgement.

### 1. Credible evidence

The source must fit one eligible `Source class`, support the asserted event, expose a verifiable date, and provide identifiable provenance. Sensitive allegations and disputed claims require clearly identified documentary evidence or credible independent corroboration.

### 2. Concrete new information

The target date must contain a reportable development: a decision, filing, vote, enforcement step, result, transaction stage, data release, operational change, market consequence, attributable reaction, or original factual finding.

Transparent syndication is acceptable. Drop a rewrite or follow-up only when it adds no meaningful new fact.

### 3. Daily briefing value

Use contextual judgement rather than fixed numerical thresholds:

- `high` - major consequences for policy, politics, economy, markets, business, technology, society, law, security, diplomacy, or humanitarian conditions.
- `medium` - a concrete development with meaningful national, regional, sector, company, community, or institutional relevance.
- `coverage-keep` - narrower but useful information admitted during Coverage Review for an under-covered category.

An event does not need to be nationally transformative. It is enough that an informed executive reader would reasonably want to know it happened today and that its consequence or relevance can be stated clearly.

Categorical rejects:

- routine marketing or promotion with no substantive consequence;
- opinion/commentary without a new reportable fact;
- unsupported rumours or speculation;
- lifestyle, celebrity, entertainment, or gossip without broader significance;
- ordinary sports results without material political, economic, diplomatic, or major-championship significance;
- content whose only rationale is that it appeared in a famous outlet.

### 4. Originality and corroboration

Select the Lead with the clearest claim-level evidence and most useful retrievable body. Do not use a global prestige score.

### 5. Deduplication

Merge only the same underlying event: substantially the same actors, action, and date. Keep later stages or follow-ups when they add a distinct decision, filing, vote, enforcement action, result, or other material fact. Broad thematic similarity is not duplication.

## Coverage Review

If the primary Verifier pass leaves a category below `min_per_category`:

1. Reconsider candidates rejected only as `No-meaningful-news-value` during the primary Verifier pass.
2. KEEP as `coverage-keep` when the candidate still has an eligible source, exact date, correct geography, a concrete new fact, and identifiable relevance to the category.
3. Regional, specialist, institutional, and company-level developments may qualify; national-scale impact is not required.
4. Never restore source-provenance failures, off-date or geography failures, China external-view violations, exact duplicates, routine PR, opinion-only pieces, unsupported rumours, or fabricated/unverifiable material.
5. Continue until the category reaches `min_per_category` or no eligible candidates remain. Existing high/medium stories are never removed merely to hit a number.

When a category remains short, record the gap instead of admitting weak evidence.

## Date Verification Rules

- Each category Scanner admits only exact-date candidates; the Verifier revalidates that decision.
- Every candidate URL must pass an `open_page` round trip on the canonical article or document.
- The extracted publication date must equal `date` in either the outlet's local timezone or UTC.
- Neighbouring days do not qualify.
- Search snippets alone are not proof.
- Drop relative-only dates with no recoverable absolute date, index/topic/search pages, empty pages, and pages whose canonical date cannot be verified.

## Category Coverage Rules

- The active category set comes from `references/language-spec.md`: six categories for a non-China report and seven for a China report.
- One category Scanner searches each active category and returns every candidate that passes its short hard-rule set.
- Verifier aims for at least `min_per_category` KEEP stories per category, using Coverage Review when necessary.
- Every story belongs to exactly one category by dominant frame.
- Underfilled categories carry the localized `gap_note`; never pad them with untrustworthy, off-date, or out-of-scope material.

## Conditional and Topical Categories

The following are Verifier routing and final-admission rules. The Scanner does not apply them while discovering candidates.

### `china_nexus` - China-Nexus Finance and Investment

- Appears only when `country == China`.
- Requires China and at least one foreign party interacting through a concrete economic or financial channel: investment, FDI, goods/technology flow, commercial or industrial policy, tariffs, export controls, sanctions, trade measures, or investment screening.
- Purely domestic China developments belong in the appropriate general category.
- Pure diplomacy without concrete economic substance belongs in `politics`.
- The foreign counterparty may be anywhere; this is a global topical search.
- Drop Chinese aid, concessional lending, or development/infrastructure finance to Africa or a small developing economy unless the event is itself a strategic key-industry or supply-chain transaction.
- Strategic areas include semiconductors, AI/compute, EVs and batteries, critical minerals, advanced manufacturing, biotech, aerospace, clean energy and grids, telecoms, and strategic logistics.

### `ipo_ma` - Corporate IPO and M&A

- Appears in every report.
- A company linked to the report country must be a principal listing entity, acquirer, target, seller, or materially affected regulated party.
- For `Europe-ex-UK`, at least one independently material principal must be headquartered, registered, listed, or regulated in non-UK Europe.
- Eligibility is contextual, not a fixed dollar threshold. A filing, priced or proposed IPO, acquisition, takeover, merger, strategic stake, review, approval, rejection, or completion is eligible when it has a concrete new development and meaningful financial, strategic, competitive, employment, regulatory, market-access, ownership, or industrial significance.
- Drop unsupported rumours and routine immaterial transactions with no identifiable briefing value.

### China-report routing tie-break

For an event that matches both `china_nexus` and `ipo_ma`:

- Route to `china_nexus` when the dominant frame is China's external economic/industrial strategy, key-industry positioning, or foreign security/antitrust/investment screening.
- Route to `ipo_ma` when the dominant frame is corporate finance, listing mechanics, price, venue, or ownership change without a strategic policy overlay.
- Route a purely domestic Chinese listing to `ipo_ma`.
