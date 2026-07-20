# Monthly Email Specification

Use the controlled sender at `plugin_root/scripts/send-report-email.py`. Never
use inline SMTP, `sendmail`, or `mail -s`.

## Subject

- `zh`: `{country_display}月度热点新闻 — {YYYY年M月}`
- `en`: `{country_display} Monthly News Intelligence — {Month YYYY}`
- `ja`: `{country_display}月間ニュース — {YYYY年M月}`

For bilingual output, use the primary language subject and append a localized
bilingual tag.

## Plain-Text Body

Render a concise body in each requested language containing:

- requested month and effective `as_of`;
- country or region;
- accepted daily-report count and missing-date count;
- final story count and per-category counts;
- attachment filenames, or an explicit no-attachment statement.

For bilingual output, stack the primary and secondary bodies in one email.

## Attachments

Use the Pipeline C meanings:

- `both`: Markdown and DOCX for every requested language;
- `docx`: DOCX only;
- `md`: Markdown only;
- `none`: omit `--attach` entirely.

Write the body to a temporary text file and pass `--body-file`. Add
`--dry-run` when `email_dry_run=true`. Preserve all local files on any sender
error.
