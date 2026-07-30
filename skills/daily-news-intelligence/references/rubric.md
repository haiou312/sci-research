# Minimal Search Scope

Pipeline C discovery is recall-first. Scanner results are search results, not opened or verified evidence, and the Verifier is a pass-through schema adapter.

## Rules retained

1. Search for news published on the requested `date` about the supplied country and category direction.
2. For a China report, search foreign media only. Do not query or return Chinese domestic media or Chinese government domains.
3. For `Europe-ex-UK`, exclude news whose sole or primary subject is the United Kingdom. A UK publisher may still report an eligible non-UK European event.

## Rules intentionally removed

- No result-page opening requirement.
- No exact-date revalidation beyond the search target and displayed search-result date.
- No readable-body, paywall, source-class, byline, primary-source, or provenance gate.
- No credibility, news-value, impact, originality, corroboration, materiality, or transaction threshold.
- No deduplication, Lead selection, final category rerouting, or Coverage Review.
- No DROP audit. Every Scanner result is forwarded in its searched category, including blocked, paywalled, snippet-only, or currently unavailable pages.

The Writer and Editor may perform later research when composing and checking the final report. Their inability to open one forwarded URL must not retroactively remove that URL from the Scanner audit or pass-through bundle.
