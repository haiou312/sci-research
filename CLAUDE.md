# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在此仓库工作时提供指引。

---

## 项目定位

这是一个 **Claude Code 插件**（`sci-research`，当前版本 1.3.2），通过多 Agent 编排，将"主题 + 比较实体 + 输出语言"转化为高质量研究/新闻产出。插件包含两条**完全独立**的流水线，互不共享 Agent：

| 特性 | `/sci-research`（深度研究） | `/news-scan`（实时新闻） |
|---|---|---|
| **目标** | 多实体对比的科普研究文章 | 指定时间窗内的新闻简报 |
| **时间焦点** | 历史 + 当前 | 近 7/30/90 天 |
| **来源** | 学术论文、官方报告、权威媒体 | 通讯社、财经媒体、行业媒体 |
| **Agent 链** | researcher → comparator → fact-checker → writer | news-scanner → news-imager → news-analyst |
| **产出** | ≤5000 字结构化文章（含 APA 引用） | 1000-3000 字简报（含事件时间线 + 图片） |

---

## 仓库结构

```
sci-research/
├── .claude-plugin/
│   ├── plugin.json              # 插件元数据（name, version, author）
│   └── marketplace.json         # 市场清单
├── agents/                      # 7 个专业 Agent（两条流水线共用目录）
│   ├── researcher.md            # [A] 每实体多源检索
│   ├── comparator.md            # [A] 跨实体维度对比分析
│   ├── fact-checker.md          # [A] 关键论断核验
│   ├── writer.md                # [A] 多语言文章合成
│   ├── news-scanner.md          # [B] 每实体实时新闻抓取（不取图）
│   ├── news-imager.md           # [B] 热点事件图片提取与校验
│   └── news-analyst.md          # [B] 去重、时间线、影响分析
├── commands/                    # 4 个 Slash 命令
│   ├── sci-research.md          # /sci-research 入口
│   ├── news-scan.md             # /news-scan 入口
│   ├── add-entity.md            # /add-entity 会话中加实体
│   └── set-lang.md              # /set-lang 切换输出语言
├── skills/                      # 两个独立 Skill 工作流
│   ├── sci-research/SKILL.md
│   └── news-scan/SKILL.md
├── contexts/
│   └── sci-research.md          # 研究模式行为上下文
├── hooks/
│   └── hooks.json               # 5 个质量钩子的配置
├── scripts/hooks/               # 钩子实现（Node.js）
│   ├── word-count-check.js      # [A] 限字（含中文字符数）
│   ├── entity-coverage-check.js # [A] 实体覆盖校验
│   ├── reference-validator.js   # [A] 引用完整性校验
│   ├── news-freshness-check.js  # [B] 新闻时效校验
│   └── research-summary.js      # [A&B] 会话元数据日志
├── rules/research/              # 三份质量规则
│   ├── source-credibility.md    # [A] 学术来源分级
│   ├── output-format.md         # [A] 文章格式规范
│   └── news-source.md           # [B] 新闻来源分级与去重
├── examples/                    # 完整产出样本
│   ├── nuclear-fusion-zh.md     # 核聚变能源（中/美/EU/日本）
│   └── mrna-vaccine-en.md       # mRNA 疫苗（US/EU/China）
├── AGENTS.md                    # Agent 链参考
├── README.md                    # 用户文档
├── CLAUDE.md                    # 本文件
└── LICENSE                      # MIT
```

---

## 核心命令

```bash
# 深度研究（多实体对比科普文章）
/sci-research <topic> --entities "Entity1,Entity2,..." --lang zh|en|ja

# 实时新闻简报（可带实体 / 时间窗）
/news-scan <topic> --entities "Entity1,Entity2,..." --period 7d|30d|90d --lang zh|en|ja

# 会话中追加实体（两条流水线均支持）
/add-entity "Entity3,Entity4"

# 切换输出语言
/set-lang en
```

`--lang` 默认 `zh`，`--period` 默认 `30d`。

---

## 两条流水线的 Agent 编排

### Pipeline A — `/sci-research`

```
User Input (topic, entities, lang)
  │
  ├─→ Researcher(A) ─┐
  ├─→ Researcher(B) ─┼─→ Comparator → Fact-Checker → Writer → Hooks → 最终文章
  └─→ Researcher(C) ─┘   (opus)        (sonnet)      (opus)
      (sonnet, 并行)
```

| Agent | 模型 | 工具 | 职责 |
|---|---|---|---|
| researcher | sonnet | Read, Grep, Glob, Bash, WebFetch, WebSearch | 每实体一个实例并行，多源检索 |
| comparator | opus | Read, Grep, Glob | 跨实体维度选择与根因分析 |
| fact-checker | sonnet | Read, Grep, Glob, WebFetch, WebSearch | 关键论断核验，标注置信度 |
| writer | opus | Read, Write, Edit, Grep | 按目标语言合成最终文章 |

**输出结构**：Abstract → Introduction → Core Concepts → Entity Analysis → Comparative Analysis → Trends & Outlook → Conclusion → Glossary → Source Credibility Table → References (APA 7th)

### Pipeline B — `/news-scan`

```
User Input (topic, entities, period, lang)
  │
  ├─→ News-Scanner(A) ─┐
  ├─→ News-Scanner(B) ─┼─→ 选出 Top 3-5 事件 → News-Imager → News-Analyst → Hooks → 简报
  └─→ News-Scanner(C) ─┘                        (sonnet)       (opus)
      (sonnet, 并行)
```

| Agent | 模型 | 工具 | 职责 |
|---|---|---|---|
| news-scanner | sonnet | WebSearch, WebFetch, Read, Grep, Glob | 每实体实时新闻抓取（不取图） |
| news-imager | sonnet | WebFetch, Read, Grep, Glob | 为 Top 事件提取合规图片与替代文本 |
| news-analyst | opus | Read, Write, Edit, Grep | 去重、时间线、影响矩阵、趋势信号 |

**输出结构**：Key Events Summary → Full Event Timeline → Entity-by-Entity Developments → Impact Analysis → Trend Signals & Risk Alerts → Sources

---

## 来源分级体系

### Pipeline A（学术 + 官方）
| 级别 | 类型 | 示例 |
|---|---|---|
| ★★★★★ | 同行评审期刊 | Nature, Science, The Lancet |
| ★★★★★ | 国际组织报告 | WHO, OECD, IPCC, World Bank |
| ★★★★☆ | 政府报告 | DOE, EU Commission, 国务院白皮书 |
| ★★★★☆ | 通讯社 | Reuters, AP, AFP, 新华社 |
| ★★★☆☆ | 优质新闻 | Scientific American, BBC Science |
| ★★☆☆☆ | 预印本 | arXiv, medRxiv（标注未经同行评审） |

### Pipeline B（新闻媒体）
| 级别 | 类型 | 示例 |
|---|---|---|
| ★★★★★ | 通讯社 | Reuters, AP, AFP, 新华社 |
| ★★★★☆ | 财经/商业媒体 | FT, Bloomberg, CNBC, 财新, BBC |
| ★★★☆☆ | 行业垂直媒体 | Finextra, TechCrunch, 36氪 |
| ★★☆☆☆ | 智库评论 | Brookings, PIIE, VoxEU |
| ★☆☆☆☆ | 社交/博客 | 除非是经验证专家否则回避 |

---

## 质量钩子（hooks/hooks.json）

| Hook | 流水线 | 触发 | 行为 |
|---|---|---|---|
| word-count-check | A | PostToolUse:Write | 超过 5000 字 / 7500 中文字符则阻断 |
| entity-coverage-check | A | PostToolUse:Write | 实体无专节或提及 <3 次则警告 |
| reference-validator | A | PostToolUse:Write | 内文 `[N]` 与参考条目不一致则警告 |
| news-freshness-check | B | PostToolUse:Write | 近 7 天内无来源则警告 |
| research-summary | A & B | Stop | 异步记录会话元数据（非阻断） |

---

## 开发约定

- **Agent 文件**：Markdown + YAML frontmatter（`name`, `description`, `tools`, `model`）
- **Skill 文件**：Markdown 明确分段（When to Activate / Workflow / Quality Rules）
- **Command 文件**：Markdown + description frontmatter
- **Hook 配置**：JSON，含 matcher 条件
- **文件命名**：全小写 + 连字符（kebab-case）
- **两条流水线完全独立**：修改 Pipeline A 的 Agent 不影响 Pipeline B，反之亦然
- **多语言**：默认支持 zh / en / ja，新增语言需同步更新 `writer.md`、`news-analyst.md` 与 `set-lang.md`

---

## 常见修改入口

| 目标 | 修改文件 |
|---|---|
| 调整 A 字数限制 | `scripts/hooks/word-count-check.js`（`WORD_LIMIT` / `CHAR_LIMIT_ZH`） |
| 调整 B 新鲜度窗口 | `scripts/hooks/news-freshness-check.js`（7 天常量） |
| 增加 A 对比维度 | `agents/comparator.md`（Section 1 Dimension Selection） |
| 新增输出语言 | `agents/writer.md` + `agents/news-analyst.md` + `commands/set-lang.md` |
| 调整 A 来源分级 | `rules/research/source-credibility.md` |
| 调整 B 新闻来源规则 | `rules/research/news-source.md` |
| 修改文章格式 | `rules/research/output-format.md` |

---

## 环境要求

- Claude Code CLI
- Node.js ≥ 18（运行 hook 脚本）
- 能访问外网（供 WebSearch / WebFetch）

---

## 参考文件

- **README.md** — 面向最终用户的使用文档（安装、示例、自定义）
- **AGENTS.md** — Agent 链的可视化流程图与工具表
- **examples/** — 两个完整产出样例，撰写新功能时可作为格式基准
