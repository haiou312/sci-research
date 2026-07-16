#!/usr/bin/env node

/**
 * Validate Pipeline F opportunity-briefing Markdown.
 *
 * Hook mode reports correction context without blocking apply_patch itself.
 * Direct --file mode exits 2 on violations and is the blocking export gate.
 */

const fs = require("fs");
const path = require("path");

const REQUIRED_HEADINGS = [
  "## 一、本期结论",
  "## 二、商机优先清单",
  "## 三、英国经济与政策信号",
  "## 四、中国企业出海欧洲",
  "## 五、跨境并购动态",
  "## 六、英国及欧洲投资布局",
  "## 七、Companies House 雷达",
  "## 八、未来两周关注",
  "## 来源与免责声明",
];

const OPPORTUNITY_TABLE_HEADER =
  "| 优先级 | 企业/项目 | 最新事件 | 潜在需求 | 建议动作 | 时间窗口 |";
const CH_TABLE_HEADER =
  "| 英国实体 | Company No. | 中国母公司/关联方 | 本期变化 | 中资置信度 | 商业意义 |";
const WATCH_TABLE_HEADER =
  "| 日期/窗口 | 事项 | 涉及企业/行业 | 关注原因 | 建议跟进 |";
const NO_IMAGE_LINE =
  "**配图：** 未采用（未找到可合法嵌入且与事件直接相关的权威图片）";

function isPluginInternal(filePath) {
  return (
    /\/(agents|skills|hooks|scripts|references|examples)\//.test(filePath) ||
    /\/(README|CLAUDE|AGENTS|LICENSE)\.md$/i.test(filePath)
  );
}

function isOpportunityBriefing(filePath, content) {
  if (!filePath.endsWith(".md") || filePath.endsWith(".bak")) return false;
  return (
    /china-opportunity-briefings\//.test(filePath) ||
    /^# 中资企业商机拓展简报\s*$/m.test(content)
  );
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

function extractStoryBlocks(content) {
  const lines = content.split(/\r?\n/);
  const stories = [];
  let inStoryRegion = false;
  let current = null;

  for (const line of lines) {
    if (line === "## 三、英国经济与政策信号") {
      inStoryRegion = true;
      continue;
    }
    if (line === "## 七、Companies House 雷达") {
      if (current) stories.push(current);
      break;
    }
    if (!inStoryRegion) continue;

    if (line.startsWith("## ")) {
      if (current) {
        stories.push(current);
        current = null;
      }
      continue;
    }
    if (line.startsWith("### ")) {
      if (current) stories.push(current);
      current = { title: line.slice(4).trim(), body: "" };
      continue;
    }
    if (current) current.body += `${line}\n`;
  }

  return stories;
}

function countTableRows(content, header) {
  const index = content.indexOf(header);
  if (index < 0) return 0;
  const rest = content.slice(index).split("\n");
  let rows = 0;
  for (let i = 2; i < rest.length; i++) {
    const line = rest[i].trim();
    if (!line.startsWith("|")) break;
    rows += 1;
  }
  return rows;
}

function validate(filePath, content) {
  const violations = [];

  if (!/^# 中资企业商机拓展简报\s*$/m.test(content)) {
    violations.push("Missing exact H1: `# 中资企业商机拓展简报`.");
  }
  if (!/^> 报告期：\d{4}-\d{2}-\d{2} 至 \d{4}-\d{2}-\d{2}\s*$/m.test(content)) {
    violations.push("Missing or invalid `> 报告期：YYYY-MM-DD 至 YYYY-MM-DD` metadata.");
  }
  if (!/^> 编制日期：\d{4}-\d{2}-\d{2}\s*$/m.test(content)) {
    violations.push("Missing or invalid `> 编制日期：YYYY-MM-DD` metadata.");
  }
  if (!/^> 使用范围：内部使用\s*$/m.test(content)) {
    violations.push("Missing `> 使用范围：内部使用` metadata.");
  }

  let lastHeadingIndex = -1;
  for (const heading of REQUIRED_HEADINGS) {
    const index = content.indexOf(heading);
    if (index < 0) {
      violations.push(`Missing required section: \`${heading}\`.`);
    } else if (index <= lastHeadingIndex) {
      violations.push(`Section is out of order: \`${heading}\`.`);
    }
    if (index >= 0) lastHeadingIndex = index;
  }

  for (const [header, name] of [
    [OPPORTUNITY_TABLE_HEADER, "opportunity priority"],
    [CH_TABLE_HEADER, "Companies House radar"],
    [WATCH_TABLE_HEADER, "future watch"],
  ]) {
    if (!content.includes(header)) {
      violations.push(`Missing exact ${name} table header: \`${header}\`.`);
    }
  }

  const opportunityRows = countTableRows(content, OPPORTUNITY_TABLE_HEADER);
  if (opportunityRows < 1) {
    violations.push("Opportunity priority table must contain at least one data row.");
  }

  const stories = extractStoryBlocks(content);
  if (stories.length < 1) {
    violations.push(
      "No story blocks found between section three and Companies House. Use `### headline` blocks."
    );
  }

  for (const story of stories) {
    for (const label of [
      "**摘要：**",
      "**关键影响：**",
      "**商机切入点：**",
      "**后续关注：**",
      "**来源：**",
    ]) {
      if (!story.body.includes(label)) {
        violations.push(`Story "${story.title}" is missing ${label}.`);
      }
    }
    const urls = story.body.match(/https?:\/\/[^\s)]+/g) || [];
    if (urls.length === 0) {
      violations.push(`Story "${story.title}" has no source URL.`);
    }
    const imageMatch = story.body.match(/!\[[^\]]*\]\([^)]+\)/);
    if (imageMatch && !/\*图片来源：[^*\n]+\*/.test(story.body)) {
      violations.push(
        `Story "${story.title}" embeds an image but lacks an italic image-source line.`
      );
    }
    if (!imageMatch && !story.body.includes(NO_IMAGE_LINE)) {
      violations.push(
        `Story "${story.title}" must include an eligible image or the exact no-image line.`
      );
    }
  }

  const chSection = content.match(
    /^## 七、Companies House 雷达\s*$([\s\S]*?)^## 八、未来两周关注\s*$/m
  );
  if (chSection) {
    if (!/^### Companies House 覆盖说明\s*$/m.test(chSection[1])) {
      violations.push("Companies House section lacks `### Companies House 覆盖说明`.");
    }
    if (/\|\s*未验证\s*\|/.test(chSection[1])) {
      violations.push(
        "Companies House final table must not include unverified Chinese-nexus entities."
      );
    }
  }

  if (!/免责声明：本简报基于公开资料编制/.test(content)) {
    violations.push("Missing the required Pipeline F disclaimer.");
  }
  if (/turn\d+(?:search|view|fetch)\d+/.test(content)) {
    violations.push("Internal web tool citation tokens must not appear in the report.");
  }
  if (/现有客户关系|已确认融资需求|已委任我行/.test(content)) {
    violations.push(
      "Potentially unsupported relationship/demand language found. Reframe as a hypothesis unless sourced."
    );
  }

  return violations;
}

function buildFailureMessage(filePath, violations) {
  return [
    `opportunity briefing format check FAILED for ${filePath}`,
    "Pipeline F Markdown must match skills/china-outbound-opportunity-briefing/references/output-spec.md.",
    "",
    ...violations.map((violation, index) => `  ${index + 1}. ${violation}`),
    "",
    "Correct the file before DOCX export or email.",
  ].join("\n");
}

function runFileCheck(filePath) {
  if (!filePath) {
    process.stderr.write(
      "Usage: opportunity-briefing-format-check.js --file <report.md>\n"
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
  if (!isOpportunityBriefing(filePath, content)) {
    process.stderr.write(`Not a Pipeline F opportunity briefing: ${filePath}\n`);
    return 2;
  }
  const violations = validate(filePath, content);
  if (violations.length === 0) {
    process.stdout.write(`FORMAT_OK: ${filePath}\n`);
    return 0;
  }
  process.stderr.write(`${buildFailureMessage(filePath, violations)}\n`);
  return 2;
}

function main() {
  let input = "";
  process.stdin.setEncoding("utf8");
  process.stdin.on("data", (chunk) => (input += chunk));
  process.stdin.on("end", () => {
    try {
      const data = JSON.parse(input);
      const failures = [];
      for (const filePath of collectPatchedFilePaths(data)) {
        if (isPluginInternal(filePath)) continue;
        let content;
        try {
          content = fs.readFileSync(filePath, "utf8");
        } catch (error) {
          continue;
        }
        if (!content || !isOpportunityBriefing(filePath, content)) continue;
        const violations = validate(filePath, content);
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
  collectPatchedFilePaths,
  extractStoryBlocks,
  runFileCheck,
  validate,
};
