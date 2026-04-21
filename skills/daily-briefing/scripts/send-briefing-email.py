#!/usr/bin/env python3
"""
Send daily briefing report via Gmail SMTP.

Independent email script for the daily-briefing pipeline.
Uses MIMEMultipart("mixed") with RFC 2231 CJK filename encoding.

Reads credentials from environment variables:
  GOOGLE_EMAIL_USERNAME        — Gmail address
  GOOGLE_EMAIL_APP_PASSWORD    — Gmail app password (16 chars)
  GOOGLE_EMAIL_FROM_NAME       — optional display name
  GOOGLE_EMAIL_HOST            — SMTP host (default: smtp.gmail.com)
  GOOGLE_EMAIL_PORT            — SMTP port (default: 587)
  GOOGLE_EMAIL_START_TLS       — 'true' for STARTTLS (default: true)

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
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders
from email.header import Header, decode_header, make_header
from email.utils import encode_rfc2231
from pathlib import Path

REQUIRED_ENV = ["GOOGLE_EMAIL_USERNAME", "GOOGLE_EMAIL_APP_PASSWORD"]
EMAIL_RE = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


def load_env():
    missing = [k for k in REQUIRED_ENV if not os.environ.get(k)]
    if missing:
        print(f"ERROR: missing env vars: {', '.join(missing)}", file=sys.stderr)
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
    import re
    recipients = [r.strip() for r in raw.split(",") if r.strip()]
    if not recipients:
        print("ERROR: no recipients specified", file=sys.stderr)
        sys.exit(2)
    invalid = [r for r in recipients if not re.match(EMAIL_RE, r)]
    if invalid:
        print(f"ERROR: invalid email format: {invalid}", file=sys.stderr)
        sys.exit(2)
    return recipients


def read_body(body_text, body_file):
    if body_file:
        p = Path(body_file).expanduser()
        if not p.exists():
            print(f"ERROR: body file not found: {p}", file=sys.stderr)
            sys.exit(5)
        return p.read_text(encoding="utf-8")
    return body_text or ""


def build_message(cfg, recipients, subject, body, attachments):
    msg = MIMEMultipart("mixed")
    from_name = cfg["from_name"] or cfg["user"]
    msg["From"] = f'"{from_name}" <{cfg["user"]}>'
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    for path in attachments:
        p = Path(path).expanduser()
        if not p.exists():
            print(f"ERROR: attachment not found: {p}", file=sys.stderr)
            sys.exit(4)
        ctype, encoding = mimetypes.guess_type(str(p))
        if ctype is None or encoding is not None:
            ctype = "application/octet-stream"
        maintype, subtype = ctype.split("/", 1)
        part = MIMEBase(maintype, subtype)
        with open(p, "rb") as f:
            part.set_payload(f.read())
        encoders.encode_base64(part)
        # Emit BOTH filename= (RFC 2047) and filename*= (RFC 2231) so non-ASCII
        # filenames survive corporate Exchange/Outlook, which drop attachments
        # as "noname" when only the RFC 2231 extended form is present.
        legacy = Header(p.name, "utf-8").encode()
        extended = encode_rfc2231(p.name, "utf-8")
        part.add_header(
            "Content-Disposition",
            f'attachment; filename="{legacy}"; filename*={extended}',
        )
        msg.attach(part)
    return msg


def send(cfg, msg, dry_run):
    if dry_run:
        print("=== DRY RUN — message NOT sent ===")
        print(f"From: {msg['From']}")
        print(f"To: {msg['To']}")
        print(f"Subject: {msg['Subject']}")
        names = []
        body_text = ""
        for part in msg.walk():
            fn = part.get_filename()
            if fn:
                names.append(str(make_header(decode_header(fn))))
            elif part.get_content_type() == "text/plain" and not body_text:
                body_text = part.get_payload(decode=True).decode("utf-8", errors="replace")
        print(f"Attachments ({len(names)}): {names}")
        if body_text:
            print("--- body preview ---")
            print(body_text[:800])
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
        print(f"ERROR: SMTP auth failed: {e.smtp_code}", file=sys.stderr)
        sys.exit(3)
    except (smtplib.SMTPException, ConnectionError, TimeoutError, OSError) as e:
        print(f"ERROR: SMTP failed: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(3)


def main():
    parser = argparse.ArgumentParser(description="Send daily briefing via Gmail SMTP.")
    parser.add_argument("--to", required=True, help="Comma-separated recipients")
    parser.add_argument("--subject", required=True, help="Email subject")
    body_group = parser.add_mutually_exclusive_group(required=True)
    body_group.add_argument("--body", help="Plain-text body")
    body_group.add_argument("--body-file", help="Path to body text file")
    parser.add_argument("--attach", nargs="*", default=[], help="File paths to attach")
    parser.add_argument("--dry-run", action="store_true", help="Preview without sending")
    args = parser.parse_args()

    cfg = load_env()
    recipients = parse_recipients(args.to)
    body = read_body(args.body, args.body_file)
    msg = build_message(cfg, recipients, args.subject, body, args.attach)
    send(cfg, msg, args.dry_run)

    if not args.dry_run:
        print(f"OK: email sent to {len(recipients)} recipient(s) with {len(args.attach)} attachment(s).")


if __name__ == "__main__":
    main()
