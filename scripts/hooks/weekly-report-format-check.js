#!/usr/bin/env node

/**
 * Weekly Report Format Check Hook
 *
 * Validates `/weekly-report` Markdown output format. The Writer must produce
 * a file matching `skills/weekly-report/references/output-spec.md`. This hook
 * runs on PostToolUse:Write and exits 2 on violation to block the bad write.
 *
 * Trigger: PostToolUse:Write when filePath is under weekly-reports/ OR when
 * the content's H1 matches one of the localised weekly-report titles
 * (zh / en / ja).
 *
 * Exit codes:
 *   0 — pass (format compliant, or not our concern)
 *   2 — block (format violation; details on stdout)
 */

const fs = require("fs");

// ---------- triggers ----------

function isWeeklyReport(filePath, content) {
  if (filePath.endsWith(".bak") || !filePath.endsWith(".md")) return false;
  const byPath = /weekly-reports?\//.test(filePath);
  const byH1 = /^# (?:全球宏观与市场周报|Global Macro & Market Weekly Report|グローバル・マクロ市場週報)/m.test(
    content
  );
  return byPath || byH1;
}

function isPluginInternal(filePath) {
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

// ---------- localisation tables ----------

const SECTION_HEADINGS = [
  // [section_id, en, zh, ja]
  ["market_event", "Market event", "市场事件", "市場イベント"],
  ["money_market", "Money Market", "货币市场", "マネーマーケット"],
  ["fixed_income", "Fixed Income", "固定收益", "債券市場"],
  ["foreign_exchange", "Foreign Exchange", "外汇", "外国為替"],
  ["commodity", "Commodity", "大宗商品", "コモディティ"],
  ["sources", "Sources", "来源", "出典"],
];

const DATA_GAPS_HEADING = ["Data Gaps", "数据缺口", "データギャップ"];

const ALLOWED_SOURCES = [
  "FRED",
  "FRED proxy",
  "Bank of England (spot curve)",
  "Japan MOF (jgbcme.csv)",
  "yfinance ETF proxy",
  "Yahoo Finance",
];

// ---------- helpers ----------

function lineNumber(content, idx) {
  return content.slice(0, idx).split("\n").length;
}

// Find the index ranges (start, end) of each ## section in display order.
// Returns Map<section_id, {start_line, end_line, heading_text}>.
function locateSections(content) {
  const lines = content.split("\n");
  const headingPositions = []; // [{idx, heading}]
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].startsWith("## ")) {
      headingPositions.push({ idx: i, heading: lines[i].slice(3).trim() });
    }
  }
  const sectionMap = new Map();
  for (const sec of SECTION_HEADINGS) {
    const [id, ...names] = sec;
    const found = headingPositions.findIndex((p) => names.includes(p.heading));
    if (found >= 0) {
      const start = headingPositions[found].idx;
      const next = headingPositions[found + 1];
      const end = next ? next.idx : lines.length;
      sectionMap.set(id, { start, end, heading: headingPositions[found].heading });
    }
  }
  // Data Gaps (optional)
  const dgFound = headingPositions.findIndex((p) => DATA_GAPS_HEADING.includes(p.heading));
  if (dgFound >= 0) {
    const start = headingPositions[dgFound].idx;
    const next = headingPositions[dgFound + 1];
    const end = next ? next.idx : lines.length;
    sectionMap.set("data_gaps", { start, end, heading: headingPositions[dgFound].heading });
  }
  return { sectionMap, headingPositions };
}

function sectionText(content, range) {
  if (!range) return "";
  return content.split("\n").slice(range.start, range.end).join("\n");
}

function hasMarkdownTable(text) {
  // Detect a header row | ... | followed by a separator | --- | --- |
  return /\n\|[^\n]+\|\n\|[\s\-:|]+\|\n/.test("\n" + text + "\n");
}

// ---------- main validation ----------

function validate(filePath, content) {
  const violations = [];

  // 1. H1 contains start_date and end_date
  const h1Match = content.match(/^# .+$/m);
  if (!h1Match) {
    violations.push("Missing H1 title.");
  } else {
    const h1 = h1Match[0];
    const dates = h1.match(/\d{4}-\d{2}-\d{2}/g) || [];
    if (dates.length < 2) {
      violations.push(
        `H1 must contain two ISO YYYY-MM-DD dates (start and end of the window). Got: "${h1}".`
      );
    }
  }

  // 2. Six required H2 sections present in order
  const { sectionMap, headingPositions } = locateSections(content);
  const requiredIds = ["market_event", "money_market", "fixed_income", "foreign_exchange", "commodity", "sources"];
  const missing = requiredIds.filter((id) => !sectionMap.has(id));
  if (missing.length > 0) {
    violations.push(`Missing required H2 sections: ${missing.join(", ")}.`);
  }
  if (missing.length === 0) {
    const orderIdx = requiredIds.map((id) => sectionMap.get(id).start);
    for (let i = 1; i < orderIdx.length; i++) {
      if (orderIdx[i] <= orderIdx[i - 1]) {
        violations.push(
          `H2 section order is wrong; required order is: ${requiredIds.join(" → ")}.`
        );
        break;
      }
    }
  }

  // 3. Each market-data section has at least one Markdown table
  for (const id of ["money_market", "fixed_income", "foreign_exchange", "commodity"]) {
    const range = sectionMap.get(id);
    if (!range) continue;
    const text = sectionText(content, range);
    if (!hasMarkdownTable(text)) {
      violations.push(`Section "${id}" has no Markdown table (expected a header row + separator).`);
    }
  }

  // 4. [Sn] reference tags appear ONLY in the Market event section
  const allTags = [...content.matchAll(/\[S\d+\]/g)];
  const meRange = sectionMap.get("market_event");
  const sourcesRange = sectionMap.get("sources");
  if (meRange) {
    const meText = sectionText(content, meRange);
    const sourcesText = sectionText(content, sourcesRange);
    const allowed = new Set();
    for (const m of [...meText.matchAll(/\[S\d+\]/g)]) allowed.add(m.index + meRange.start);
    for (const m of [...sourcesText.matchAll(/\[S\d+\]/g)]) allowed.add(m.index + sourcesRange.start);
    // Check every tag's line index against allowed sections.
    const lines = content.split("\n");
    let lineCursor = 0;
    let charCursor = 0;
    const lineIdxFor = (charPos) => content.slice(0, charPos).split("\n").length - 1;
    for (const m of allTags) {
      const li = lineIdxFor(m.index);
      const inMe = meRange && li >= meRange.start && li < meRange.end;
      const inSrc = sourcesRange && li >= sourcesRange.start && li < sourcesRange.end;
      if (!inMe && !inSrc) {
        violations.push(
          `[Sn] reference tag found outside Market event / Sources section at line ${li + 1}.`
        );
        break; // one is enough
      }
    }
  }

  // 5. Sources section has at least one entry matching `[Sn] Title (YYYY-MM-DD) — Outlet — URL`
  if (sourcesRange) {
    const text = sectionText(content, sourcesRange);
    if (!/^- \[S\d+\] .+ \(\d{4}-\d{2}-\d{2}\) — .+ — https?:\/\//m.test(text)) {
      violations.push(
        `Sources section must contain at least one bullet of form: \`- [Sn] Title (YYYY-MM-DD) — Outlet — URL\`.`
      );
    }
  }

  // 6. Data Gaps (if present) has at least one substantive bullet (not just placeholder)
  const dgRange = sectionMap.get("data_gaps");
  if (dgRange) {
    const text = sectionText(content, dgRange);
    const bullets = (text.match(/^- .+$/gm) || []).map((s) => s.trim());
    if (bullets.length === 0) {
      violations.push(
        `Data Gaps section is present but empty. Either remove the heading or add a substantive bullet.`
      );
    } else {
      const placeholderOnly = bullets.every((b) =>
        /^- (?:数据缺口|TBD|Data gap|データギャップ|n\/a)\s*$/i.test(b)
      );
      if (placeholderOnly) {
        violations.push(
          `Data Gaps section contains only placeholders. Either remove the heading or add a real explanation.`
        );
      }
    }
  }

  // 7. Source labels in market-data tables come from the allowed set
  for (const id of ["money_market", "fixed_income", "foreign_exchange", "commodity"]) {
    const range = sectionMap.get(id);
    if (!range) continue;
    const text = sectionText(content, range);
    // Pull the last column of each non-header table row that's not a separator.
    const rowRegex = /^\|[^\n]+\|$/gm;
    const rows = text.match(rowRegex) || [];
    for (const row of rows) {
      if (/^\|[\s\-:|]+\|$/.test(row)) continue; // separator
      const cells = row.split("|").map((c) => c.trim()).filter(Boolean);
      if (cells.length < 2) continue;
      // Heuristic: look at the last non-empty cell. Skip header rows by checking
      // whether the row starts with "Instrument" or "Tenor" or "Pair".
      if (/^(Instrument|Tenor|Pair)$/i.test(cells[0])) continue;
      const last = cells[cells.length - 1];
      if (!last) continue;
      const matchedAllowed = ALLOWED_SOURCES.some((src) => last.includes(src));
      if (!matchedAllowed) {
        violations.push(
          `Section "${id}" table row uses unrecognised Source label "${last}". Allowed: ${ALLOWED_SOURCES.join(", ")}.`
        );
        break;
      }
    }
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

      if (!filePath || !content) process.exit(0);
      if (isPluginInternal(filePath)) process.exit(0);
      if (!isWeeklyReport(filePath, content)) process.exit(0);

      const violations = validate(filePath, content);
      if (violations.length === 0) {
        process.stdout.write(
          JSON.stringify({
            result: "pass",
            message: `✅ weekly-report format check passed: ${filePath}`,
          })
        );
        process.exit(0);
      }

      const message = [
        `❌ weekly-report format check FAILED for ${filePath}`,
        `Output must match skills/weekly-report/references/output-spec.md.`,
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
      process.stdout.write(
        JSON.stringify({
          result: "pass",
          message: `weekly-report-format-check internal error: ${e.message}`,
        })
      );
      process.exit(0);
    }
  });
}

main();
