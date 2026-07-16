# Companies House Method

## Purpose and Boundary

Use Companies House as a registry evidence source, not as a nationality classifier. The API can search names, dates, status, type, location, and SIC codes, and can retrieve company profiles, officers, PSCs, charges, and filing history. It does not provide an exhaustive filter for Chinese parent ownership.

Report the monitored universe. Never claim complete coverage of all Chinese-backed UK entities.

## API Authentication

Read `COMPANIES_HOUSE_API_KEY`. Send HTTP Basic authentication with the API key as username and an empty password. Never print the key.

## Collection Inputs

Combine:

1. Explicit company numbers from the current Scanner Batch.
2. Known company numbers and aliases from the optional watchlist.
3. Alias searches limited to the report incorporation-date window.

Recommended watchlist JSON:

```json
{
  "version": 1,
  "parents": [
    {
      "parent_name": "Example Chinese Parent Co., Ltd.",
      "aliases": ["EXAMPLE", "EXAMPLE UK"],
      "company_numbers": ["01234567"],
      "notes": "Ownership confirmed from parent annual report."
    }
  ]
}
```

Aliases are discovery terms only. A name match does not establish ownership.

## Endpoints

Use:

- `/advanced-search/companies`
- `/company/{company_number}`
- `/company/{company_number}/officers`
- `/company/{company_number}/persons-with-significant-control`
- `/company/{company_number}/filing-history`
- `/company/{company_number}/charges`

Treat 404 on optional subresources as an empty result, not a fatal error. Record other request errors in the snapshot.

## Material Changes

Prioritise:

- incorporation or registration of an overseas company/UK establishment;
- company status, name, registered office, or SIC change;
- director appointment/resignation involving senior group personnel;
- PSC/controller notification or cessation;
- statement of capital, allotment, reduction, or significant ownership filing;
- new or satisfied charge;
- accounts showing a transition from dormant to trading or a significant scale change;
- liquidation, strike-off, restoration, or insolvency action.

Routine confirmation statements and ordinary accounts filing dates are not automatically material.

## Chinese-Nexus Confidence

### Confirmed

Require a direct ownership/controller link from official company or registry evidence, or multiple authoritative sources explicitly identifying the group relationship.

### Probable

Allow only when the evidence chain is strong and described, such as a unique brand/entity pairing plus matching group officers and official corporate references. State what remains unconfirmed.

### Unverified

Use when evidence is limited to names, nationality, addresses, generic brand similarity, or unsupported databases. Exclude from the final Chinese-company table.

## Diff Interpretation

The diff script reports observed changes between snapshots. A newly observed item is not necessarily newly effective; preserve the filing/effective date. A missing item can reflect pagination, API availability, or changed disclosure, so investigate before describing it as cessation.

## Privacy and Accuracy

Use only public corporate information relevant to the commercial analysis. Do not reproduce residential addresses, full dates of birth, authentication data, or unnecessary personal details.
