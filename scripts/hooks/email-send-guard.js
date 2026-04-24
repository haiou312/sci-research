#!/usr/bin/env node

/**
 * Email Send Guard Hook
 *
 * PreToolUse:Bash matcher. Blocks inline SMTP / email-library implementations
 * invoked via Bash before they can send a message. Forces the orchestrator to
 * use the sanctioned scripts so the dual-filename Content-Disposition encoding
 * in `scripts/send-report-email.py` (and the briefing twin) is always applied.
 *
 * Observed failure (2026-04-24 Pipeline C): for 3 of 6 country reports the
 * orchestrator wrote inline `smtplib` / `email.message` code in a bash
 * heredoc / `python3 -c` instead of invoking `send-report-email.py`. Those
 * inline paths emitted only RFC 2231 `filename*=` — attachments arrived as
 * `noname` on the recipient's Exchange. Guards 7/8/9 inside the script never
 * fired because the script was never invoked.
 *
 * Allowlist (command containing one of these → pass):
 *   - `send-report-email.py`      (Pipelines C, E)
 *   - `send-briefing-email.py`    (Pipeline D)
 *
 * Blocklist (command contains any of these without allowlist match → exit 2):
 *   - `import smtplib` / `from smtplib`
 *   - `import email.mime|message` / `from email.mime|message`
 *   - `MIMEMultipart(` / `MIMEText(` / `MIMEBase(`
 *   - `EmailMessage()`
 *   - `smtplib.SMTP(` / `smtp.SMTP(`
 *   - Unix `sendmail -[stif]` / `mail -s `
 *
 * Exit codes:
 *   0 — pass
 *   2 — block (message surfaced to orchestrator so it retries with the script)
 */

function main() {
  let input = "";
  process.stdin.setEncoding("utf8");
  process.stdin.on("data", (chunk) => (input += chunk));
  process.stdin.on("end", () => {
    try {
      const data = JSON.parse(input);
      const cmd = data?.tool_input?.command || "";
      if (!cmd) {
        process.exit(0);
      }

      // Allowlist: if command clearly invokes a sanctioned script, pass through.
      // Also allow read-only inspection of the scripts (cat/grep/head/tail/less).
      if (/send-(?:report|briefing)-email\.py/.test(cmd)) {
        process.exit(0);
      }

      const blockPatterns = [
        { re: /\b(?:import|from)\s+smtplib\b/, why: "`smtplib` import" },
        {
          re: /\b(?:import|from)\s+email\.(?:mime|message)\b/,
          why: "`email.mime` / `email.message` import",
        },
        { re: /\bMIMEMultipart\s*\(/, why: "`MIMEMultipart(` constructor" },
        { re: /\bMIMEText\s*\(/, why: "`MIMEText(` constructor" },
        { re: /\bMIMEBase\s*\(/, why: "`MIMEBase(` constructor" },
        { re: /\bEmailMessage\s*\(\s*\)/, why: "`EmailMessage()` constructor" },
        { re: /\bsmtplib\.SMTP\s*\(/, why: "`smtplib.SMTP(` call" },
        {
          re: /(?:^|[;&|\s])sendmail\s+-[stif]/,
          why: "`sendmail` shell call",
        },
        { re: /(?:^|[;&|\s])mail\s+-s\s/, why: "`mail -s` shell call" },
      ];

      for (const { re, why } of blockPatterns) {
        if (re.test(cmd)) {
          const preview =
            cmd.length > 260 ? cmd.slice(0, 260) + "..." : cmd;
          const message = [
            "❌ Email Send Guard BLOCKED this Bash command.",
            "",
            `Detected inline email implementation: ${why}.`,
            "",
            "The sci-research plugin forbids inline SMTP / email-library sends " +
              "because they almost always skip the dual-filename " +
              "`Content-Disposition` encoding (RFC 2047 `filename=` + RFC 2231 " +
              "`filename*=`) required by corporate Exchange / Outlook. Without " +
              "both forms, recipients see attachments as `noname`.",
            "",
            "Use the sanctioned scripts instead:",
            "",
            "  Pipeline C (/daily-news-intelligence) and E (/reputation-track):",
            '    python3 "${CLAUDE_PLUGIN_ROOT}/scripts/send-report-email.py" \\',
            '      --to "..." --subject "..." --body-file "..." \\',
            '      --attach "..." "..."    # or --body-html-file for Pipeline E',
            "",
            "  Pipeline D (/daily-briefing):",
            '    python3 "${CLAUDE_PLUGIN_ROOT}/skills/daily-briefing/scripts/send-briefing-email.py" \\',
            '      --to "..." --subject "..." --body-file "..." --attach "..."',
            "",
            "These scripts handle env-var credentials, body encoding, " +
              "attachment filenames (Guards 7/8/9), and the required dual " +
              "Content-Disposition headers.",
            "",
            `Rejected command (truncated): ${preview}`,
          ].join("\n");
          process.stdout.write(
            JSON.stringify({ result: "block", message })
          );
          process.exit(2);
        }
      }

      process.exit(0);
    } catch (e) {
      // Never become a footgun — pass on internal errors.
      process.exit(0);
    }
  });
}

main();
