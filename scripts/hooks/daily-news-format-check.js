#!/usr/bin/env node

/**
 * Daily News Format Check Hook
 *
 * Validates Pipeline C ($sci-research:daily-news-intelligence) Markdown output format.
 * Catches the failure modes observed across multiple runs where the Writer
 * deviates from `skills/daily-news-intelligence/references/output-spec.md`:
 *
 *   - Global `## 参考文献` / `## References` / `## Sources` H2 section
 *   - `> **来源**:` blockquote replacing **References** block
 *   - `*来源：Author (Year); ...*` italic in-text citation shortcut
 *   - Per-story **References** block missing
 *   - References without [N] continuous numbering
 *   - References lines without a URL
 *   - Mismatched count between ### story titles and **References** blocks
 *   - Prohibited markers: **摘要** / **Summary** / **要約** / **分析** / **Analysis**
 *     (1.9.x+ structure: body prose follows `### title` directly; no
 *     summary/analysis markers anywhere)
 *
 * Direct `--file` mode also reports advisory en/zh body-length statistics.
 * Length alone is never a format violation.
 *
 * Trigger: Codex PostToolUse:apply_patch when the file path is under daily-news/
 *          (or the legacy daily-news-reports/ path)
 *          OR when the content's H1 matches the daily-news H1 pattern
 *          (covers all three supported languages: zh / en / ja).
 *
 * Hook mode exits 0 and injects correction context after a violation.
 * Direct `--file` mode exits 0 on success and 2 on a format violation.
 */

const fs = require("fs");
const path = require("path");

// ---------- helpers ----------

function isDailyNewsReport(filePath, content) {
  // skip backups and non-md files
  if (filePath.endsWith(".bak") || !filePath.endsWith(".md")) return false;
  const byPath = /daily-news(?:-reports)?\//.test(filePath);
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

function buildFailureMessage(filePath, violations) {
  return [
    `daily-news format check FAILED for ${filePath}`,
    `Pipeline C Markdown must match skills/daily-news-intelligence/references/output-spec.md.`,
    ``,
    ...violations.map((violation, index) => `  ${index + 1}. ${violation}`),
    ``,
    `The edit has already been applied. Correct the file and run the check again before export or email.`,
  ].join("\n");
}

function validateFile(filePath) {
  let content;
  try {
    content = fs.readFileSync(filePath, "utf8");
  } catch (error) {
    return [`Could not read report: ${error.message}`];
  }
  if (!isDailyNewsReport(filePath, content)) {
    return [`Not a Pipeline C daily-news Markdown report: ${filePath}`];
  }
  return validate(filePath, content);
}

function runFileCheck(filePath) {
  if (!filePath) {
    process.stderr.write("Usage: daily-news-format-check.js --file <report.md>\n");
    return 2;
  }
  const violations = validateFile(filePath);
  if (violations.length === 0) {
    process.stdout.write(`FORMAT_OK: ${filePath}\n`);
    try {
      const content = fs.readFileSync(filePath, "utf8");
      const lengthInfo = summarizeBodyLengths(content, detectLang(content));
      if (lengthInfo) {
        process.stdout.write(
          `LENGTH_INFO: lang=${lengthInfo.lang} stories=${lengthInfo.stories} target~${lengthInfo.target} ${lengthInfo.unit}; min=${lengthInfo.min}, max=${lengthInfo.max}, average=${lengthInfo.average} (advisory)\n`
        );
      }
    } catch (error) {
      // Format validation already succeeded; advisory statistics must not fail delivery.
    }
    return 0;
  }
  process.stderr.write(`${buildFailureMessage(filePath, violations)}\n`);
  return 2;
}

function collectPatchedFilePaths(data) {
  const rawInput = data?.tool_input;
  const toolInput = rawInput && typeof rawInput === "object" ? rawInput : {};
  const candidates = [];
  for (const value of [
    toolInput.file_path,
    toolInput.path,
    toolInput.filename,
    toolInput.file,
    data?.tool_response?.file_path,
    data?.file_path,
  ]) {
    if (typeof value === "string" && value.trim()) candidates.push(value.trim());
  }
  if (Array.isArray(toolInput.changes)) {
    for (const change of toolInput.changes) {
      const value = change?.path || change?.file_path;
      if (typeof value === "string" && value.trim()) candidates.push(value.trim());
    }
  }

  const patchTexts = [
    typeof rawInput === "string" ? rawInput : "",
    toolInput.patch,
    toolInput.input,
    toolInput.patch_text,
  ].filter((value) => typeof value === "string");
  for (const patchText of patchTexts) {
    const filePattern = /^\*\*\* (?:Add|Update|Move to) File:\s+(.+)$/gm;
    for (const match of patchText.matchAll(filePattern)) {
      candidates.push(match[1].trim());
    }
  }

  const cwd = typeof data?.cwd === "string" && data.cwd ? data.cwd : process.cwd();
  return [
    ...new Set(
      candidates.map((candidate) =>
        path.isAbsolute(candidate) ? path.normalize(candidate) : path.resolve(cwd, candidate)
      )
    ),
  ];
}

// Section/marker variants across supported languages.
// The category set is country-derived (6 H2 for a non-China report, 7 for a China
// report which adds 海外涉华财经与外交 at position 5) — see
// skills/daily-news-intelligence/references/language-spec.md § Category Catalog &
// Selection. This hook is intentionally category-count agnostic: it validates
// ###↔**References** parity, [N] continuity, prohibited markers, and quote chars,
// never the number or names of H2 sections. Body length is advisory only.
//
// Prohibited markers (1.9.x+ structure): body prose follows `### title` directly.
// No summary/analysis marker is permitted anywhere in the output.
const PROHIBITED_MARKERS = /^\*\*(?:摘要|Summary|要約|分析|Analysis)\*\*$/gm;
const REFERENCES_MARKER_LINE = "**References**"; // language-independent per spec
const BODY_LENGTH_TARGETS = {
  en: { target: 300, unit: "English words" },
  zh: { target: 500, unit: "Han characters" },
};

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

// Story bodies are the prose between a `### title` and that story's
// `**References**` marker. Headings, references, URLs, and gap notes therefore
// remain outside the count by construction.
function extractStoryBodies(content) {
  const storyBlocks = content
    .split(/^---\s*$/m)
    .filter((block) => block.includes("###"));
  const stories = [];

  for (const block of storyBlocks) {
    const match = block.match(
      /^###\s+([^\n]+)\n+([\s\S]*?)\n+\*\*References\*\*\n+([\s\S]*)$/m
    );
    if (!match) continue;
    stories.push({ title: match[1].trim(), body: match[2], refs: match[3] });
  }

  return stories;
}

// ---------- lang detection & quote-mark validation (PR #1) ----------

function detectLang(content) {
  const m = content.match(
    /^# .+?(每日热点新闻|Daily News Intelligence|デイリーニュース)/m
  );
  if (!m) return null;
  if (m[1] === "每日热点新闻") return "zh";
  if (m[1] === "Daily News Intelligence") return "en";
  if (m[1] === "デイリーニュース") return "ja";
  return null;
}

function countEnglishWords(body) {
  const wordTokens =
    /\d+(?:[.,]\d+)*|[A-Za-z0-9]+(?:['\u2019-][A-Za-z0-9]+)*(?:\$\d+(?:[.,]\d+)*)?/g;
  return (body.match(wordTokens) || []).length;
}

function countHanCharacters(body) {
  return (body.match(/\p{Script=Han}/gu) || []).length;
}

function summarizeBodyLengths(content, lang) {
  const target = BODY_LENGTH_TARGETS[lang];
  if (!target) return null;

  const stories = extractStoryBodies(content);
  const expectedStories = countMatches(content, /^### /gm);
  if (stories.length === 0 || stories.length !== expectedStories) return null;

  const counts = stories.map(({ body }) =>
    lang === "en" ? countEnglishWords(body) : countHanCharacters(body)
  );
  const total = counts.reduce((sum, count) => sum + count, 0);

  return {
    lang,
    stories: counts.length,
    target: target.target,
    unit: target.unit,
    min: Math.min(...counts),
    max: Math.max(...counts),
    average: Math.round(total / counts.length),
  };
}

// Canonical quote chars per lang (mirrors language-spec.md § Canonical Quote Marks).
// Body prose must use only the lang's canonical open/close pair. APA ref lines,
// URLs, fenced code blocks, and inline code spans are exempt.
function validateQuoteMarks(content, lang) {
  const violations = [];

  const stripped = content
    .replace(/^```[\s\S]*?^```$/gm, "")
    .replace(/^\[\d+\].*$/gm, "")
    .replace(/https?:\/\/\S+/g, "")
    .replace(/`[^`]+`/g, "");

  const forbiddenByLang = {
    zh: /["「」]/g,
    en: /[“”「」]/g,
    ja: /["“”]/g,
  };
  const allowedDesc = {
    zh: "U+201C / U+201D",
    en: "U+0022",
    ja: "U+300C / U+300D",
  };

  const hits = stripped.match(forbiddenByLang[lang]);
  if (hits) {
    const unique = [...new Set(hits)];
    const codepoints = unique
      .map(
        (c) =>
          `U+${c.codePointAt(0).toString(16).toUpperCase().padStart(4, "0")}`
      )
      .join(", ");
    violations.push(
      `${hits.length} non-canonical quote char(s) for lang=${lang}: ${codepoints}. Allowed: ${allowedDesc[lang]}.`
    );
  }

  if (lang === "zh") {
    const opens = (stripped.match(/“/g) || []).length;
    const closes = (stripped.match(/”/g) || []).length;
    if (opens !== closes) {
      violations.push(
        `Quote pair imbalance (zh): ${opens} U+201C vs ${closes} U+201D.`
      );
    }
  }
  if (lang === "ja") {
    const opens = (stripped.match(/「/g) || []).length;
    const closes = (stripped.match(/」/g) || []).length;
    if (opens !== closes) {
      violations.push(
        `Quote pair imbalance (ja): ${opens} U+300C vs ${closes} U+300D.`
      );
    }
  }

  return violations;
}

// Reference-coverage heuristic backstop (PR #5).
//
// Per-story sanity check: if a story has direct quotes (between canonical
// quote marks for `lang`), it must have ≥1 URL in its References block.
// If a story carries many specific numeric claims (with units) but only
// 0-1 URLs, it's likely missing search-URL citations.
//
// This is HEURISTIC — won't catch every reference gap, won't false-positive
// at sensible thresholds. The Editor (Step 8.5) catches missing citations
// authoritatively; this hook is the belt-and-braces backstop.
function checkReferenceCoverage(content, lang) {
  const violations = [];
  for (const { title, body, refs } of extractStoryBodies(content)) {

    const quoteRegex =
      lang === "zh"
        ? /“[^”]+”/g
        : lang === "ja"
        ? /「[^」]+」/g
        : /"[^"]+"/g;
    const quoteCount = (body.match(quoteRegex) || []).length;
    const urlCount = (refs.match(/https?:\/\/\S+/g) || []).length;

    if (quoteCount > 0 && urlCount === 0) {
      violations.push(
        `Story "${title.trim()}" has ${quoteCount} direct quote(s) but 0 URLs in References. Every quote must trace to a cited URL.`
      );
    }

    const numericRegex =
      /\d+(?:[.,]\d+)?\s?(?:%|bps|百分点|个基点|million|billion|trillion|亿|万|百万|十亿|億)/g;
    const specificNumbers = (body.match(numericRegex) || []).length;
    if (specificNumbers >= 5 && urlCount <= 1) {
      violations.push(
        `Story "${title.trim()}" has ${specificNumbers} specific numeric claim(s) with units but only ${urlCount} URL(s) in References. Likely missing search-URL citations — Writer should cite every search URL that supplied a body fact.`
      );
    }
  }
  return violations;
}

// ---------- main validation ----------

function validate(filePath, content) {
  const violations = [];

  // 1. Count invariant: ### == **References** (one of each per story)
  const h3Count = countMatches(content, /^### /gm);
  const refsBlockCount = countMatches(
    content,
    /^\*\*References\*\*$/gm
  );
  if (h3Count === 0 || h3Count !== refsBlockCount) {
    violations.push(
      `Count mismatch: ### headings=${h3Count}, **References** blocks=${refsBlockCount}. Each story must have exactly one ### and one **References** block.`
    );
  }

  // 1b. Prohibited markers — 1.9.x+ structure forbids summary/analysis markers.
  //     Body prose follows ### title directly; no marker line between.
  const prohibitedHits = content.match(PROHIBITED_MARKERS);
  if (prohibitedHits) {
    const unique = [...new Set(prohibitedHits)];
    violations.push(
      `Prohibited marker(s) found (${prohibitedHits.length} instance[s]): ${unique.join(
        ", "
      )}. The 1.9.x+ structure requires body prose to follow \`### title\` directly — no \`**摘要**\` / \`**Summary**\` / \`**要約**\` / \`**分析**\` / \`**Analysis**\` markers anywhere.`
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

  // 7. Quote-mark canonical char enforcement (per language-spec.md § Canonical Quote Marks)
  // 8. Reference-coverage heuristic backstop (PR #5).
  const lang = detectLang(content);
  if (lang) {
    violations.push(...validateQuoteMarks(content, lang));
    violations.push(...checkReferenceCoverage(content, lang));
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
      const filePaths = collectPatchedFilePaths(data);
      if (filePaths.length === 0) {
        process.exit(0);
      }

      const failures = [];
      for (const filePath of filePaths) {
        if (isPluginInternal(filePath)) continue;
        let content;
        try {
          content = fs.readFileSync(filePath, "utf8");
        } catch (e) {
          continue;
        }
        if (!content || !isDailyNewsReport(filePath, content)) continue;
        const violations = validate(filePath, content);
        if (violations.length > 0) {
          failures.push(buildFailureMessage(filePath, violations));
        }
      }
      if (failures.length === 0) {
        process.exit(0);
      }

      const message = failures.join("\n\n");
      process.stderr.write(`${message}\n`);
      process.stdout.write(
        JSON.stringify({
          systemMessage: message,
          hookSpecificOutput: {
            hookEventName: "PostToolUse",
            additionalContext: message,
          },
        })
      );
      process.exit(0);
    } catch (e) {
      // don't block on parse/logic errors — the hook must never become a footgun
      process.exit(0);
    }
  });
}

if (require.main === module) {
  if (process.argv[2] === "--file") {
    process.exit(runFileCheck(process.argv[3]));
  }
  main();
}

module.exports = {
  summarizeBodyLengths,
  countEnglishWords,
  countHanCharacters,
  extractStoryBodies,
  collectPatchedFilePaths,
  runFileCheck,
  validate,
};
