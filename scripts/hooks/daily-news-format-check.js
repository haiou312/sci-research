#!/usr/bin/env node

/**
 * Daily News Format Check Hook
 *
 * Validates Pipeline C (/daily-news-intelligence) Markdown output format.
 * Catches the failure modes observed across multiple runs where the Writer
 * deviates from `skills/daily-news-intelligence/references/output-spec.md`:
 *
 *   - Global `## 参考文献` / `## References` / `## Sources` H2 section
 *   - `> **来源**:` blockquote replacing **References** block
 *   - `*来源：Author (Year); ...*` italic in-text citation shortcut
 *   - Per-story **References** block missing
 *   - References without [N] continuous numbering
 *   - References lines without a URL
 *   - Mismatched count between ### story titles, **摘要** markers, **References** blocks
 *
 * Trigger: PostToolUse:Write when the file path is under daily-news-reports/
 *          OR when the content's H1 matches the daily-news H1 pattern
 *          (covers all three supported languages: zh / en / ja).
 *
 * Exit codes:
 *   0 — pass (format compliant, or not our concern)
 *   2 — block (format violation; print details on stdout)
 */

const fs = require("fs");

// ---------- helpers ----------

function isDailyNewsReport(filePath, content) {
  // skip backups and non-md files
  if (filePath.endsWith(".bak") || !filePath.endsWith(".md")) return false;
  const byPath = /daily-news-reports\//.test(filePath);
  const byH1 = /^# [^\n]*(?:每日热点新闻|Daily News Intelligence|デイリーニュース)/m.test(
    content
  );
  return byPath || byH1;
}

function isPluginInternal(filePath) {
  // Plugin-internal files may contain sample Markdown (examples, docs) — never check
  if (
    filePath.match(
      /\/(agents|commands|skills|\.claude-plugin|hooks|scripts|rules|contexts|examples)\//
    ) ||
    filePath.match(/\/(README|CLAUDE|AGENTS|LICENSE)\.md$/i)
  ) {
    return true;
  }
  return false;
}

// Section/marker variants across supported languages.
// section_5 is the last H2 in the body; the pattern for lang=zh is "五、其他重要事件".
const SUMMARY_MARKERS = /^\*\*(?:摘要|Summary|要約)\*\*$/gm;
const REFERENCES_MARKER_LINE = "**References**"; // language-independent per spec
const ANALYSIS_MARKERS = /^\*\*(?:分析|Analysis)\*\*$/gm;

function countMatches(content, regex) {
  return (content.match(regex) || []).length;
}

// Extract reference lines per block: lines after each **References** marker
// until the next heading or separator.
function collectReferenceLines(content) {
  const lines = content.split("\n");
  const blocks = []; // array of arrays of trimmed non-empty lines
  let inRefs = false;
  let current = [];
  const endMarkers = new Set([
    "---",
    "**摘要**",
    "**Summary**",
    "**要約**",
    "**分析**",
    "**Analysis**",
  ]);
  for (const raw of lines) {
    const line = raw.trim();
    if (line === REFERENCES_MARKER_LINE) {
      if (inRefs) {
        blocks.push(current);
      }
      inRefs = true;
      current = [];
      continue;
    }
    if (!inRefs) continue;
    // end when we hit a new heading or a separator or another structural marker
    if (line.startsWith("# ") || line.startsWith("## ") || line.startsWith("### ")) {
      blocks.push(current);
      current = [];
      inRefs = false;
      continue;
    }
    if (endMarkers.has(line)) {
      blocks.push(current);
      current = [];
      inRefs = false;
      continue;
    }
    if (line === "") continue;
    current.push(line);
  }
  if (inRefs) blocks.push(current);
  return blocks;
}

// ---------- main validation ----------

function validate(filePath, content) {
  const violations = [];

  // 1. Count invariants: ### == 摘要 == **References**
  const h3Count = countMatches(content, /^### /gm);
  const summaryCount = countMatches(content, SUMMARY_MARKERS);
  const refsBlockCount = countMatches(
    content,
    /^\*\*References\*\*$/gm
  );
  if (
    h3Count === 0 ||
    h3Count !== summaryCount ||
    h3Count !== refsBlockCount
  ) {
    violations.push(
      `Count mismatch: ### headings=${h3Count}, 摘要/Summary/要約 markers=${summaryCount}, **References** blocks=${refsBlockCount}. Each story must have exactly one of each.`
    );
  }

  // 2. No global H2 refs section
  const globalRefs = content.match(
    /^##\s*(参考文献|References|Sources)\s*$/gm
  );
  if (globalRefs) {
    violations.push(
      `Prohibited global refs section found (${globalRefs.length} instance[s]): ${globalRefs.join(
        " / "
      )}. Refs must be per-story in **References** blocks, not a trailing global list.`
    );
  }

  // 3. No blockquote 来源 style
  const bq = content.match(/^>\s*\*\*(?:来源|Source|Sources)\*\*/gm);
  if (bq) {
    violations.push(
      `Prohibited blockquote source style found (${bq.length} instance[s]). Replace \`> **来源**: ...\` with \`**References**\\n\\n[N] ...\`.`
    );
  }

  // 4. No italic in-text short citation
  const italic = content.match(/^\*\s*(?:来源|Sources?)[:：]/gm);
  if (italic) {
    violations.push(
      `Prohibited italic in-text citation found (${italic.length} instance[s]). \`*来源：Author (Year); ...*\` is forbidden — every reference must be a full APA line inside a per-story **References** block.`
    );
  }

  // 5. [N] numbering continuous from 1 across all references blocks
  // 6. Every reference line must contain a URL
  const blocks = collectReferenceLines(content);
  const refLines = blocks.flat();
  const expected = [];
  const badFormat = [];
  const missingUrl = [];
  for (const line of refLines) {
    const m = line.match(/^\[(\d+)\]\s+(.+)$/);
    if (!m) {
      badFormat.push(line);
      continue;
    }
    expected.push(parseInt(m[1], 10));
    if (!/https?:\/\//.test(m[2])) {
      missingUrl.push(line);
    }
  }

  if (badFormat.length > 0) {
    violations.push(
      `${badFormat.length} reference line[s] missing [N] prefix. First offender: "${badFormat[0].slice(
        0,
        120
      )}"`
    );
  }
  // only meaningful if we have valid [N]-prefixed lines
  if (expected.length > 0) {
    for (let i = 0; i < expected.length; i++) {
      if (expected[i] !== i + 1) {
        violations.push(
          `[N] numbering not continuous from 1. Expected [${i + 1}] at position ${
            i + 1
          }, found [${expected[i]}]. Full sequence start: [${expected.slice(0, 10).join("], [")}]`
        );
        break;
      }
    }
  }
  if (missingUrl.length > 0) {
    violations.push(
      `${missingUrl.length} reference line[s] missing URL. Every reference must include a bare https:// URL. First offender: "${missingUrl[0].slice(
        0,
        160
      )}"`
    );
  }

  return violations;
}

// ---------- hook entry ----------

function main() {
  let input = "";
  process.stdin.setEncoding("utf8");
  process.stdin.on("data", (chunk) => (input += chunk));
  process.stdin.on("end", () => {
    try {
      const data = JSON.parse(input);
      const filePath = data?.tool_input?.file_path || "";
      const content = data?.tool_input?.content || "";

      if (!filePath || !content) {
        process.exit(0);
      }
      if (isPluginInternal(filePath)) {
        process.exit(0);
      }
      if (!isDailyNewsReport(filePath, content)) {
        process.exit(0);
      }

      const violations = validate(filePath, content);
      if (violations.length === 0) {
        process.stdout.write(
          JSON.stringify({
            result: "pass",
            message: `✅ daily-news format check passed: ${filePath}`,
          })
        );
        process.exit(0);
      }

      const message = [
        `❌ daily-news format check FAILED for ${filePath}`,
        `Pipeline C Markdown must match skills/daily-news-intelligence/references/output-spec.md.`,
        ``,
        ...violations.map((v, i) => `  ${i + 1}. ${v}`),
        ``,
        `Fix the output and write again. This hook blocks the Write to prevent malformed reports from being emailed.`,
      ].join("\n");
      process.stdout.write(
        JSON.stringify({ result: "block", message })
      );
      process.exit(2);
    } catch (e) {
      // don't block on parse/logic errors — the hook must never become a footgun
      process.stdout.write(
        JSON.stringify({ result: "pass", message: `daily-news-format-check internal error: ${e.message}` })
      );
      process.exit(0);
    }
  });
}

main();
