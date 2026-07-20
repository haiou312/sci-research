#!/usr/bin/env node

/**
 * Validate Pipeline G monthly-news Markdown.
 *
 * Reuses Pipeline C's story/reference/body-length validation, then enforces the
 * monthly H1, source-coverage note, and country-derived category sequence.
 */

const fs = require("fs");
const daily = require("./daily-news-format-check.js");

const MONTHS =
  "(?:January|February|March|April|May|June|July|August|September|October|November|December)";

const CATEGORIES = {
  en: {
    ordinary: [
      "## 1. Economy & Markets",
      "## 2. Politics & Diplomacy",
      "## 3. Technology & Industry",
      "## 4. Society & Livelihood",
      "## 5. Corporate IPO & M&A",
      "## 6. Other Notable Events",
    ],
    china: [
      "## 1. Economy & Markets",
      "## 2. Politics & Diplomacy",
      "## 3. Technology & Industry",
      "## 4. Society & Livelihood",
      "## 5. China-Nexus Finance & Investment",
      "## 6. Corporate IPO & M&A",
      "## 7. Other Notable Events",
    ],
  },
  zh: {
    ordinary: [
      "## 一、经济与市场",
      "## 二、政治与外交",
      "## 三、科技与产业",
      "## 四、社会与民生",
      "## 五、企业IPO与并购",
      "## 六、其他重要事件",
    ],
    china: [
      "## 一、经济与市场",
      "## 二、政治与外交",
      "## 三、科技与产业",
      "## 四、社会与民生",
      "## 五、海外涉华财经",
      "## 六、企业IPO与并购",
      "## 七、其他重要事件",
    ],
  },
  ja: {
    ordinary: [
      "## 1. 経済と市場",
      "## 2. 政治と外交",
      "## 3. テクノロジーと産業",
      "## 4. 社会と生活",
      "## 5. 企業のIPO・M&A",
      "## 6. その他の重要事項",
    ],
    china: [
      "## 1. 経済と市場",
      "## 2. 政治と外交",
      "## 3. テクノロジーと産業",
      "## 4. 社会と生活",
      "## 5. 海外の対中経済・投資",
      "## 6. 企業のIPO・M&A",
      "## 7. その他の重要事項",
    ],
  },
};

function isMonthlyNewsReport(filePath, content) {
  if (filePath.endsWith(".bak") || !filePath.endsWith(".md")) return false;
  return (
    /monthly-news\//.test(filePath) ||
    /^# [^\n]*(?:月度热点新闻|Monthly News Intelligence|月間ニュース)/m.test(
      content
    )
  );
}

function isPluginInternal(filePath) {
  return (
    /\/(agents|commands|skills|\.claude-plugin|hooks|scripts|rules|contexts|examples)\//.test(
      filePath
    ) || /\/(README|CLAUDE|AGENTS|LICENSE)\.md$/i.test(filePath)
  );
}

function detectLang(content) {
  if (/^# [^\n]*月度热点新闻/m.test(content)) return "zh";
  if (/^# [^\n]* Monthly News Intelligence/m.test(content)) return "en";
  if (/^# [^\n]*月間ニュース/m.test(content)) return "ja";
  return null;
}

function expectedH1Pattern(lang) {
  if (lang === "zh") {
    return /^# .+月度热点新闻 — \d{4}年(?:1[0-2]|[1-9])月$/;
  }
  if (lang === "en") {
    return new RegExp(
      `^# .+ Monthly News Intelligence — ${MONTHS} \\d{4}$`
    );
  }
  return /^# .+月間ニュース — \d{4}年(?:1[0-2]|[1-9])月$/;
}

function coveragePattern(lang) {
  if (lang === "zh") return /^\*资料范围：.+\*$/gm;
  if (lang === "en") return /^\*Source coverage: .+\*$/gm;
  return /^\*資料範囲：.+\*$/gm;
}

function isChinaReport(content, lang) {
  if (lang === "en") {
    return /^# China Monthly News Intelligence —/m.test(content);
  }
  return /^# 中国(?:月度热点新闻|月間ニュース) —/m.test(content);
}

function monthlyViolations(filePath, content) {
  const violations = [];
  const lang = detectLang(content);
  if (!lang) {
    return [
      "Could not detect monthly report language from H1. Use 月度热点新闻, Monthly News Intelligence, or 月間ニュース.",
    ];
  }

  const firstLine =
    content
      .split("\n")
      .map((line) => line.trim())
      .find(Boolean) || "";
  if (!expectedH1Pattern(lang).test(firstLine)) {
    violations.push(`Invalid monthly H1 for lang=${lang}: "${firstLine}"`);
  }

  const coverageMatches = content.match(coveragePattern(lang)) || [];
  if (coverageMatches.length !== 1) {
    violations.push(
      `Expected exactly one localized source-coverage note after H1; found ${coverageMatches.length}.`
    );
  } else {
    const firstH2 = content.search(/^## /m);
    const coverageAt = content.indexOf(coverageMatches[0]);
    if (firstH2 >= 0 && coverageAt > firstH2) {
      violations.push("Source-coverage note must appear before the first H2.");
    }
  }

  const actualH2 = content.match(/^## .+$/gm) || [];
  const scope = isChinaReport(content, lang) ? "china" : "ordinary";
  const expectedH2 = CATEGORIES[lang][scope];
  if (JSON.stringify(actualH2) !== JSON.stringify(expectedH2)) {
    violations.push(
      `Monthly H2 sequence mismatch for lang=${lang}, scope=${scope}. ` +
        `Expected ${JSON.stringify(expectedH2)}, got ${JSON.stringify(actualH2)}.`
    );
  }

  const dailyGapNotes =
    content.match(/^\*(?:注：.*当日|Note:.*today|注：.*本日).*\*$/gm) || [];
  if (dailyGapNotes.length > 0) {
    violations.push(
      `${dailyGapNotes.length} daily gap note(s) found. Monthly output must use the localized monthly gap-note pattern.`
    );
  }

  violations.push(...daily.validate(filePath, content));
  return violations;
}

function buildFailureMessage(filePath, violations) {
  return [
    `monthly-news format check FAILED for ${filePath}`,
    "Pipeline G Markdown must match skills/monthly-news-intelligence/references/output-overrides.md.",
    "",
    ...violations.map((item, index) => `  ${index + 1}. ${item}`),
    "",
    "The edit has already been applied. Correct the file and run the check again before export or email.",
  ].join("\n");
}

function runFileCheck(filePath) {
  if (!filePath) {
    process.stderr.write(
      "Usage: monthly-news-format-check.js --file <report.md>\n"
    );
    return 2;
  }
  let content;
  try {
    content = fs.readFileSync(filePath, "utf8");
  } catch (error) {
    process.stderr.write(`Could not read report: ${error.message}\n`);
    return 2;
  }
  if (!isMonthlyNewsReport(filePath, content)) {
    process.stderr.write(`Not a Pipeline G monthly-news report: ${filePath}\n`);
    return 2;
  }
  const violations = monthlyViolations(filePath, content);
  if (violations.length > 0) {
    process.stderr.write(`${buildFailureMessage(filePath, violations)}\n`);
    return 2;
  }
  process.stdout.write(`FORMAT_OK: ${filePath}\n`);
  const lang = detectLang(content);
  const info = daily.summarizeBodyLengths(content, lang);
  if (info) {
    process.stdout.write(
      `LENGTH_INFO: lang=${info.lang} stories=${info.stories} target~${info.target} ${info.unit}; required>=${info.minimum}, min=${info.min}, max=${info.max}, average=${info.average}\n`
    );
  }
  return 0;
}

function main() {
  let input = "";
  process.stdin.setEncoding("utf8");
  process.stdin.on("data", (chunk) => (input += chunk));
  process.stdin.on("end", () => {
    try {
      const data = JSON.parse(input);
      const filePaths = daily.collectPatchedFilePaths(data);
      const failures = [];
      for (const filePath of filePaths) {
        if (isPluginInternal(filePath)) continue;
        let content;
        try {
          content = fs.readFileSync(filePath, "utf8");
        } catch (error) {
          continue;
        }
        if (!content || !isMonthlyNewsReport(filePath, content)) continue;
        const violations = monthlyViolations(filePath, content);
        if (violations.length > 0) {
          failures.push(buildFailureMessage(filePath, violations));
        }
      }
      if (failures.length === 0) process.exit(0);
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
    } catch (error) {
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
  detectLang,
  isMonthlyNewsReport,
  monthlyViolations,
  runFileCheck,
};
