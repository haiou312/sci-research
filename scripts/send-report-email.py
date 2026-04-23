#!/usr/bin/env python3
"""
Send sci-research pipeline reports via Gmail SMTP.

Supports three body modes (mutually exclusive, exactly one required):
  --body          plain text inline
  --body-file     plain text from file (used by Pipelines C / D)
  --body-html-file  HTML from file → builds multipart/alternative with auto
                  text/plain fallback (used by reputation-track / Pipeline E)

Reads credentials from environment variables:
  GOOGLE_EMAIL_USERNAME        — Gmail address (e.g. user@gmail.com)
  GOOGLE_EMAIL_APP_PASSWORD    — Gmail app password (16 chars, not account password)
  GOOGLE_EMAIL_FROM_NAME       — optional display name for the From header
  GOOGLE_EMAIL_HOST            — SMTP host (default: smtp.gmail.com)
  GOOGLE_EMAIL_PORT            — SMTP port (default: 587)
  GOOGLE_EMAIL_START_TLS       — 'true' to use STARTTLS on port 587 (default: true)

Usage:
  # Text body + attachments (Pipelines C / D)
  send-report-email.py \\
    --to "alice@foo.com,bob@bar.com" \\
    --subject "中国每日热点新闻 — 2026年4月14日" \\
    --body-file /tmp/body.txt \\
    --attach /path/to/report.md /path/to/report.docx \\
    [--dry-run]

  # HTML body, no attachment (reputation-track)
  send-report-email.py \\
    --to "risk@foo.com" \\
    --subject "[Reputation Alert] Acme — 2026-04-21" \\
    --body-html-file /tmp/report.html \\
    [--dry-run]

Exit codes:
  0 — success or dry-run completed
  1 — missing required environment variables
  2 — no recipients specified
  3 — SMTP connection or send failure
  4 — attachment file not found
  5 — body file not found
  6 — no content to send (neither --attach nor --body-html-file provided, when using a plain-text body)
  7 — attachment has an empty filename stem (e.g. ".docx", "   .docx")
  8 — attachment has no file extension (e.g. "briefing" with no suffix)
  9 — Content-Disposition header is missing the dual filename= / filename*= encoding (script-internal regression guard)
"""

import argparse
import mimetypes
import os
import re
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


def read_html_body(html_file):
    """Read an HTML body file. Exit 5 if missing."""
    p = Path(html_file).expanduser()
    if not p.exists():
        print(f"ERROR: body HTML file not found: {p}", file=sys.stderr)
        sys.exit(5)
    return p.read_text(encoding="utf-8")


def html_to_text(html):
    """Generate a readable text/plain fallback from an HTML body.

    Purpose is the multipart/alternative text fallback for mail clients that
    don't render HTML — not a perfect round-trip. Strips script/style blocks,
    converts common block-ending tags to newlines, decodes a handful of
    entities, and collapses whitespace.
    """
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</(p|div|h[1-6]|li|tr|blockquote)>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    entities = {
        "&nbsp;": " ", "&amp;": "&", "&lt;": "<", "&gt;": ">",
        "&quot;": '"', "&#39;": "'", "&apos;": "'",
        "&ldquo;": '"', "&rdquo;": '"', "&lsquo;": "'", "&rsquo;": "'",
        "&middot;": "·", "&mdash;": "—", "&ndash;": "–",
    }
    for k, v in entities.items():
        text = text.replace(k, v)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def build_message(cfg, recipients, subject, body_text, attachments, body_html=None):
    """Construct a MIMEMultipart("mixed") message.

    When `body_html` is provided, the body becomes a multipart/alternative
    containing both text/plain (auto-generated fallback) and text/html. When
    body_html is None, a single text/plain part is attached (legacy path for
    Pipelines C / D).

    Attachment filenames use both RFC 2047 `filename=` and RFC 2231
    `filename*=` so non-ASCII names survive corporate Exchange clients.
    """
    msg = MIMEMultipart("mixed")
    from_name = cfg["from_name"] or cfg["user"]
    msg["From"] = f'"{from_name}" <{cfg["user"]}>'
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject

    if body_html:
        alt = MIMEMultipart("alternative")
        alt.attach(MIMEText(body_text, "plain", "utf-8"))
        alt.attach(MIMEText(body_html, "html", "utf-8"))
        msg.attach(alt)
    else:
        msg.attach(MIMEText(body_text, "plain", "utf-8"))

    for path in attachments:
        p = Path(path).expanduser()
        if not p.exists():
            print(f"ERROR: attachment not found: {p}", file=sys.stderr)
            sys.exit(4)

        # Guard 1: reject files whose basename stem is empty or whitespace-only.
        # e.g. "/tmp/.docx" → stem="", "/tmp/   .docx" → stem="   ". Mail
        # clients show these as "noname" even with correct MIME encoding.
        if not p.stem.strip():
            print(
                f"ERROR: attachment {p.name!r} has an empty filename stem. "
                f"Mail clients cannot render this. Check your out_md/out_docx "
                f"construction — the filename must have a non-empty name before "
                f"the extension.",
                file=sys.stderr,
            )
            sys.exit(7)

        # Guard 2: reject files with no extension. Mail clients key off the
        # extension (and Content-Type) to decide how to display / open.
        if not p.suffix:
            print(
                f"ERROR: attachment {p.name!r} has no file extension. "
                f"Mail clients need an extension (.md, .docx, .pdf, ...) to "
                f"render the attachment. Check pandoc output or slug construction.",
                file=sys.stderr,
            )
            sys.exit(8)

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

        # Guard 3: regression check. Verify the dual-filename encoding is
        # actually present in the Content-Disposition header we just set.
        # Catches future refactors that might drop one of the two forms.
        cd = part.get("Content-Disposition", "")
        if 'filename="' not in cd or "filename*=" not in cd:
            print(
                f"ERROR: Content-Disposition header for {p.name!r} is missing "
                f"the dual-filename encoding (RFC 2047 filename= AND RFC 2231 "
                f"filename*=). Got: {cd!r}. This is a script-internal regression "
                f"— both forms are required so attachments don't become "
                f'"noname" on corporate Exchange / Outlook.',
                file=sys.stderr,
            )
            sys.exit(9)

        msg.attach(part)

    return msg


def send(cfg, msg, dry_run):
    """Send the message via SMTP, or print a summary if dry-run."""
    if dry_run:
        print("=== DRY RUN — message NOT sent ===")
        print(f"SMTP host: {cfg['host']}:{cfg['port']} (starttls={cfg['starttls']})")
        print(f"From: {msg['From']}")
        print(f"To: {msg['To']}")
        print(f"Subject: {msg['Subject']}")
        attachment_names = []
        body_text = ""
        html_len = 0
        for part in msg.walk():
            fn = part.get_filename()
            if fn:
                attachment_names.append(str(make_header(decode_header(fn))))
                continue
            ctype = part.get_content_type()
            if ctype == "text/plain" and not body_text:
                body_text = part.get_payload(decode=True).decode("utf-8", errors="replace")
            elif ctype == "text/html":
                payload = part.get_payload(decode=True)
                if payload:
                    html_len = len(payload.decode("utf-8", errors="replace"))
        print(f"Attachments ({len(attachment_names)}): {attachment_names}")
        print(f"HTML body: {'yes, ' + str(html_len) + ' chars' if html_len else 'no'}")
        if body_text:
            body_preview = body_text[:800]
            src = "auto-stripped from HTML" if html_len else "text body"
            print(f"--- text preview ({src}) ---")
            print(body_preview)
            if len(body_text) > 800:
                print(f"... (body truncated, total {len(body_text)} chars)")
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
    body_group.add_argument(
        "--body-html-file",
        help=(
            "Path to an HTML file used as the email body. Builds a "
            "multipart/alternative with an auto-generated text/plain fallback. "
            "Used by reputation-track (Pipeline E)."
        ),
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

    if not args.attach and not args.body_html_file:
        print(
            "ERROR: no content to send. Provide --attach <paths> (Pipelines C/D) "
            "or --body-html-file (reputation-track / Pipeline E). Refusing to "
            "send an email with only a plain-text body and no attachments.",
            file=sys.stderr,
        )
        sys.exit(6)

    cfg = load_env()
    recipients = parse_recipients(args.to)

    if args.body_html_file:
        body_html = read_html_body(args.body_html_file)
        body = html_to_text(body_html)
    else:
        body_html = None
        body = read_body(args.body, args.body_file)

    msg = build_message(cfg, recipients, args.subject, body, args.attach, body_html=body_html)
    send(cfg, msg, args.dry_run)

    if not args.dry_run:
        body_kind = "html" if body_html else "text"
        print(
            f"OK: email sent to {len(recipients)} recipient(s) "
            f"(body={body_kind}, attachments={len(args.attach)})."
        )


if __name__ == "__main__":
    main()
