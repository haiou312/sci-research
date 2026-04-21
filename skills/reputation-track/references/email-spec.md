# Email Spec — HTML Delivery via Gmail SMTP

Loaded at Workflow Step 7 when `email` is set. Uses the shared `scripts/send-report-email.py` (extended in v1.7.0 to support `--body-html-file` and `multipart/alternative` bodies).

## When This Step Runs

Only when **both** conditions hold:

1. `--email` is non-empty
2. Classifier's `total_items_kept > 0` (at least one negative finding above `--severity-min`)

If `total_items_kept == 0` (clean scan) → silent exit. The orchestrator prints a terminal message and returns 0. No email is sent.

## Environment Variables

Same as Pipelines C and D — `GOOGLE_EMAIL_USERNAME`, `GOOGLE_EMAIL_APP_PASSWORD`, optional `GOOGLE_EMAIL_FROM_NAME`, `GOOGLE_EMAIL_HOST`, `GOOGLE_EMAIL_PORT`, `GOOGLE_EMAIL_START_TLS`. See `.env.example`.

**Never log or echo the app password.**

## Subject Template

Default (override via `--email-subject`):

- `lang=zh`:
  ```
  [声誉预警] {company_display} — {date_display} · {items_kept} 项负面（{highest_severity_label}）
  ```
- `lang=en`:
  ```
  [Reputation Alert] {company_display} — {date_display} · {items_kept} adverse ({highest_severity_label})
  ```

`{highest_severity_label}` = the localised label of the most severe kept item (e.g. `危急` / `CRITICAL`).

## Invocation

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/send-report-email.py" \
  --to "$email" \
  --subject "$subject" \
  --body-html-file "$out_html" \
  ${email_dry_run:+--dry-run}
```

The script will:
1. Read `$out_html` as UTF-8
2. Strip tags to generate a `text/plain` fallback
3. Build `multipart/alternative` with both parts
4. Send (or dry-run print)

## Attachment Behaviour

**No attachments by default.** The HTML is the email body itself, not an attachment — recipients see a rendered page inline in Gmail/Outlook, no extra click.

If an orchestrator wants to attach supporting artifacts (e.g. JSON evidence dump for audit), it can pass `--attach <path> [<path> ...]` alongside `--body-html-file`. For v1 MVP, no attachments are used.

## Exit Code Handling

Same table as `skills/daily-news-intelligence/references/email-spec.md`:

| Python script exit | Orchestrator action |
|---|---|
| 0 | Print "✅ email sent to {N} recipient(s)" |
| 1 | Print "⚠️ email skipped: missing env vars. Local HTML is preserved." |
| 2 | Print "⚠️ email skipped: invalid recipient format." |
| 3 | Print "⚠️ email failed: SMTP error. Local HTML is preserved." |
| 5 | Print "⚠️ email failed: body HTML file not found." |
| 6 | Print "⚠️ email skipped: no content to send (check --body-html-file)." |

**Hard rule:** email failure must never delete the local `out_html` file. It was already produced by the Writer in Step 6.

## Security

- Never `echo`, `cat`, or interpolate `$GOOGLE_EMAIL_APP_PASSWORD`.
- Validate recipients against `^[^@\s]+@[^@\s]+\.[^@\s]+$` before sending (the Python script enforces this).
- The HTML body may contain verbatim quotes that are themselves sensitive (allegations, accusations). Recipients should be on a need-to-know basis — the orchestrator does not second-guess the `--email` list.
