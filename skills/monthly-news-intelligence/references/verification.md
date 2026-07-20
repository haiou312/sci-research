# Monthly Verification

## Source and Selection

1. Confirm the source index identifies the requested country and month.
2. Confirm every accepted source path is inside `source_dir`.
3. Confirm each calendar date contributes at most one report.
4. Confirm `reports_found > 0`; if `require_complete_month=true`, require
   `coverage_complete=true`.
5. Confirm every Curator category completed and every referenced story ID exists.
6. Confirm the Verifier emits every active category once and no source story ID
   supports two final stories.
7. Confirm each Fact Manifest story matches one Verifier final story and contains
   the union of unique references from its evidence story IDs.

## Final Markdown

Run:

```bash
node "$PLUGIN_ROOT/scripts/hooks/monthly-news-format-check.js" --file "$OUT_MD"
```

Correct every violation before export or email. Then confirm:

- H1 and filename use the requested month and target language;
- exactly one localized source-coverage note appears before the first H2;
- H2 categories match the Pipeline C country-derived set and order;
- final story IDs are represented once and in Verifier order;
- facts, dates, transaction stages, uncertainty, and quotations match the
  Manifest;
- each story carries all and only its Manifest URLs;
- `[N]` is continuous document-wide;
- Chinese and English story bodies meet their hard minimum without padding;
- current-month language says the report is through `as_of`, not a completed
  month.

## Export and Delivery

Run format validation before each pandoc export. Confirm every requested `.md`
and `.docx` exists. Email only when explicitly requested, using
`plugin_root/scripts/send-report-email.py`; email failure must not remove or
alter local reports.
