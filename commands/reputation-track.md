---
description: "Monitor reputational risk for a company across News, Reddit, and X (Twitter). Given a company name or stock ticker + optional date, resolves the company and its executives, scans for adverse content, and — only if negative findings exist — emails an HTML report. Silent when clean. Usage: /reputation-track --company \"<name|ticker>\" [--date YYYY-MM-DD] [--lang zh|en] [--sources news,reddit,x] [--severity-min low|medium|high] [--email <a@x.com,b@y.com>] [--email-dry-run]"
---

Invoke the `sci-research:reputation-track` skill. Parse the following arguments from the user's slash-command invocation and pass them to the skill orchestrator:

- `--company` (required) — company official name or stock ticker
- `--date` (optional, default today) — target date `YYYY-MM-DD`
- `--lang` (optional, default `zh`) — HTML output language: `zh` or `en`
- `--sources` (optional, default `news,reddit,x`) — subset of supported sources
- `--severity-min` (optional, default `medium`) — drop items below this severity
- `--out-dir` (optional, default `~/Desktop/reputation-reports/{date}/`)
- `--email` (optional) — comma-separated recipients; only sent if negative findings exist
- `--email-subject` (optional) — override the auto-generated subject
- `--email-dry-run` (optional flag) — preview without sending SMTP

Follow the Workflow in `skills/reputation-track/SKILL.md`. In particular:

1. Launch the Resolver first and halt if confidence is low
2. Launch the three Scanners in parallel in a single orchestrator message
3. Silent exit if the Classifier kept zero items — do NOT write HTML, do NOT send email
4. Only invoke the email script when `--email` is non-empty AND items were kept

Print the `DERIVED:` line after Step 1, and the full summary block after Step 9.
