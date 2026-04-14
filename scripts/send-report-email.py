#!/usr/bin/env python3
"""
Send daily news intelligence report via Gmail SMTP.

Reads credentials from environment variables:
  GOOGLE_EMAIL_USERNAME        — Gmail address (e.g. user@gmail.com)
  GOOGLE_EMAIL_APP_PASSWORD    — Gmail app password (16 chars, not account password)
  GOOGLE_EMAIL_FROM_NAME       — optional display name for the From header
  GOOGLE_EMAIL_HOST            — SMTP host (default: smtp.gmail.com)
  GOOGLE_EMAIL_PORT            — SMTP port (default: 587)
  GOOGLE_EMAIL_START_TLS       — 'true' to use STARTTLS on port 587 (default: true)

Usage:
  send-report-email.py \\
    --to "alice@foo.com,bob@bar.com" \\
    --subject "中国每日热点新闻 — 2026年4月14日" \\
    --body-file /tmp/body.txt \\
    --attach /path/to/report.md /path/to/report.docx \\
    [--dry-run]

Exit codes:
  0 — success or dry-run completed
  1 — missing required environment variables
  2 — no recipients specified
  3 — SMTP connection or send failure
  4 — attachment file not found
  5 — body file not found
"""

import argparse
import mimetypes
import os
import smtplib
import ssl
import sys
from email.message import EmailMessage
from pathlib import Path


REQUIRED_ENV = [
    "GOOGLE_EMAIL_USERNAME",
    "GOOGLE_EMAIL_APP_PASSWORD",
]

EMAIL_RE = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


def load_env():
    """Read Gmail SMTP config from environment. Exit 1 on missing required vars."""
    missing = [k for k in REQUIRED_ENV if not os.environ.get(k)]
    if missing:
        print(
            f"ERROR: missing required environment variables: {', '.join(missing)}",
            file=sys.stderr,
        )
        print(
            "Set them in your shell profile (e.g. ~/.zshrc) and reload before running.",
            file=sys.stderr,
        )
        sys.exit(1)

    return {
        "user": os.environ["GOOGLE_EMAIL_USERNAME"],
        "password": os.environ["GOOGLE_EMAIL_APP_PASSWORD"],
        "from_name": os.environ.get("GOOGLE_EMAIL_FROM_NAME", "").strip(),
        "host": os.environ.get("GOOGLE_EMAIL_HOST", "smtp.gmail.com").strip(),
        "port": int(os.environ.get("GOOGLE_EMAIL_PORT", "587")),
        "starttls": os.environ.get("GOOGLE_EMAIL_START_TLS", "true").lower() == "true",
    }


def parse_recipients(raw):
    """Split comma-separated recipient string and validate format."""
    import re

    recipients = [r.strip() for r in raw.split(",") if r.strip()]
    if not recipients:
        print("ERROR: no recipients specified via --to", file=sys.stderr)
        sys.exit(2)

    invalid = [r for r in recipients if not re.match(EMAIL_RE, r)]
    if invalid:
        print(f"ERROR: invalid email address format: {invalid}", file=sys.stderr)
        sys.exit(2)
    return recipients


def read_body(body_text, body_file):
    """Prefer --body-file when both given; return the text content."""
    if body_file:
        p = Path(body_file).expanduser()
        if not p.exists():
            print(f"ERROR: body file not found: {p}", file=sys.stderr)
            sys.exit(5)
        return p.read_text(encoding="utf-8")
    return body_text or ""


def build_message(cfg, recipients, subject, body, attachments):
    """Construct an EmailMessage with attachments."""
    msg = EmailMessage()
    from_name = cfg["from_name"] or cfg["user"]
    msg["From"] = f'"{from_name}" <{cfg["user"]}>'
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    msg.set_content(body, charset="utf-8")

    for path in attachments:
        p = Path(path).expanduser()
        if not p.exists():
            print(f"ERROR: attachment not found: {p}", file=sys.stderr)
            sys.exit(4)

        ctype, encoding = mimetypes.guess_type(str(p))
        if ctype is None or encoding is not None:
            ctype = "application/octet-stream"
        maintype, subtype = ctype.split("/", 1)

        with open(p, "rb") as f:
            msg.add_attachment(
                f.read(),
                maintype=maintype,
                subtype=subtype,
                filename=p.name,
            )
    return msg


def send(cfg, msg, dry_run):
    """Send the message via SMTP, or print a summary if dry-run."""
    if dry_run:
        print("=== DRY RUN — message NOT sent ===")
        print(f"SMTP host: {cfg['host']}:{cfg['port']} (starttls={cfg['starttls']})")
        print(f"From: {msg['From']}")
        print(f"To: {msg['To']}")
        print(f"Subject: {msg['Subject']}")
        attachment_names = [a.get_filename() or "(unnamed)" for a in msg.iter_attachments()]
        print(f"Attachments ({len(attachment_names)}): {attachment_names}")
        # Print first 800 chars of body for inspection
        body_part = msg.get_body(preferencelist=("plain",))
        if body_part:
            body_preview = body_part.get_content()[:800]
            print("--- body preview ---")
            print(body_preview)
            if len(body_part.get_content()) > 800:
                print(f"... (body truncated, total {len(body_part.get_content())} chars)")
        return

    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP(cfg["host"], cfg["port"], timeout=30) as server:
            server.ehlo()
            if cfg["starttls"]:
                server.starttls(context=ctx)
                server.ehlo()
            server.login(cfg["user"], cfg["password"])
            server.send_message(msg)
    except smtplib.SMTPAuthenticationError as e:
        print(
            f"ERROR: SMTP authentication failed. Verify GOOGLE_EMAIL_APP_PASSWORD "
            f"is a Gmail App Password (16 chars, no spaces), not your account "
            f"password. Detail: {e.smtp_code} {e.smtp_error.decode('utf-8', errors='replace') if isinstance(e.smtp_error, bytes) else e.smtp_error}",
            file=sys.stderr,
        )
        sys.exit(3)
    except (smtplib.SMTPException, ConnectionError, TimeoutError, OSError) as e:
        print(f"ERROR: SMTP send failed: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(3)


def main():
    parser = argparse.ArgumentParser(
        description="Send a daily news report via Gmail SMTP.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--to",
        required=True,
        help="Comma-separated list of recipient email addresses.",
    )
    parser.add_argument(
        "--subject",
        required=True,
        help="Email subject line (UTF-8 supported).",
    )
    body_group = parser.add_mutually_exclusive_group(required=True)
    body_group.add_argument(
        "--body",
        help="Plain-text email body (use --body-file for long content).",
    )
    body_group.add_argument(
        "--body-file",
        help="Path to a UTF-8 text file containing the email body.",
    )
    parser.add_argument(
        "--attach",
        nargs="*",
        default=[],
        help="Zero or more file paths to attach. Missing files abort the send.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build the message and print a summary but do NOT connect to SMTP.",
    )

    args = parser.parse_args()

    cfg = load_env()
    recipients = parse_recipients(args.to)
    body = read_body(args.body, args.body_file)

    msg = build_message(cfg, recipients, args.subject, body, args.attach)
    send(cfg, msg, args.dry_run)

    if not args.dry_run:
        print(
            f"OK: email sent to {len(recipients)} recipient(s) with "
            f"{len(args.attach)} attachment(s)."
        )


if __name__ == "__main__":
    main()
