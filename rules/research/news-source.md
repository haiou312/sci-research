# News Source Rules

These rules MUST be followed when retrieving and using news sources in `/news-scan`.

## Source Credibility Hierarchy

1. **Wire services** (Reuters, AP, AFP, 新华社, 中新社)
   - Highest authority for breaking news and factual reporting
   - Always trace secondary coverage back to the original wire report
   - If a story originates from a wire service, cite the wire service, not the outlet that republished it

2. **Mainstream financial/business media** (FT, Bloomberg, WSJ, CNBC, 财新, BBC)
   - Authoritative for market analysis and policy interpretation
   - Distinguish between news reporting and opinion/editorial content
   - Opinion columns should be cited as "[Author], writing in [Publication]" not as the publication's view

3. **Industry vertical media** (Finextra, TechCrunch, The Paypers, 36氪)
   - Good for sector-specific developments and startup news
   - May have commercial relationships with companies they cover — note potential bias
   - Cross-reference with Tier 1-2 sources when making significant claims

4. **Think tank and expert commentary** (Brookings, PIIE, VoxEU, ProMarket)
   - Useful for analysis and context, not for breaking facts
   - Cite the author and their affiliation, not just the platform
   - Clearly label as "analysis" or "commentary" in the report

5. **Social media and self-published content**
   - Do NOT use as news sources
   - Exception: official government/institutional social media accounts for first-announcement verification

## Deduplication Rules

- When 3+ outlets cover the same event, trace to the **original primary report**
- Count as ONE event in the timeline, list corroborating outlets separately
- If outlets add unique facts not in the original, note these additions
- Never count republished wire stories as independent corroboration

## Time Window Enforcement

| Period | Search Scope | Minimum Fresh Sources |
|--------|-------------|----------------------|
| `7d` | Last 7 calendar days | ≥3 sources from last 7 days |
| `30d` | Last 30 calendar days | ≥5 sources from last 30 days |
| `90d` | Last 90 calendar days | ≥8 sources from last 90 days |

If the minimum cannot be met, state "limited news coverage found for this period" rather than padding with older or irrelevant results.

## Language and Geographic Bias Awareness

- English-language sources dominate global news indexing — actively search in the entity's local language
- Government-affiliated media (新华社, RT, VOA) may reflect state positions — note this framing, do not treat as neutral reporting
- Financial media may reflect market consensus bias — note when contrarian views exist
