# Minimal Search Scope

Pipeline C discovery is recall-first. Scanner results are Google News search results, not fetched or verified evidence, and the Verifier is a deduplication-only schema adapter.

## Rules retained

1. Search for news published on the requested `date` about the supplied country and category direction.
2. For a China report, search foreign media only. Do not query or return Chinese domestic media or Chinese government domains.
3. For `Europe-ex-UK`, exclude news whose sole or primary subject is the United Kingdom. A UK publisher may still report an eligible non-UK European event.

## Rules intentionally removed

- No result-page opening requirement.
- No exact-date revalidation beyond the search target and displayed search-result date.
- No readable-body, paywall, source-class, byline, primary-source, or provenance gate.
- No credibility, news-value, impact, originality, corroboration, materiality, or transaction threshold.
- No Lead-quality selection, final category rerouting, or Coverage Review.
- The only Verifier removal is a later report of the same underlying event. The first occurrence remains the representative even when a later duplicate has a stronger headline, source, or summary.
- Different follow-up developments, reactions, decisions, transactions, or transaction stages remain separate stories. No DROP reason other than `DROP_DUPLICATE` is allowed.

The Writer and Editor may perform later research when composing and checking the final report. Retrieval failure must not retroactively alter the Scanner audit or the Verifier's deduplication decisions.
