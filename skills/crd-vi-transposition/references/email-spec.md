# CRD VI Email Delivery

Use the controlled sender at `plugin_root/scripts/send-report-email.py`. Never
use inline SMTP, `sendmail`, or `mail -s`.

## Trigger and subject

Send only when `email` is non-empty. The default subject is:

```text
CRD VI Transposition Tracker — {report_week}
```

Use `email_subject` when supplied. Recipients are a comma-separated list of
validated email addresses.

## Body

Send a concise English plain-text body containing:

- report week, period, status cutoff, and checked-at timestamp;
- validated EU Member State count;
- material country-change count and regulatory-news count;
- status counts and the saved report path;
- whether the Markdown report is attached;
- a short note that the attached report is AI-assisted and should be verified
  independently before reliance.

Use the report itself as the source of all figures. Do not include secrets or
the full SMTP configuration in the body.

## Attachment and invocation

`email_attach=md` attaches the saved Markdown report. `email_attach=none`
sends the body only and must omit `--attach` entirely. The report must always be
saved before email delivery, even when `output=inline` was requested.

Invoke:

```bash
python3 "$PLUGIN_ROOT/scripts/send-report-email.py" \
  --to "$EMAIL" \
  --subject "$EMAIL_SUBJECT" \
  --body "$EMAIL_BODY" \
  [--attach "$OUT_MD"] \
  [--dry-run]
```

Add `--dry-run` only when `email_dry_run=true`. Dry-run does not connect to
SMTP, but the sender still requires the standard email environment variables:
`GOOGLE_EMAIL_USERNAME` and `GOOGLE_EMAIL_APP_PASSWORD`.

Email errors must be reported while preserving all local Markdown and audit
files. Never print `GOOGLE_EMAIL_APP_PASSWORD`.
