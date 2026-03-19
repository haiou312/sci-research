#!/usr/bin/env node

/**
 * Entity Coverage Check Hook
 *
 * Verifies that all user-specified comparison entities appear substantively
 * in the written article (not just mentioned once, but have dedicated sections).
 *
 * Exit codes:
 *   0 — pass
 *   2 — block (missing entity coverage)
 */

const fs = require("fs");

// Minimum mentions for "substantive coverage"
const MIN_MENTIONS = 3;
// Minimum section heading appearances
const MIN_SECTION_HEADINGS = 1;

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
      if (!filePath.match(/research.*\.md$/i) && !filePath.match(/研究.*\.md$/i)) {
        process.exit(0);
      }

      const content = data?.tool_input?.content || "";
      if (!content) {
        process.exit(0);
      }

      // Try to extract entities from the article header or metadata
      // Look for patterns like "比较实体:" or "Entities:" in the first 500 chars
      const header = content.substring(0, 1000);
      const entityMatch =
        header.match(/比较实体[：:]\s*(.+)/i) ||
        header.match(/entities[：:]\s*(.+)/i) ||
        header.match(/实体选取[：:]\s*(.+)/i);

      if (!entityMatch) {
        // Can't determine entities, skip check
        process.exit(0);
      }

      const entities = entityMatch[1]
        .split(/[,，、]/)
        .map((e) => e.trim())
        .filter(Boolean);

      const missingEntities = [];

      for (const entity of entities) {
        // Check for section headings containing the entity name
        const headingRegex = new RegExp(`^#{2,3}\\s.*${escapeRegex(entity)}`, "gmi");
        const headingMatches = content.match(headingRegex) || [];

        // Check for total mentions
        const mentionRegex = new RegExp(escapeRegex(entity), "gi");
        const mentionMatches = content.match(mentionRegex) || [];

        if (
          headingMatches.length < MIN_SECTION_HEADINGS ||
          mentionMatches.length < MIN_MENTIONS
        ) {
          missingEntities.push({
            entity,
            headings: headingMatches.length,
            mentions: mentionMatches.length,
          });
        }
      }

      if (missingEntities.length > 0) {
        const details = missingEntities
          .map(
            (e) =>
              `"${e.entity}" (headings: ${e.headings}, mentions: ${e.mentions})`
          )
          .join(", ");
        const msg = `⚠️ ENTITY COVERAGE GAP: The following entities lack substantive coverage: ${details}. Each entity needs ≥${MIN_SECTION_HEADINGS} section heading and ≥${MIN_MENTIONS} mentions.`;
        process.stdout.write(JSON.stringify({ result: "warn", message: msg }));
        process.exit(2);
      }

      process.stdout.write(
        JSON.stringify({
          result: "pass",
          message: `✅ All ${entities.length} entities have substantive coverage.`,
        })
      );
      process.exit(0);
    } catch (e) {
      process.exit(0);
    }
  });
}

function escapeRegex(str) {
  return str.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

main();
