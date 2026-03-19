#!/usr/bin/env node

/**
 * Word Count Check Hook
 *
 * Validates that written research articles stay within the 5000-word limit.
 * For Chinese text, counts characters (excluding punctuation) and uses
 * a 1.5x character-to-word ratio.
 *
 * Exit codes:
 *   0 — pass (within limit or not a research article)
 *   2 — block (over limit, inject warning)
 */

const fs = require("fs");

const WORD_LIMIT = 5000;
const CHAR_LIMIT_ZH = 7500; // ~5000 words equivalent in Chinese

function countWords(text) {
  // Count Chinese characters
  const chineseChars = (text.match(/[\u4e00-\u9fff]/g) || []).length;

  // Count English words (sequences of latin characters)
  const englishWords = (
    text.match(/[a-zA-Z]+(?:[''-][a-zA-Z]+)*/g) || []
  ).length;

  // Count numbers as words
  const numbers = (text.match(/\d+(?:[.,]\d+)*/g) || []).length;

  // For mixed content: Chinese chars / 1.5 + English words + numbers
  if (chineseChars > 100) {
    return Math.round(chineseChars / 1.5) + englishWords + numbers;
  }

  return englishWords + numbers;
}

function main() {
  let input = "";

  process.stdin.setEncoding("utf8");
  process.stdin.on("data", (chunk) => {
    input += chunk;
  });

  process.stdin.on("end", () => {
    try {
      const data = JSON.parse(input);

      // Only check files that look like research articles
      const filePath = data?.tool_input?.file_path || "";
      if (!filePath.match(/research.*\.md$/i) && !filePath.match(/研究.*\.md$/i)) {
        process.exit(0);
      }

      const content = data?.tool_input?.content || "";
      if (!content) {
        process.exit(0);
      }

      // Strip markdown syntax for accurate count
      const plainText = content
        .replace(/^#+\s.*$/gm, "") // headers
        .replace(/\|.*\|/g, "") // tables
        .replace(/```[\s\S]*?```/g, "") // code blocks
        .replace(/\[(\d+)\]/g, "") // citation markers
        .replace(/https?:\/\/\S+/g, "") // URLs
        .replace(/[★☆✅🟡⚠️❌❓📋🏢🌐⏱️]/g, "") // emoji
        .replace(/---+/g, ""); // horizontal rules

      const wordCount = countWords(plainText);

      if (wordCount > WORD_LIMIT) {
        const msg = `⚠️ WORD COUNT EXCEEDED: ${wordCount} words (limit: ${WORD_LIMIT}). Reduce content — cut Section 5 (Trends) first, then trim examples in Section 3.`;
        process.stdout.write(JSON.stringify({ result: "warn", message: msg }));
        process.exit(2);
      }

      process.stdout.write(
        JSON.stringify({
          result: "pass",
          message: `✅ Word count: ${wordCount}/${WORD_LIMIT}`,
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
