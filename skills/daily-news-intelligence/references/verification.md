# Verification

Writer self-check and final delivery checks only. Workflow and agent assignment live in `../SKILL.md`.

## Writer Self-Check

Before `apply_patch`, run `output-spec.md` § Self-Check Checksum and the applicable rules in `language-spec.md`. Repair what the evidence supports; warn about unresolved defects and still write the best available report.

## End-to-End Verification (after pandoc export)

Run from the skill orchestrator:

```bash
ls -la "{out_md}" "{out_docx}"
```

Both files must exist. Then spot-check the Markdown:

1. `grep -c '^## ' "{out_md}"` should return `6` for a non-China report and `7` for a China report (= `len(active_categories)`).
2. `grep -c '^### ' "{out_md}"` must equal the Verifier's `Kept count`. Every category must contain at most 6 stories; a category below `min_per_category` after deduplication and selection must carry its localized gap note.
3. Pick one story at random and confirm its URL, source, displayed search-result date, and summary trace to the saved Scanner audit. Do not require the URL to open.
4. Confirm every references line matches `^<Org|Surname>.* \(\d{4}, [A-Z][a-z]+ \d{1,2}\)\. .+\. .+\. https?://`.

Also inspect `SCANNER_AUDIT` before delivery:

1. It contains exactly one `<!-- BEGIN CATEGORY OUTPUT: <id> -->` block per active category, in active-category order.
2. Every category block contains `Status: complete`, `partial`, or `unavailable`, the matching `Searched category`, and a normalized candidate count equal to its story blocks and no greater than 10. One unavailable category is not a pipeline failure.
3. Every story contains a category-prefixed Candidate ID, `Publish date (search result)`, `Source`, `URL`, and `Search-result summary`; `URL` is the `google_news_url` returned by `search_news` and may be either a raw URL or a Markdown link. URL presentation and the `news.google.com` domain are not failures, and the story must not claim that the publisher article was fetched or verified.
4. The Scanner Batch header totals equal the sum of the capped category outputs and never exceed 60 candidates for six categories or 70 for seven categories.

Also inspect `VERIFIER_AUDIT` before delivery. Violations trigger the documented mechanical fallback or a warning; they never discard usable report content:

1. `Input count = Kept count + Duplicate count + Not-selected count`.
2. Every Scanner Candidate ID appears exactly once, as a retained `Candidate ID`, a `DROP_DUPLICATE` heading, or a `DROP_NOT_SELECTED` heading.
3. Every duplicate points directly to its first-occurrence representative, which may be KEEP or `DROP_NOT_SELECTED`; there are no duplicate chains.
4. Retained representatives keep their relative first-occurrence input order and searched category.
5. Every retained category count is at most 6. When 3-6 unique events exist, all are retained; when more than 6 exist, exactly 6 are retained; when fewer than 3 exist, all are retained. A gap is recorded only when retained count is below `min_per_category`.
6. The only DROP verdicts are `DROP_DUPLICATE` and `DROP_NOT_SELECTED`.
