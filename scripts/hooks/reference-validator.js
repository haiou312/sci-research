#!/usr/bin/env node

/**
 * Reference Validator Hook
 *
 * Validates that every inline citation [N] in the article body has a
 * corresponding entry in the References section, and that no reference
 * entries are orphaned (never cited).
 *
 * Exit codes:
 *   0 — pass
 *   2 — block (broken references)
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

      // Early exit for plugin-internal files (agents, skills, commands, config, docs)
      if (
        filePath.match(/\/(agents|commands|skills|\.claude-plugin|hooks|scripts|rules|contexts|examples)\//) ||
        filePath.match(/\/(README|CLAUDE|AGENTS|LICENSE)\.md$/i)
      ) {
        process.exit(0);
      }

      // Only check files that look like deep-research article outputs
      if (
        !filePath.match(/(?:deep-research|research-report|研究报告|research-article)[^/]*\.md$/i) &&
        !filePath.match(/研究.*\.md$/i)
      ) {
        process.exit(0);
      }

      const content = data?.tool_input?.content || "";
      if (!content) {
        process.exit(0);
      }

      // Find the References section
      const refSectionMatch = content.match(
        /##\s*(?:参考文献|References)[\s\S]*$/i
      );
      if (!refSectionMatch) {
        process.stdout.write(
          JSON.stringify({
            result: "warn",
            message: "⚠️ No References section found in the article.",
          })
        );
        process.exit(2);
      }

      const refSection = refSectionMatch[0];
      const bodySection = content.substring(
        0,
        content.indexOf(refSectionMatch[0])
      );

      // Extract inline citations from body: [1], [2], [3]
      const inlineCitations = new Set();
      const inlineMatches = bodySection.match(/\[(\d+)\]/g) || [];
      for (const match of inlineMatches) {
        const num = parseInt(match.replace(/[\[\]]/g, ""));
        if (num > 0 && num < 200) {
          inlineCitations.add(num);
        }
      }

      // Extract reference entries: [1], [2], etc. at line start
      const refEntries = new Set();
      const refMatches = refSection.match(/^\s*\[(\d+)\]/gm) || [];
      for (const match of refMatches) {
        const num = parseInt(match.replace(/[\[\]\s]/g, ""));
        if (num > 0 && num < 200) {
          refEntries.add(num);
        }
      }

      // Find mismatches
      const uncitedRefs = [...refEntries].filter(
        (n) => !inlineCitations.has(n)
      );
      const missingRefs = [...inlineCitations].filter(
        (n) => !refEntries.has(n)
      );

      const issues = [];

      if (missingRefs.length > 0) {
        issues.push(
          `Missing reference entries for citations: [${missingRefs.sort((a, b) => a - b).join("], [")}]`
        );
      }

      if (uncitedRefs.length > 0) {
        issues.push(
          `Orphaned references (never cited in body): [${uncitedRefs.sort((a, b) => a - b).join("], [")}]`
        );
      }

      if (issues.length > 0) {
        const msg = `⚠️ REFERENCE INTEGRITY ISSUES:\n${issues.join("\n")}`;
        process.stdout.write(JSON.stringify({ result: "warn", message: msg }));
        process.exit(2);
      }

      process.stdout.write(
        JSON.stringify({
          result: "pass",
          message: `✅ Reference integrity OK: ${inlineCitations.size} citations, ${refEntries.size} reference entries, all matched.`,
        })
      );
      process.exit(0);
    } catch (e) {
      process.exit(0);
    }
  });
}

main();
