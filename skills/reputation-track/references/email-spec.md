# Reputation Alert Email

Send only when the Verifier returns one or more findings. A clean run writes no HTML and sends no email.

Default subject:

- `zh`: `[声誉预警] {company_display} - {date_display} - {highest_severity_label}`
- `en`: `[Reputation Alert] {company_display} - {date_display} - {highest_severity_label}`

Send the HTML as the email body with the controlled script:

```bash
python3 "$PLUGIN_ROOT/scripts/send-report-email.py" \
  --to "$email" \
  --subject "$subject" \
  --body-html-file "$out_html"
```

Add `--dry-run` only when `email_dry_run=true`. Do not attach the HTML file.

Never implement SMTP inline or use `sendmail` / `mail -s`. Email failure must not delete the local HTML file, and credentials must never be printed.
