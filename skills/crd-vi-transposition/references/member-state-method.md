# Dynamic EU Member-State Method

Determine the country scope again on every run. Never use a bundled country
list, an expected count, EY rows, or the previous report as the membership
authority.

## Official authorities

Open and extract the complete English-language Member-State list from both:

1. European Union country profiles:
   `https://european-union.europa.eu/principles-countries-history/eu-countries_en`
2. EUR-Lex Member States:
   `https://eur-lex.europa.eu/legal-content/EN/ALL/?uri=LEGISSUM:member_states`

Open the underlying pages. Do not infer membership from search snippets,
candidate-country pages, the euro area, Schengen, the EEA, or CRD VI tracker
row counts.

Follow every pagination page or load-more result. Record the authority's stated
total as `displayed_count`, extract every country into `countries`, and let the
validator reject the source when the stated total and extracted unique rows do
not agree. Never treat the first visible page as the complete list.

## Run artifact

Create `audit/membership-snapshot.json` before any country research:

```json
{
  "schema_version": 1,
  "checked_at": "2026-08-03T07:00:00+01:00",
  "count": 27,
  "countries": ["Austria", "Belgium", "..."],
  "sources": [
    {
      "source_id": "eu_country_profiles",
      "url": "https://european-union.europa.eu/principles-countries-history/eu-countries_en",
      "available": true,
      "pagination_complete": true,
      "retrieved_at": "2026-08-03T07:00:00+01:00",
      "displayed_count": 27,
      "countries": ["Austria", "Belgium", "..."]
    },
    {
      "source_id": "eur_lex_member_states",
      "url": "https://eur-lex.europa.eu/legal-content/EN/ALL/?uri=LEGISSUM:member_states",
      "available": true,
      "pagination_complete": true,
      "retrieved_at": "2026-08-03T07:01:00+01:00",
      "displayed_count": 27,
      "countries": ["Austria", "Belgium", "..."]
    }
  ]
}
```

Use the EU country-profiles spelling in the top-level `countries` list. The
validator normalizes harmless naming variants such as `Czech Republic` and
`Czechia` only for cross-source comparison; it never adds or removes a country.

Validate immediately:

```bash
python3 "$SKILL_ROOT/scripts/validate-member-states.py" \
  --file "$MEMBERSHIP_SNAPSHOT"
```

Both authorities must set `available: true` and `pagination_complete: true`, be
internally complete, and be equal after name normalization. The top-level list
and `count` must agree with them. Any missing, extra, duplicate, unavailable, or
conflicting country is a hard failure. Do not reuse the previous week's
membership snapshot as a successful current check.

## Dynamic national-source discovery

Treat the validated top-level membership list as the full-country run scope.
There is no bundled national-source map.

- For a country present in the previous successful state, reuse its verified
  national `source_urls` as discovery hints, then reopen the underlying pages.
- For a new member or a country without usable historical national URLs, run a
  deep official-source search under `brave-search-method.md` across its gazette,
  legislation portal, parliament, finance ministry, central bank, or financial
  regulator together with `Directive (EU) 2024/1619`, `CRD VI`, and Article 21c
  terms.
- Form local-language queries dynamically from the official country and source
  pages. Do not persist a fixed country/source table in the skill.
- Save every URL actually checked in `audit/source-checks.json` and the final
  verified URLs in that country's `current-state.json` record.

A membership addition or removal is a material weekly scope change. Show it in
Weekly Changes and preserve it in `weekly-diff.json`.
