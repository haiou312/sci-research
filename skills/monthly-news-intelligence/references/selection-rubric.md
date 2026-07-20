# Monthly Selection Rubric

Load this file in the Monthly Curator and Monthly Verifier. Apply it only to
stories already present in the monthly source index. Never search the web.

## Unit of Selection

Select an **event cluster**, not a daily headline. An event cluster contains
daily-report stories that share substantially the same principal actors and
underlying development. Merge later reporting when it advances the same
decision, transaction, policy, crisis, data series, or consequence.

Do not merge stories merely because they concern the same institution, industry,
country, or broad theme. Keep a later development separate when it is a distinct
decision, vote, filing, enforcement action, completed transaction, result, or
other independently consequential event.

## Ranking Dimensions

Judge the whole cluster. Use editorial judgement rather than a mechanical score.

1. **Institutional consequence** — changes law, policy, regulation, official
   leadership, fiscal or monetary settings, market structure, or public services.
2. **Scale and reach** — materially affects a large population, important market,
   strategic industry, major company, or cross-border relationship.
3. **Monthly development** — contains a meaningful progression, result, reversal,
   escalation, or resolution during the requested month.
4. **Decision usefulness** — helps an institutional reader understand what
   happened, why it matters, who is affected, and what remains unresolved.
5. **Evidence depth** — the source daily stories provide enough facts, dates,
   numbers, attribution, and references for a substantive monthly synthesis.

Repeated coverage is evidence of development only when later stories add facts.
Frequency alone never makes an event important. Do not force artificial coverage
of the beginning, middle, and end of the month; use date spread only as a
tiebreaker between events of similar significance.

## Selection Rules

- Return at most `stories_per_category` primary clusters plus at most two
  alternates.
- Keep fewer primary clusters when the source index does not support the target.
  Never pad with routine announcements or loosely related stories.
- Assign every cluster to exactly one final category.
- Preserve the Pipeline C active-category order.
- Select the smallest evidence set that supports a complete monthly story:
  normally one to five source story IDs.
- List every related story ID for deduplication, but distinguish it from the
  smaller `Evidence story IDs` set.
- Use facts only from the evidence story IDs in downstream writing.
- Prefer evidence stories that jointly capture the first material development,
  important intermediate change, and latest stage.
- Never infer facts from a headline, URL, file name, missing date, or publication
  frequency.

## Cross-Category Resolution

The Verifier owns final cross-category deduplication and routing. When two
Curators select the same underlying event:

1. Keep one event cluster.
2. Route it to the category that best represents the principal new development.
3. Combine the smallest complementary evidence set from the duplicate clusters
   when needed, while retaining the one-to-five-ID limit.
4. Promote an alternate in the vacated category only when it independently meets
   the rubric.
5. Preserve all evidence story IDs needed for the event timeline.

For China reports, retain the Pipeline C distinction:

- `china_nexus` covers overseas reporting whose central development is a
  China-linked financial, investment, trade, sanctions, supply-chain, or
  cross-border business matter.
- `ipo_ma` covers a concrete IPO or M&A stage involving a China-linked principal.
  When both apply, a concrete listing or transaction stage takes `ipo_ma`.

## Prohibited Behaviour

- Do not open URLs or use WebSearch.
- Do not add a story absent from the source index.
- Do not invent significance, causality, customer impact, transaction stage, or
  future action.
- Do not treat missing daily reports as evidence that no event occurred.
- Do not select the same event twice under different wording.
- Do not rewrite source bodies during Curator or Verifier stages.
