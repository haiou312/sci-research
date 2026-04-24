# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在此仓库工作时提供指引。

---

## 项目定位

这是一个 **Claude Code 插件**（`sci-research`，当前版本 1.7.3），通过多 Agent 编排，将"主题 + 比较实体 + 输出语言"转化为高质量研究/新闻产出。插件包含五条**完全独立**的流水线，互不共享 Agent：

| 特性 | `/sci-research` | `/news-scan` | `/daily-news-intelligence` | `/daily-briefing` | `/reputation-track` |
|---|---|---|---|---|---|
| **目标** | 多实体对比的科普研究文章 | 指定时间窗内的新闻简报 | 单国每日新闻简报 | 多国品牌新闻简报（SPD Bank） | 公司声誉风险监控 |
| **时间焦点** | 历史 + 当前 | 近 7/30/90 天 | 单日（指定日期） | 单日（读取已有报告） | 单日（指定日期） |
| **来源** | 学术论文、官方报告、权威媒体 | 通讯社、财经媒体、行业媒体 | T1-T4 分级媒体（逐 URL 日期核验） | Pipeline C 产出的各国 Markdown | News (T1-T4) + Reddit + X |
| **Agent 链** | researcher → comparator → fact-checker → writer | news-scanner → news-imager → news-analyst | news-scanner → news-verifier → daily-news-writer | briefing-curator → docx 脚本 → 邮件脚本 | reputation-resolver → reputation-scanner×3 → reputation-classifier → reputation-writer |
| **产出** | ≤5000 字结构化文章（含 APA 引用） | 1000-3000 字简报（含事件时间线 + 图片） | 五类固定栏目简报（Markdown + docx，可邮件投递） | 13-15 条品牌 Word 文档（含邮件投递） | 仅当命中负面时发送 HTML 邮件（inline body，无附件） |

---

## 仓库结构

```
sci-research/
├── .claude-plugin/
│   ├── plugin.json              # 插件元数据（name, version, author）
│   └── marketplace.json         # 市场清单
├── agents/                      # 13 个专业 Agent（五条流水线共用目录）
│   ├── researcher.md            # [A] 每实体多源检索
│   ├── comparator.md            # [A] 跨实体维度对比分析
│   ├── fact-checker.md          # [A] 关键论断核验
│   ├── writer.md                # [A] 多语言文章合成
│   ├── news-scanner.md          # [B/C] 每实体实时新闻抓取（不取图）
│   ├── news-imager.md           # [B] 热点事件图片提取与校验
│   ├── news-analyst.md          # [B] 去重、时间线、影响分析
│   ├── news-verifier.md         # [C] 编辑台二次筛选（原创性/权威性/影响力/去重）
│   ├── daily-news-writer.md     # [C] 多语言每日简报合成（仅消费 Verifier KEEP 集）
│   ├── briefing-curator.md      # [D] 多国新闻筛选改写（读取已有 MD，不搜索）
│   ├── reputation-resolver.md   # [E] ticker/name → 公司 + 高管列表消歧
│   ├── reputation-scanner.md    # [E] 每源并行扫 News/Reddit/X（不判负面）
│   ├── reputation-classifier.md # [E] 逐条打分：category + severity + verbatim quote
│   └── reputation-writer.md     # [E] 渲染内联 HTML 邮件正文（模板固定）
├── commands/                    # 7 个 Slash 命令
│   ├── sci-research.md          # /sci-research 入口
│   ├── news-scan.md             # /news-scan 入口
│   ├── daily-news-intelligence.md # /daily-news-intelligence 入口
│   ├── daily-briefing.md        # /daily-briefing 入口
│   ├── reputation-track.md      # /reputation-track 入口
│   ├── add-entity.md            # /add-entity 会话中加实体
│   └── set-lang.md              # /set-lang 切换输出语言
├── skills/                      # 五个独立 Skill 工作流
│   ├── sci-research/SKILL.md
│   ├── news-scan/SKILL.md
│   ├── daily-news-intelligence/
│   │   ├── SKILL.md
│   │   └── references/          # Pipeline C 的规范文档
│   │       ├── email-spec.md
│   │       ├── language-spec.md
│   │       ├── output-spec.md
│   │       ├── rubric.md
│   │       ├── schemas.md
│   │       └── verification.md
│   ├── daily-briefing/          # Pipeline D（完全独立）
│   │   ├── SKILL.md
│   │   ├── template/
│   │   │   └── briefing-template.docx  # SPD Bank 品牌模板
│   │   ├── references/
│   │   │   └── email-spec.md    # 独立邮件模板规范
│   │   └── scripts/
│   │       ├── generate-branded-docx.py  # docx 生成脚本
│   │       └── send-briefing-email.py    # 独立邮件发送脚本
│   └── reputation-track/        # Pipeline E（完全独立）
│       ├── SKILL.md
│       └── references/          # Pipeline E 的规范文档
│           ├── entity-resolution.md  # 代码/名字消歧 + 高管抓取
│           ├── source-matrix.md      # News + Reddit + X 的搜索模板
│           ├── negativity-rubric.md  # 分类 + 严重度 + 可信度加权
│           ├── html-template.md      # 内联 CSS HTML 邮件正文骨架
│           ├── email-spec.md         # 调用 send-report-email.py 的契约
│           └── schemas.md            # Resolver/Scanner/Classifier 输出格式
├── contexts/
│   └── sci-research.md          # 研究模式行为上下文
├── hooks/
│   └── hooks.json               # 5 个质量钩子的配置
├── scripts/
│   ├── hooks/                   # 钩子实现（Node.js）
│   │   ├── word-count-check.js      # [A] 限字（含中文字符数）
│   │   ├── entity-coverage-check.js # [A] 实体覆盖校验
│   │   ├── reference-validator.js   # [A] 引用完整性校验
│   │   ├── news-freshness-check.js  # [B] 新闻时效校验
│   │   └── research-summary.js      # [A&B] 会话元数据日志
│   └── send-report-email.py     # [C & E] Gmail SMTP 邮件发送脚本（支持 --body-html-file）
├── rules/research/              # 三份质量规则
│   ├── source-credibility.md    # [A] 学术来源分级
│   ├── output-format.md         # [A] 文章格式规范
│   └── news-source.md           # [B] 新闻来源分级与去重
├── examples/                    # 完整产出样本
│   ├── nuclear-fusion-zh.md     # 核聚变能源（中/美/EU/日本）
│   └── mrna-vaccine-en.md       # mRNA 疫苗（US/EU/China）
├── .env.example                 # Gmail SMTP 环境变量模板
├── .gitignore
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

# 单国每日新闻情报（支持邮件投递）
/daily-news-intelligence --country "Japan" [--date 2026-04-14] [--lang zh|en|ja] [--out-dir <path>] [--min-per-category <N>] [--email <a@x.com,b@y.com>] [--email-attach both|docx|md|none] [--email-dry-run]

# 多国品牌新闻简报（读取已有报告，生成 SPD Bank 品牌 Word）
/daily-briefing [--date 2026-04-16] [--countries "中国,英国,美国,欧洲,日本,韩国"] [--total 14] [--email <a@x.com>] [--email-dry-run] [--no-wait]

# 公司声誉风险监控（仅在命中负面时发 HTML 邮件）
/reputation-track --company "<名字或股票代码>" [--date 2026-04-21] [--lang zh|en] [--sources news,reddit,x] [--severity-min low|medium|high] [--email <a@x.com>] [--email-dry-run]

# 会话中追加实体（Pipeline A & B）
/add-entity "Entity3,Entity4"

# 切换输出语言
/set-lang en
```

`--lang` 默认 `zh`，`--period` 默认 `30d`，`--min-per-category` 默认 `2`。

---

## 五条流水线的 Agent 编排

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

### Pipeline C — `/daily-news-intelligence`

```
User Input (country, date, lang)
  │
  └─→ News-Scanner ─→ News-Verifier ─→ Daily-News-Writer ─→ pandoc → 邮件（可选）
      (sonnet)         (sonnet)          (opus)
      英文检索 +        原创性/权威性/     消费 KEEP 集，
      逐URL日期核验     影响力/去重筛选    翻译为目标语言
```

| Agent | 模型 | 工具 | 职责 |
|---|---|---|---|
| news-scanner | sonnet | WebSearch, WebFetch, Read, Grep, Glob | 英文检索 20-30 候选 URL，逐 URL WebFetch 日期核验，T1-T4 分级 |
| news-verifier | sonnet | Read, Grep, Glob, WebFetch | 编辑台二次筛选：原创性、权威性、影响力、去重，输出 KEEP/DROP 集 |
| daily-news-writer | opus | Read, Write, Edit, Grep | 消费 Verifier KEEP 集，翻译为目标语言，输出 Markdown + APA 引用 |

**固定五栏**：经济与市场 → 政治与外交 → 科技与产业 → 社会与民生 → 其他要闻

**输出**：Markdown 文件 + pandoc 导出 docx，可选 Gmail SMTP 邮件投递（支持 `--email-dry-run` 预览）

### Pipeline D — `/daily-briefing`

```
daily-news-reports/YYYY-MM-DD/*.md  (各国已有报告)
  │
  └─→ Briefing-Curator ─→ generate-branded-docx.py ─→ send-briefing-email.py
      (opus)                (python-docx)               (Gmail SMTP)
      读取各国 MD，          基于 SPD Bank 模板           邮件投递品牌 docx
      筛选+改写 13-15 条     生成品牌 Word 文档
```

| 组件 | 模型 | 工具 | 职责 |
|---|---|---|---|
| briefing-curator | opus | Read, Grep, Glob | 读取各国 MD，筛选最重要的 13-15 条新闻，改写为统一风格 |
| generate-branded-docx.py | — | python-docx | 基于 SPD Bank 模板生成品牌 Word 文档 |
| send-briefing-email.py | — | Gmail SMTP | 邮件投递品牌 docx |

**输出**：SPD Bank 品牌 Word 文档（header 有银行 logo、footer 有装饰图案），可选邮件投递

### Pipeline E — `/reputation-track`

```
User Input (company name|ticker, date, lang)
  │
  └─→ Reputation-Resolver ──→ Reputation-Scanner × 3 (并行)  ──→ Reputation-Classifier ──→ Reputation-Writer ──→ 邮件（仅在命中负面时）
      (opus)                   (sonnet)                          (sonnet)                   (opus)
      ticker→公司名+高管        news / reddit / x 各一路          逐条 category+severity      HTML 模板渲染，
                               date-verified raw candidates      + verbatim quote 去重      inline CSS，邮件 body
```

| Agent / 组件 | 模型 | 工具 | 职责 |
|---|---|---|---|
| reputation-resolver | opus | WebFetch, WebSearch, Read, Grep, Glob | ticker/name 消歧（Yahoo Finance/SEC/Wikipedia），抓 5-8 名高管；resolution_confidence=low 时中止 |
| reputation-scanner (×3) | sonnet | WebSearch, WebFetch, Read, Grep, Glob | 每源一个实例并行。News 走 WebSearch+T1-T4；Reddit 走 `/search.json`；X 走 `site:` search。只抓不判 |
| reputation-classifier | sonnet | Read, Grep, Glob, WebFetch | 逐条打 category + severity + 可信度；WebFetch 源文件提 verbatim quote；跨源去重；低于 severity_min 丢弃 |
| reputation-writer | opus | Read, Write, Edit, Grep | 按 `html-template.md` 渲染内联 CSS HTML；verbatim quote 原样；生成 TL;DR |
| send-report-email.py `--body-html-file` | — | Gmail SMTP | 扩展后支持 HTML body，multipart/alternative 自动生成 text/plain 降级 |

**关键约束**：
- `total_items_kept == 0` → 静默退出，不写 HTML 文件，不发邮件
- **覆盖范围**：News (T1-T4) + Reddit（公开 sub）+ X（Google 索引）。**Facebook 和 Threads 不在 v1 覆盖**（公开搜索过稀，靠不住）
- 每条输出必须含源文件的 verbatim 引用 — 不改写、不编造
- 低可信度（Reddit/X）声称 high/critical 时需 T1-T3 佐证，否则降级或丢弃

**输出**：
- `{out_dir}{company_display}-reputation-{date}.html`（内联 CSS，最大 600px，无外部资源）
- 邮件主题格式：`[声誉预警] {公司} — {日期} · {N} 项负面（{最高严重度}）`

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

### Pipeline C（T1-T4 分级）
| 级别 | 类型 | 示例 |
|---|---|---|
| T1 | 通讯社 / 官方发布 | Reuters, AP, AFP, 政府官网 |
| T2 | 主流财经 / 综合媒体 | FT, Bloomberg, BBC, NHK |
| T3 | 行业垂直 / 质量报纸 | TechCrunch, Nikkei, 财新 |
| T4 | 区域 / 利基媒体 | 地方报纸、专业博客（需原创报道） |

详细规则见 `skills/daily-news-intelligence/references/rubric.md`。

---

## 质量钩子（hooks/hooks.json）

| Hook | 流水线 | 触发 | 行为 |
|---|---|---|---|
| word-count-check | A | PostToolUse:Write | 超过 5000 字 / 7500 中文字符则阻断 |
| entity-coverage-check | A | PostToolUse:Write | 实体无专节或提及 <3 次则警告 |
| reference-validator | A | PostToolUse:Write | 内文 `[N]` 与参考条目不一致则警告 |
| news-freshness-check | B | PostToolUse:Write | 近 7 天内无来源则警告 |
| **daily-news-format-check** | **C** | **PostToolUse:Write** | **Writer 输出格式违规即阻断（blockquote 来源 / 斜体 in-text / 全局 `## 参考文献` / 缺 `[N]` / `[N]` 不连续 / 缺 URL / `### == 摘要 == **References**` 数目不符）** |
| **email-send-guard** | **C & D & E** | **PreToolUse:Bash** | **Bash 命令里检测到 inline `smtplib` / `email.message` / `MIMEMultipart` / `sendmail` / `mail -s` 且未调用 `send-*-email.py` → 阻断。防止 orchestrator 绕过 sanctioned 脚本导致附件 noname** |
| research-summary | A & B | Stop | 异步记录会话元数据（非阻断） |

---

## 开发约定

- **Agent 文件**：Markdown + YAML frontmatter（`name`, `description`, `tools`, `model`）
- **Skill 文件**：Markdown 明确分段（When to Activate / Workflow / Quality Rules）
- **Command 文件**：Markdown + description frontmatter
- **Hook 配置**：JSON，含 matcher 条件
- **文件命名**：全小写 + 连字符（kebab-case）
- **五条流水线完全独立**：修改一条流水线的 Agent 不影响其他流水线
- **多语言**：默认支持 zh / en / ja，新增语言需同步更新 `writer.md`、`news-analyst.md`、`daily-news-writer.md` 与 `set-lang.md`
- **Pipeline C 规范文档**：集中在 `skills/daily-news-intelligence/references/` 目录下，修改前需通读相关 spec

---

## 常见修改入口

| 目标 | 修改文件 |
|---|---|
| 调整 A 字数限制 | `scripts/hooks/word-count-check.js`（`WORD_LIMIT` / `CHAR_LIMIT_ZH`） |
| 调整 B 新鲜度窗口 | `scripts/hooks/news-freshness-check.js`（7 天常量） |
| 增加 A 对比维度 | `agents/comparator.md`（Section 1 Dimension Selection） |
| 新增输出语言 | `agents/writer.md` + `agents/news-analyst.md` + `agents/daily-news-writer.md` + `commands/set-lang.md` + `skills/daily-news-intelligence/references/language-spec.md` |
| 调整 A 来源分级 | `rules/research/source-credibility.md` |
| 调整 B 新闻来源规则 | `rules/research/news-source.md` |
| 调整 C 来源分级与日期核验 | `skills/daily-news-intelligence/references/rubric.md` |
| 调整 C Verifier 筛选逻辑 | `agents/news-verifier.md` |
| 调整 C 输出格式 / Markdown 语法 | `skills/daily-news-intelligence/references/output-spec.md` |
| 调整 C 邮件投递 | `skills/daily-news-intelligence/references/email-spec.md` + `scripts/send-report-email.py` |
| 调整 C 栏目分类 / 本地化 | `skills/daily-news-intelligence/references/language-spec.md` |
| 调整 C Reference 格式校验规则 | `scripts/hooks/daily-news-format-check.js` + `skills/daily-news-intelligence/references/output-spec.md` § Self-Check Checksum |
| 调整邮件发送守卫（禁止 inline SMTP） | `scripts/hooks/email-send-guard.js` + 三份 SKILL.md 的 email Step 里的 "Hard rule" 段 |
| 修改 A 文章格式 | `rules/research/output-format.md` |
| 调整 D 品牌模板 | `skills/daily-briefing/template/briefing-template.docx` |
| 调整 D 新闻筛选逻辑 | `agents/briefing-curator.md` |
| 调整 D docx 生成 | `skills/daily-briefing/scripts/generate-branded-docx.py` |
| 调整 D 邮件投递 | `skills/daily-briefing/references/email-spec.md` + `skills/daily-briefing/scripts/send-briefing-email.py` |
| 调整 E 负面分类/严重度 | `skills/reputation-track/references/negativity-rubric.md` |
| 调整 E 数据源（News/Reddit/X）搜索模板 | `skills/reputation-track/references/source-matrix.md` |
| 调整 E HTML 邮件模板 | `skills/reputation-track/references/html-template.md` |
| 调整 E 实体消歧/高管抓取 | `skills/reputation-track/references/entity-resolution.md` + `agents/reputation-resolver.md` |
| 调整 E 邮件投递 | `skills/reputation-track/references/email-spec.md` + `scripts/send-report-email.py`（`--body-html-file` 支持） |

---

## 环境要求

- Claude Code CLI
- Node.js ≥ 18（运行 hook 脚本）
- Python 3（Pipeline C 邮件发送脚本，仅 `--email` 时需要）
- pandoc（Pipeline C docx 导出）
- 能访问外网（供 WebSearch / WebFetch）
- Gmail SMTP 凭据（仅 Pipeline C `--email` 时需要，见 `.env.example`）

---

## 参考文件

- **README.md** — 面向最终用户的使用文档（安装、示例、自定义）
- **AGENTS.md** — Agent 链的可视化流程图与工具表
- **examples/** — 两个完整产出样例，撰写新功能时可作为格式基准
- **.env.example** — Pipeline C 邮件投递所需的环境变量模板
