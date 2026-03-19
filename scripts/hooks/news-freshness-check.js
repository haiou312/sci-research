#!/usr/bin/env node

/**
 * News Freshness Check Hook
 *
 * Validates that a news analysis report contains sufficiently recent sources.
 * Checks for date patterns in the output and warns if no sources are from
 * the last 7 days.
 *
 * Exit codes:
 *   0 — pass (fresh sources found or not a news report)
 *   2 — warn (no recent sources detected)
 */

function main() {
  let input = "";

  process.stdin.setEncoding("utf8");
  process.stdin.on("data", (chunk) => {
    input += chunk;
  });

  process.stdin.on("end", () => {
    try {
      const data = JSON.parse(input);

      const filePath = data?.tool_input?.file_path || "";
      // Only check files that look like news reports
      if (
        !filePath.match(/news.*\.md$/i) &&
        !filePath.match(/新闻.*\.md$/i)
      ) {
        process.exit(0);
      }

      const content = data?.tool_input?.content || "";
      if (!content) {
        process.exit(0);
      }

      // Extract dates from the content (YYYY-MM-DD format)
      const datePattern = /\b(20\d{2})[-\/](0[1-9]|1[0-2])[-\/](0[1-9]|[12]\d|3[01])\b/g;
      const dates = [];
      let match;
      while ((match = datePattern.exec(content)) !== null) {
        dates.push(new Date(match[0]));
      }

      if (dates.length === 0) {
        const msg =
          "⚠️ NEWS FRESHNESS: No date-stamped sources found in the report. Ensure all news items include publication dates (YYYY-MM-DD).";
        process.stdout.write(JSON.stringify({ result: "warn", message: msg }));
        process.exit(2);
      }

      // Check if any date is within the last 7 days
      const now = new Date();
      const sevenDaysAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
      const recentDates = dates.filter((d) => d >= sevenDaysAgo);

      if (recentDates.length === 0) {
        const mostRecent = new Date(Math.max(...dates.map((d) => d.getTime())));
        const daysAgo = Math.floor(
          (now.getTime() - mostRecent.getTime()) / (1000 * 60 * 60 * 24)
        );
        const msg = `⚠️ NEWS FRESHNESS: No sources from the last 7 days. Most recent source is from ${daysAgo} days ago (${mostRecent.toISOString().split("T")[0]}). Consider searching for more recent coverage.`;
        process.stdout.write(JSON.stringify({ result: "warn", message: msg }));
        process.exit(2);
      }

      process.stdout.write(
        JSON.stringify({
          result: "pass",
          message: `✅ News freshness OK: ${recentDates.length} source(s) from the last 7 days. Total dated sources: ${dates.length}.`,
        })
      );
      process.exit(0);
    } catch (e) {
      // Don't block on parse errors
      process.exit(0);
    }
  });
}

main();
