#!/usr/bin/env node

/**
 * Research Summary Hook (Stop event)
 *
 * Logs research session metadata to a summary file for tracking.
 * Runs asynchronously after each response — non-blocking.
 *
 * Exit codes:
 *   0 — always (non-blocking)
 */

const fs = require("fs");
const path = require("path");

function main() {
  let input = "";

  process.stdin.setEncoding("utf8");
  process.stdin.on("data", (chunk) => {
    input += chunk;
  });

  process.stdin.on("end", () => {
    try {
      const data = JSON.parse(input);
      const transcript = data?.transcript_path;

      if (!transcript) {
        process.exit(0);
      }

      // Log session info
      const logDir = path.join(
        process.env.HOME || process.env.USERPROFILE || ".",
        ".sci-research",
        "sessions"
      );

      if (!fs.existsSync(logDir)) {
        fs.mkdirSync(logDir, { recursive: true });
      }

      const logEntry = {
        timestamp: new Date().toISOString(),
        transcript_path: transcript,
        plugin: "sci-research",
      };

      const logFile = path.join(logDir, "session-log.jsonl");
      fs.appendFileSync(logFile, JSON.stringify(logEntry) + "\n");

      process.exit(0);
    } catch (e) {
      process.exit(0);
    }
  });
}

main();
