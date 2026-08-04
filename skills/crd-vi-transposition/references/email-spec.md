# CRD VI Email Delivery

Use the controlled sender at `plugin_root/scripts/send-report-email.py`. Never
use inline SMTP, `sendmail`, or `mail -s`.

## Trigger and subject

Send only when `email` is non-empty, using the validated comma-separated
recipients and the configured or default `email_subject`.

## Body

Send a concise English plain-text body containing:

- report week, period, status cutoff, and checked-at timestamp;
- validated EU Member State count;
- material country-change count and regulatory-news count;
- status counts and the saved Markdown and Word paths;
- the actual attachment filenames, or an explicit no-attachment statement;
- a short note that the report is AI-assisted and should be verified
  independently before reliance, referring to an attachment only when one is
  actually included.

Use the report itself as the source of all figures. Do not include secrets or
the full SMTP configuration in the body.

## Attachment and invocation

The default is `email_attach=docx`, which attaches the mandatory Word report.
Supported values are:

| Value | Attachments |
|---|---|
| `docx` (default) | `OUT_DOCX` |
| `both` | `OUT_MD` and `OUT_DOCX` |
| `md` | `OUT_MD` |
| `none` | none; omit `--attach` entirely |

Require saved Markdown, a validated DOCX, and successful delivery metadata
before any email attempt. Never fall back from Word to Markdown silently.

Invoke:

```bash
python3 "$PLUGIN_ROOT/scripts/send-report-email.py" \
  --to "$EMAIL" \
  --subject "$EMAIL_SUBJECT" \
  --body "$EMAIL_BODY" \
  --attach "$OUT_DOCX" \
  [--dry-run]
```

The command shows the default. For `both`, replace its attachment argument with
`--attach "$OUT_MD" "$OUT_DOCX"`; for `md`, use `--attach "$OUT_MD"`; for
`none`, omit the entire `--attach` option.

Add `--dry-run` only when `email_dry_run=true`. Dry-run does not connect to
SMTP, but the sender still requires the standard email environment variables:
`GOOGLE_EMAIL_USERNAME` and `GOOGLE_EMAIL_APP_PASSWORD`.

Email errors must be reported while preserving all local Markdown, Word, and
audit files. Never print `GOOGLE_EMAIL_APP_PASSWORD`.
