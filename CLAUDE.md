# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在此仓库工作时提供指引。

---

## 项目定位

这是一个 **Claude Code 插件**（`sci-research`，当前版本 1.18.0），通过多 Agent 编排，将"主题 + 比较实体 + 输出语言"转化为高质量研究/新闻产出。插件包含六条**完全独立**的流水线，互不共享 Agent：

| 特性 | `/sci-research` | `/news-scan` | `/daily-news-intelligence` | `/daily-briefing` | `/reputation-track` | `/weekly-report` |
|---|---|---|---|---|---|---|
| **目标** | 多实体对比的科普研究文章 | 指定时间窗内的新闻简报 | 单国每日新闻简报 | 多国品牌新闻简报（SPD Bank） | 公司声誉风险监控 | 周度宏观与市场报告 |
| **时间焦点** | 历史 + 当前 | 近 7/30/90 天 | 单日（指定日期） | 单日（读取已有报告） | 单日（指定日期） | 前 7 日滚动 |
| **来源** | 学术论文、官方报告、权威媒体 | 通讯社、财经媒体、行业媒体 | T1-T4 分级媒体（逐 URL 日期核验） | Pipeline C 产出的各国 Markdown | News (T1-T4) + Reddit + X | Pipeline C 报告 + FRED/BOE/BOJ/yfinance 行情 |
| **Agent 链** | researcher → comparator → fact-checker → writer | news-scanner → news-imager → news-analyst | daily-news-scanner（单 agent，顺序扫全类目） → news-verifier → daily-fact-extractor → daily-news-writer（× langs） → daily-editor（× langs） | briefing-curator → docx 脚本 → 邮件脚本 | reputation-resolver → reputation-scanner×3 → reputation-classifier → reputation-writer | weekly-news-aggregator ‖ market-data-collector → weekly-report-writer |
| **产出** | ≤5000 字结构化文章（含 APA 引用） | 1000-3000 字简报（含事件时间线 + 图片） | 条件化 6/7 栏简报（中国 7 栏含涉华，其余 6 栏；Markdown + docx；**单/双语模式**：`--lang zh\|en\|ja` 单语 1 套文件，`--lang zh+en` 等 6 种双语组合 2 套文件 + 堆叠双语邮件正文） | 13-15 条品牌 Word 文档（含邮件投递） | 仅当命中负面时发送 HTML 邮件（inline body，无附件） | 多分节 Markdown + docx（市场事件 + Money Market + Fixed Income + FX + Commodity，可邮件投递） |

**Pipeline C 八个结构性设计**（容易被忽视）：
1. **China 外部视角**：`--country "China"` 时 Source Matrix 本身就是外部视角 — 不查询中国本土媒体（Xinhua / Caixin / SCMP / People's Daily / TechNode / 澎湃 等），不查询中国政府域名（`gov.cn` / `pbc.gov.cn` / `stats.gov.cn` 等）。T4 改用外部机构清单（IMF / World Bank / WTO / OECD / BIS / IEA / Treasury / USTR / State Dept / Commerce-BIS / White House / EU Commission / UK Gov / METI / MOFA Japan）。
2. **Writer 自由文笔**（1.9.0+）：Writer 不再机械翻译 Verifier 包，按目标语言以解释性新闻文笔重写 — 数字/姓名/日期/直接引语必须忠于源，其余措辞自由组织。
3. **Fact-Manifest + Editor 双层防线**（1.11.0+）：Verifier 之后插入 `daily-fact-extractor`（sonnet）抽取每条 story 的 hard_facts / quotes 的 verbatim YAML manifest；Writer 之后插入 `daily-editor`（opus）跑核查，用 `Edit` 在原文件改。**Writer 引用规则反转**：search URL 必须进 References（References = Verifier KEEP URLs ∪ {支撑了正文事实的 search URLs}）。**引号 canonical 钉死**：en `""` U+0022 / zh `""` U+201C/U+201D / ja `「」` U+300C/U+300D，hook 字符级阻断。**Editor 五道核查（1.16.0+）**：Pass 1 Verifier-locked 事实 / Pass 2 Writer-search 事实回填 / Pass 3 引语逐字 / Pass 4 引号规范化 / **Pass 5 局部通顺 + 逻辑空洞修补**（新；闭合 5 类缺陷白名单：`pass2-cut-gap` / `foreign-residue` / `inconsistent-name` / `filler-marker` / `awkward-connector`；**无 WebSearch / WebFetch**；每 story ≤ 3 Edit、全文 ≤ `2 × story_count`；动 6 个不变量任一失败立即回滚；不可恢复失败时 Pass 5 graceful abort，pipeline 不阻断）。Pass 5 永远不动 `###` 标题 / References 块 / URL / 引号内文本 / 段落数 / H1 / `##` H2。
4. **条件化类目（1.12.0+）**：栏目集**按 `country` 派生**，不是写死 5 栏。非中国日报 6 栏（econ / politics / tech / society / **ipo_ma** / other）；中国日报 7 栏（第 5 位插入 **china_nexus**）。`china_nexus`（海外涉华财经，**仅财经口径**——投资/FDI/商业与产业政策/关税/出口管制/制裁/投资审查；纯外交归第 2 栏政治与外交）仅中国日报出现、强制跨境（中国×境外方，经济渠道）、排除中国对非洲/小型发展中经济体援助与基建贷款（关键产业例外）、关键产业优先；`ipo_ma`（企业IPO与并购）所有日报都有、聚焦本报告国公司（买方/卖方/上市主体）。**ipo_ma 重要性 3 带（1.15.0+）**：主带 IPO≥3 亿/并购≥5 亿美元（或受审或触及中国关键产业）进主池；**软带 USD 50M ≤ value < 主带门槛**写 Reserve Pool（仅 Fallback 1.5 升格）；<50M 硬 DROP。真源 = `references/language-spec.md` § Category Catalog & Selection（身份/命名/排序/编号）+ `references/rubric.md` § Conditional & Topical Categories（资格/排除/3 带门槛/Cat5↔Cat6 路由）。H2 编号随类目位置变（`ipo_ma` 非中国是第 5、中国是第 6）。格式钩子与类目数无关，不需改。
5. **单 Scanner + 双-Pass 源模型（1.13.0+，1.17.0 合并为单 agent）**：Scanner **单一实例顺序扫全部类目**（原并行 ×N + Merger 架构因 token 消耗过大而合并）。Scanner 跑 **Pass A**（矩阵 tier 阶梯，矩阵=种子+权威标定+China 红线，非硬墙）+ **Pass B**（无 site: 自由发现，按 `references/rubric.md` § Source Legitimacy 分级：auto-accept / conditional-accept 封顶 T2 / hard-reject；付费墙原文的免费全文转载豁免为合法 Lead；ipo_ma 加 SEC EDGAR 一手申报；China 报告 Pass B 套中国本土媒体/gov denylist）。完成全类目后 Scanner 内部执行跨类去重 + Cat5↔Cat6 路由（原 Merger 职责），产出统一 Scanner Bundle（`references/schemas.md` § Scanner Bundle Schema）交 Verifier。Verifier 五检查不变（输入 Scanner Bundle，去重/路由仅验证不重做）。代价：丧失并行加速（顺序扫比并行慢），换取大幅降低 token 消耗（省去 6-7 个 Scanner subagent context + 1 个 Merger context）。**搜索词模型（1.14.0+）**：栏目检索词从写死 OR 串改为**逐词扫**——每词单发一条 query、多词短语加引号、禁 `OR` 拼接（长 OR 会退化丢尾词）；词集大幅拓宽；T4-official / T1-wire / T1-flagship 三高层**整表逐词全跑、不受 `min_per_category` 早停**（min 仅管是否下探 T2/T3）；`ipo_ma` 一手申报查询（SEC EDGAR / LSE RNS / 交易所披露 + 财经垂直）与 `china_nexus` 外部-T4 + 全球通讯社主题扫提为**永远首发渠道**（不再"低于 min 才进"）。真源 = `skills/daily-news-intelligence/agents/daily-news-scanner.md` § Step 1 + § Conditional Categories；`SKILL.md` 不再复制词表（改为指针，杜绝漂移）。
6. **Subagent 派发 = 内置 `general-purpose` + 嵌入 `agents/*.md` body（永久模型，全 6 条流水线通用）**：**A / B / C / D / E / F 全部 stage** 一律以内置 `general-purpose` spawn，并**显式传 `model`**（`general-purpose` 不读 frontmatter `model:`，必须显式指定）。各流水线模型分配：
   - **A**: researcher=sonnet / comparator=opus / fact-checker=sonnet / writer=opus
   - **B**: news-scanner=sonnet / news-imager=sonnet / news-analyst=opus
   - **C**: Scanner / Verifier / Fact-Extractor = sonnet；Writer / Editor = opus
   - **D**: briefing-curator=opus
   - **E**: reputation-resolver=opus / reputation-scanner ×3=sonnet / reputation-classifier=sonnet / reputation-writer=opus
   - **F**: weekly-news-aggregator=sonnet / market-data-collector=sonnet / weekly-report-writer=opus

   **历史背景（rationale 单一真源在本条；SKILL.md 只描述流程，不再重复 rationale）**：1.16.2 之前 `agents/*.md` 放在 plugin 根目录，Claude Code 会自动注册为 `sci-research:*` 子 agent；marketplace 插件子 agent 运行时拿不到 `WebSearch`/`WebFetch`（`Grep`/`Glob`/`Bash`/MCP 也不稳），即便 frontmatter 声明也没用（Claude Code 缺陷 **anthropics/claude-code#21318，closed as "not planned"**，无上游修复；旁证 #25200 / #52055 / #46250 / #31002），那样 spawn 的插件 agent 会**静默编造 URL/日期/JSON**——只有查 `tool_uses` 才发现。1.16.2 起 `agents/` 子目录搬到各 skill 下（不再 auto-register），并把 dispatch 永久改为 "general-purpose + embed body"，**两层防线叠用**：即便将来 Claude Code 修了 #21318，这套机制也不再回退（避免每条流水线代码大改）。`agents/*.md` 一律视为**提示词模板**，编排器须 `Read` 文件→剥 frontmatter→body 当指令 prompt→注入参数+上游数据。流程细节见各 skill 的 SKILL.md § Subagent Dispatch Rule。Hooks 不受影响（PostToolUse/PreToolUse 按工具调用触发，与 agent 类型无关）。
7. **Reserve Pool + Three-Step Coverage Fallback（1.15.0+）**：解决"当日来源稀疏 / 付费墙挤压"导致分类 < `min_per_category` 时的兜底通道。Scanner Pass B 把**通过日期门 + 红线 + Legitimacy 但卡在 authority cap 下方**的 conditional-accept 候选（T3-niche / T3-trade / 小型国家媒体）写入 `## Reserve Pool`（`Held: below-authority-cap`）而非丢弃；`ipo_ma` 软带（USD 50M ≤ value < 主带门槛）同入 Reserve Pool（`Held: below-ipo-ma-floor`）。Scanner § Step 6 同样的去重原则把 Reserve Pool 汇总到 Scanner Bundle。Verifier 的兜底从 Two-Step 升为 **Three-Step**：**Fallback 1** 放宽 impact tier→`Regional-structural`；**Fallback 1.5**（新）从 Reserve Pool 升格——按 best-first（更接近 T2、更原创、更高 impact、auto-accept 优先），promote 出来的故事标 `Origin: reserve-pool` + `Authority score: T3-extended`（仅 below-authority-cap 用），且**stop-at-floor**（够 min 即停）；Fallback 1.5 仍**revalidate Source Legitimacy**——`Illegitimate-source` 不放过；**Fallback 2** 录 gap。**永远不放宽**：日期、China 红线、Originality `Syndicated-rewrite`、Source Legitimacy `Illegitimate-source`。真源 = `references/rubric.md` § Three-Step Coverage Fallback + § Conditional & Topical Categories 三带；Scanner / Verifier 两 agent 同步实现。Output Schema 拓展：`Fallback used: fallback_1+1.5 | fallback_1+1.5+gap`；新字段 `Reserve pool input count / promotions / Reserve Pool — Held` block。
8. **双语模式 + 上游复用（1.18.0+）**：`--lang` 既接受单语（`zh` / `en` / `ja`）也接受双语组合（`zh+en` / `en+zh` / `zh+ja` / `ja+zh` / `en+ja` / `ja+en`，共 6 种排列；3 语暂不支持）。**架构关键：上游 3 stage（Scanner / Verifier / Fact-Extractor）只跑 1 次**——因为它们是英文 language-agnostic 的；Writer + Editor **per-lang fan out**，每语一个 subagent 实例，写 `out_md_{lang}` / `out_docx_{lang}`，pandoc 也跑 N 次。Token 成本约 +70%（对比单语；如果完全跑 2 遍则是 +100%）。**邮件 Step 10**：双语模式下 subject 用 primary-lang + 双语 tag（`（中英双语）` / `(Bilingual EN+ZH)`）；body 堆叠 primary-lang 全文 + `━━━━━━━━━━━` 分隔线 + secondary-lang 全文；`--email-attach both` 附 4 个文件（zh.md / zh.docx / en.md / en.docx），`docx` 附 2 个，`md` 附 2 个，`none` 附 0。`send-report-email.py --attach` 已是 `nargs="*"`，**无需改 Python 脚本**。每个 lang 派生字段（`out_md_{lang}` / `country_display_{lang}` / `date_display_{lang}`）独立计算；filename ASCII-only 自检（zh/ja 必须翻译过 country）按 per-lang 验。Failure：单边 Writer 失败默认 halt + 报错。真源 = `references/language-spec.md` § Bilingual Mode + `references/email-spec.md` § Bilingual subject + § Bilingual body。

---

## 仓库结构

```
sci-research/
├── .claude-plugin/
│   ├── plugin.json              # 插件元数据（name, version, author）
│   └── marketplace.json         # 市场清单
├── commands/                    # 6 个主命令 + 2 个工具命令
│   ├── sci-research.md          # /sci-research 入口
│   ├── news-scan.md             # /news-scan 入口
│   ├── daily-news-intelligence.md # /daily-news-intelligence 入口
│   ├── daily-briefing.md        # /daily-briefing 入口
│   ├── reputation-track.md      # /reputation-track 入口
│   ├── weekly-report.md         # /weekly-report 入口
│   ├── add-entity.md            # /add-entity 会话中加实体
│   └── set-lang.md              # /set-lang 切换输出语言
├── skills/                      # 六个独立 Skill 工作流；agents/*.md 作为提示词模板挂在各 skill 下（不在 plugin 根，避免 Claude Code 把它们注册成 `sci-research:*` 子 agent — 真源 § 项目定位 第 6 条）
│   ├── sci-research/            # Pipeline A
│   │   ├── SKILL.md
│   │   └── agents/              # 提示词模板（非注册子 agent）
│   │       ├── researcher.md            # 每实体多源检索
│   │       ├── comparator.md            # 跨实体维度对比分析
│   │       ├── fact-checker.md          # 关键论断核验
│   │       └── writer.md                # 多语言文章合成
│   ├── news-scan/               # Pipeline B
│   │   ├── SKILL.md
│   │   └── agents/
│   │       ├── news-scanner.md          # 每实体实时新闻抓取（时间窗 7d/30d/90d，不取图）
│   │       ├── news-imager.md           # 热点事件图片提取与校验
│   │       └── news-analyst.md          # 去重、时间线、影响分析
│   ├── daily-news-intelligence/ # Pipeline C
│   │   ├── SKILL.md
│   │   ├── agents/
│   │   │   ├── daily-news-scanner.md    # 单 agent 顺序扫全类目（Pass A 矩阵 + Pass B 自由发现，严格日期核验；§ Step 6 跨类去重 + Cat5↔Cat6 路由；China=外部视角）
│   │   │   ├── news-verifier.md         # 编辑台五检查（原创性/权威性/影响力/正版性/去重验证，输入 Scanner Bundle）
│   │   │   ├── daily-fact-extractor.md  # Verifier KEEP → YAML Fact Manifest（hard_facts / quotes / locked_urls，sonnet，不上网）
│   │   │   ├── daily-news-writer.md     # 多语言每日简报合成（吃 Verifier + Manifest，自由文笔 + search URL 强制进 References）
│   │   │   └── daily-editor.md          # Writer 之后五道核查（1-4 事实 / 引语 / 引号 + 5 局部通顺与逻辑空洞修补，闭合 5 类缺陷白名单，无 web），用 Edit 在原文件改
│   │   └── references/          # Pipeline C 的规范文档
│   │       ├── email-spec.md
│   │       ├── language-spec.md
│   │       ├── output-spec.md
│   │       ├── rubric.md
│   │       ├── schemas.md
│   │       └── verification.md
│   ├── daily-briefing/          # Pipeline D（完全独立）
│   │   ├── SKILL.md
│   │   ├── agents/
│   │   │   └── briefing-curator.md      # 多国新闻筛选改写（读取已有 MD，不搜索）
│   │   ├── template/
│   │   │   └── briefing-template.docx   # SPD Bank 品牌模板
│   │   ├── references/
│   │   │   └── email-spec.md            # 独立邮件模板规范
│   │   └── scripts/
│   │       ├── generate-branded-docx.py # docx 生成脚本
│   │       └── send-briefing-email.py   # 独立邮件发送脚本
│   ├── reputation-track/        # Pipeline E（完全独立）
│   │   ├── SKILL.md
│   │   ├── agents/
│   │   │   ├── reputation-resolver.md   # ticker/name → 公司 + 高管列表消歧
│   │   │   ├── reputation-scanner.md    # 每源并行扫 News/Reddit/X（不判负面）
│   │   │   ├── reputation-classifier.md # 逐条打分：category + severity + verbatim quote
│   │   │   └── reputation-writer.md     # 渲染内联 HTML 邮件正文（模板固定）
│   │   └── references/          # Pipeline E 的规范文档
│   │       ├── entity-resolution.md     # 代码/名字消歧 + 高管抓取
│   │       ├── source-matrix.md         # News + Reddit + X 的搜索模板
│   │       ├── negativity-rubric.md     # 分类 + 严重度 + 可信度加权
│   │       ├── html-template.md         # 内联 CSS HTML 邮件正文骨架
│   │       ├── email-spec.md            # 调用 send-report-email.py 的契约
│   │       └── schemas.md               # Resolver/Scanner/Classifier 输出格式
│   └── weekly-report/           # Pipeline F
│       ├── SKILL.md
│       ├── agents/
│       │   ├── weekly-news-aggregator.md # 读 7 天 Pipeline C 报告，去重 + 按国家分组
│       │   ├── market-data-collector.md  # 并行跑 FRED / BoE / BoJ / yfinance 脚本，聚合 JSON
│       │   └── weekly-report-writer.md   # 消费 events bundle + market data bundle，按语言本地化合成 Markdown
│       └── (references / scripts 见 skill 目录)
├── contexts/
│   └── sci-research.md          # 研究模式行为上下文
├── hooks/
│   └── hooks.json               # 8 个质量钩子的配置
├── scripts/
│   ├── hooks/                   # 钩子实现（Node.js）
│   │   ├── word-count-check.js          # [A] 限字（含中文字符数）
│   │   ├── entity-coverage-check.js     # [A] 实体覆盖校验
│   │   ├── reference-validator.js       # [A] 引用完整性校验
│   │   ├── news-freshness-check.js      # [B] 新闻时效校验
│   │   ├── daily-news-format-check.js   # [C] Markdown 格式硬阻断（计数/[N]连续/URL/禁用模式）
│   │   ├── weekly-report-format-check.js # [F] 周报 Markdown 格式硬阻断
│   │   ├── email-send-guard.js          # [C/D/E/F] 阻断 inline SMTP，强制走 send-*-email.py
│   │   └── research-summary.js          # [A&B] 会话元数据日志
│   └── send-report-email.py     # [C & E & F] Gmail SMTP 邮件发送脚本（支持 --body-html-file）
├── rules/research/              # 三份质量规则
│   ├── source-credibility.md    # [A] 学术来源分级
│   ├── output-format.md         # [A] 文章格式规范
│   └── news-source.md           # [B] 新闻来源分级与去重
├── examples/                    # 完整产出样本
│   ├── nuclear-fusion-zh.md     # 核聚变能源（中/美/EU/日本）
│   └── mrna-vaccine-en.md       # mRNA 疫苗（US/EU/China）
├── .env.example                 # Gmail SMTP 环境变量模板
├── .gitignore
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
/daily-news-intelligence --country "Japan" [--date 2026-04-14] [--lang zh|en|ja|zh+en|en+zh|zh+ja|ja+zh|en+ja|ja+en] [--out-dir <path>] [--min-per-category <N>] [--email <a@x.com,b@y.com>] [--email-attach both|docx|md|none] [--email-dry-run]

# 多国品牌新闻简报（读取已有报告，生成 SPD Bank 品牌 Word）
/daily-briefing [--date 2026-04-16] [--countries "中国,英国,美国,欧洲,日本,韩国"] [--total 14] [--email <a@x.com>] [--email-dry-run] [--no-wait]

# 公司声誉风险监控（仅在命中负面时发 HTML 邮件）
/reputation-track --company "<名字或股票代码>" [--date 2026-04-21] [--lang zh|en] [--sources news,reddit,x] [--severity-min low|medium|high] [--email <a@x.com>] [--email-dry-run]

# 周度宏观与市场报告（读前 7 日 Pipeline C 报告 + 实时行情）
/weekly-report [--end-date 2026-05-11] [--start-date 2026-05-05] [--countries "CN,US,UK,EU,JP,KR"] [--lang zh|en|ja] [--out-dir <path>] [--news-dir <path>] [--commodity-symbols "GC=F,SI=F,CL=F"] [--kr-bond-symbol 148070.KS] [--email <a@x.com,b@y.com>] [--email-attach both|docx|md|none] [--email-dry-run]

# 会话中追加实体（Pipeline A & B）
/add-entity "Entity3,Entity4"

# 切换输出语言
/set-lang en
```

`--lang` 默认 `zh`，`--period` 默认 `30d`，`--min-per-category` 默认 `2`。

---

## 六条流水线的 Agent 编排

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
  └─→ Daily-News-Scanner ─────────────────────────→ News-Verifier ─→ Daily-Fact-Extractor ─→ Daily-News-Writer ─→ Daily-Editor ─→ pandoc → 邮件（可选）
      (sonnet, 单 agent, 顺序扫全类目)               (sonnet)         (sonnet, 不上网)        (opus, 带 search)    (opus, 仅 Edit)
      Pass A 矩阵 + Pass B 自由发现                  原创性/权威性/   抽取 hard_facts /       消费 Verifier +     五道核查
      逐 URL 日期核验 + 正版分级                      影响力/正版/去重  quotes → YAML manifest  Manifest，search    （含引号规范化
      + 跨类去重 + Cat5↔Cat6 路由（§ Step 6）        验证（输入 Scanner Bundle）  (事实锚点表)   URL 强制进 References + 通顺修补）
```

| Agent | 模型 | 工具 | 职责 |
|---|---|---|---|
| daily-news-scanner | sonnet | WebSearch, WebFetch, Read, Grep, Glob | **单一实例顺序扫全部类目（1.17.0 合并）**，Pass A + Pass B per category，完成后在 § Step 6 执行跨类去重 + Cat5↔Cat6 路由（原 Merger 职责），输出统一 Scanner Bundle（`references/schemas.md` § Scanner Bundle Schema）。**Pass A**：矩阵 tier 顺序搜索（T4-official→T1-wire→T1-flagship→T2→T3）；**Pass B**：无 site: 自由发现，按 rubric § Source Legitimacy 分级（auto/conditional 封顶 T2/hard-reject），ipo_ma 加 SEC EDGAR 一手申报，China 报告对 Pass B 套中国本土媒体/gov 域名 denylist。逐 URL WebFetch 严格日期核验（必须等于 date，不接受邻近日）。**付费墙补救（Step 3.5，1.16.3+ 反转）**：硬付费墙域名（Bloomberg/FT/WSJ/Economist/Telegraph/Times/Nikkei Asia 等）**Lead-eligible**——先用 title 关键词反搜免费媒体（Reuters/AP/AFP/BBC/Guardian/Kyodo）找替代 Lead（找到→免费媒体进 Lead，付费墙挂 `Corroborated by`，`Body-source: full`）；**找不到→付费墙本身就是 Lead**，打 `Body-source: paywall-stub` 标记，由 Writer 强制跑 ≥2 次 WebSearch/WebFetch 把 body 凑到 ≥200 字（search URL 必须进 References）、Editor Pass 3 把抓不到原文的直接引语降级为间接引语。设计取舍：牺牲付费墙独家爆料的事实抽取密度，换不再丢稿；Fact-Extractor 接受稀疏 manifest，Editor Pass 1 按 `body_source` scale 期望。Verifier 透传 `Corroborated by` + `Body-source`，Writer 给每个 URL 单独发一条 APA `[N]`。**`country = China` 时**：T1-wire 只 Universal（无 Xinhua / China News Service），T1-flagship Country-of-coverage 为空（无 Caixin / People's Daily / SCMP），T3 无 Country: China 行，T4 改用外部机构清单（IMF / World Bank / WTO / OECD / BIS / IEA / Treasury / USTR / State Dept / Commerce-BIS / White House / EU Commission / UK Gov / METI / MOFA Japan）。中国政府域名永不查询。 |
| news-verifier | sonnet | Read, Grep, Glob, WebFetch | 编辑台五检查（原创性 / 权威性 / 影响力 / **正版性** / 去重验证），输入 **Scanner Bundle**；Pass-A 源预清，Pass-B 套 rubric § Source Legitimacy（不合格 DROP `Illegitimate-source`）；去重/路由已在 Scanner § Step 6 完成，仅验证。输出 KEEP/DROP 集 |
| daily-fact-extractor | sonnet | Read, Write, Grep | **新增（1.11.0）**：读 Verifier KEEP bundle，对每条 story 抽取 hard_facts（数字 / 命名 / 日期 / 机构 / 产品的 verbatim value + source_url + factual_excerpt 子串）+ quotes（speaker + verbatim_en + source_url），输出 YAML Fact Manifest 到 `${OUT_DIR}/fact-manifest-{country_slug}-{date}.yaml`。**不上网、不写叙事、不翻译**。Manifest 是 Writer 的"locked values"硬约束 + Editor 的事实核查 ground truth。 |
| daily-news-writer | opus | Read, Write, Edit, Grep, WebSearch, WebFetch | 消费 Verifier KEEP + Fact Manifest，按目标语言**自由文笔**重写。Manifest 锁定的数字 / 命名 / 日期 / 引语**不可漂移**（值必须匹配 manifest）。**默认每 story 跑 1-3 次 WebSearch / WebFetch 拉背景**。**引用契约**：References = Verifier KEEP URLs ∪ {支撑了正文事实的 search URLs}——search URL 必须进 References（APA + 连续 `[N]`）。引号按 canonical 表（en `""` / zh `""` / ja `「」`）。 |
| daily-editor | opus | Read, Edit, Grep, WebFetch, WebSearch | **新增（1.11.0），1.16.0+ 升至 5 道核查**：Writer 之后顺序跑 — **Pass 1** Verifier-locked 事实是否与 Manifest 一致（漂移即改回）；**Pass 2** Writer-search 事实是否在 References 有 URL（缺则 search 补 ref / 砍句 / 弱化）；**Pass 3** 直接引语逐字 WebFetch 对源（不一致则降级为间接引语）；**Pass 4** 引号字符规范化；**Pass 5** 局部通顺 + 逻辑空洞修补（闭合 5 类缺陷白名单：`pass2-cut-gap` 修复 Pass 2 砍句留下的桥；`foreign-residue` 翻译腔改写；`inconsistent-name` 跨故事统一人名/机构名；`filler-marker` 删 Writer 漏过的填充词（闭合白名单）；`awkward-connector` 句内连接词错位）。**只用 Edit，不 Write**；Pass 2+3 预算 2 WebSearch + 4 WebFetch / story；Pass 5 **零 web 调用**、每 story ≤ 3 Edit、全文 ≤ `2 × story_count`、6 不变量自检失败即回滚（manifest 事实保留 / References 字节相同 / 段落数不变 / 标题不变 / 引号配对平衡 / 无禁用 marker）；Pass 5 不可恢复失败时 abort 但 pipeline 不阻断；产出 stdout 报告供日志。 |

**条件化栏目（按 `country` 派生，真源见 `references/language-spec.md` § Category Catalog & Selection）**：
- 非中国日报（6 栏）：经济与市场 → 政治与外交 → 科技与产业 → 社会与民生 → 企业IPO与并购 → 其他重要事件
- 中国日报（7 栏，第 5 位插入涉华）：经济与市场 → 政治与外交 → 科技与产业 → 社会与民生 → 海外涉华财经 → 企业IPO与并购 → 其他重要事件

**输出**：Markdown 文件 + pandoc 导出 docx，可选 Gmail SMTP 邮件投递（支持 `--email-dry-run` 预览）

**外部视角中国（1.9.1+ 结构性设计）**：`/daily-news-intelligence --country "China"` 用矩阵结构本身实现外部视角，不靠条件分支或覆盖逻辑。设计点：
- Source Matrix 里的 `Country: China` 行（T1-wire / T1-flagship / T3）已全部删除
- `Country: Hong Kong | SCMP` 行已删除
- T4 主表的中国机构 examples 已清空（PBOC / 国务院 / CSRC / NFRA / NBS / MFA / NDRC / MIIT / GACC / NEA / 最高人民法院 / 财政部 都不再列），T4 表底新增 China external-T4 子表 + 中国政府域名禁止清单
- Step 2.1 T4 段对 `country = China` 写明改用 external-T4 表
- Paywall Status 三表同步删除中国本土媒体行（Caixin / SCMP / Xinhua / China News Service / People's Daily / Yicai / Sixth Tone）
- 实际 China 搜索池：57 家（T4: 15 / T1-wire: 5 / T1-flagship: 14 / T2: 5 / T3: 18），~40 可做 Lead，~16 只能 Corroborated

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
| reputation-scanner (×3) | sonnet | WebSearch, WebFetch, Read, Grep, Glob, **mcp__apidirect__search_reddit**, **mcp__apidirect__search_twitter** | 每源一个实例并行。News 走 WebSearch+T1-T4；**Reddit/X 走 apidirect MCP 单次调用**（月 50 token 预算，每次 run 2 token）。只抓不判 |
| reputation-classifier | sonnet | Read, Grep, Glob, WebFetch | 逐条打 category + severity + 可信度；WebFetch 源文件提 verbatim quote；跨源去重；低于 severity_min 丢弃 |
| reputation-writer | opus | Read, Write, Edit, Grep | 按 `html-template.md` 渲染内联 CSS HTML；verbatim quote 原样；生成 TL;DR |
| send-report-email.py `--body-html-file` | — | Gmail SMTP | 扩展后支持 HTML body，multipart/alternative 自动生成 text/plain 降级 |

**关键约束**：
- `total_items_kept == 0` → 静默退出，不写 HTML 文件，不发邮件
- **覆盖范围**：News (T1-T4) + Reddit（apidirect MCP，单次调用）+ X（apidirect MCP，单次调用）。**Facebook 和 Threads 不在 v1 覆盖**
- **apidirect 配额**：月 50 token 免费，每次 `/reputation-track` 烧 2 token（Reddit + X 各 1），支持 ~25 runs/month。Scanner 禁止重试或分页
- 每条输出必须含源文件的 verbatim 引用 — 不改写、不编造
- 低可信度（Reddit/X）声称 high/critical 时需 T1-T3 佐证，否则降级或丢弃

**输出**：
- `{out_dir}{company_display}-reputation-{date}.html`（内联 CSS，最大 600px，无外部资源）
- 邮件主题格式：`[声誉预警] {公司} — {日期} · {N} 项负面（{最高严重度}）`

### Pipeline F — `/weekly-report`

```
End Date (default: today) → 计算前 7 日窗口
  │
  ├─→ Weekly-News-Aggregator (Stage A) ─┐
  │   读 daily-news-reports/ 前 7 日各国 MD                  ├─→ Weekly-Report-Writer ─→ pandoc → 邮件（可选）
  │   去重 + 按国家分组 → WeeklyEventsBundle                  │       (opus)
  │   (sonnet)                                              │       消费两个 bundle，按
  │                                                          │       lang 本地化 section 标题，
  └─→ Market-Data-Collector (Stage B) ──┘       合成 Markdown
      并行调 FRED / BoE / BoJ / yfinance
      聚合 JSON → MarketDataBundle
      (sonnet)
```

| Agent / 组件 | 模型 | 工具 | 职责 |
|---|---|---|---|
| weekly-news-aggregator | sonnet | Read, Bash, Grep, Glob | 读 `--news-dir` 下前 7 日各国 Pipeline C 报告，**不上网**；去重相同事件，按国家分组，输出 WeeklyEventsBundle |
| market-data-collector | sonnet | Bash, Read | 并行跑 FRED（货币市场 + 汇率）、BoE + BoJ + FRED（固收）、yfinance（KR ETF 代理 + 商品期货）脚本；不读新闻，不写报告；聚合为 MarketDataBundle |
| weekly-report-writer | opus | Read, Write, Edit, Grep | 消费两个 bundle，按 `language-spec.md` 本地化 section 标题，按 `output-spec.md` 输出 Markdown；不上网，不调脚本，不翻译 URL / APA |

**Pipeline F 分节**：Market event → Money Market → Fixed Income → FX → Commodity

**关键约束**：
- weekly-news-aggregator **绝不上网**，只读本地 Pipeline C 报告 — 因此前一周必须有 daily-news-intelligence 跑过
- market-data-collector 不读新闻，weekly-report-writer 不上网 — 三段职责互不越界
- `weekly-report-format-check` hook 在 PostToolUse:Write 时硬阻断格式违规

**输出**：Markdown 文件 + pandoc 导出 docx，可选 Gmail SMTP 邮件投递

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

### Pipeline C（T1-T4 分级，按 tier 自上而下搜索）
| 级别 | 类型 | 示例 |
|---|---|---|
| T4-official | 政府 / 央行 / 监管 / 议会 / 法院的官方发布 | Fed, ECB, BoE, BoJ, US Treasury, USTR, State Dept, EU Commission, gov.uk, IMF, World Bank, WTO, OECD |
| T1-wire | 国际通讯社 | Reuters, AP, AFP, Bloomberg, DJ Newswires; 国别：Kyodo (JP), Yonhap (KR), TASS (RU) |
| T1-flagship | 全球旗舰报纸 / 国别旗舰 | FT, WSJ, Economist, NYT, WaPo, Guardian, BBC, Telegraph, Times (London), Le Monde, Spiegel, FAZ, El País, Nikkei Asia |
| T2 | 区域旗舰 / 主流 | NHK World, ABC Australia, Straits Times, Korea Herald, The Hindu, CNBC, CNN, NPR, Politico Europe, DW |
| T3 | 行业垂直 | TechCrunch, MIT Tech Review, Wired, Finextra, S&P Global, STAT News, MLex, Law360 |

**China 特殊处理（1.9.1+）**：`country = China` 时矩阵结构本身就是外部视角 — 不含 Xinhua / Caixin / People's Daily / SCMP / TechNode / 澎湃 等中国本土媒体；不查询 `gov.cn` / `pbc.gov.cn` / `stats.gov.cn` 等中国政府域名；T4 改用 IMF / World Bank / WTO / OECD / BIS / IEA / Treasury / USTR / State Dept / Commerce-BIS / White House / EU Commission / UK Gov / METI / MOFA Japan 等外部机构清单。详见 `skills/daily-news-intelligence/agents/daily-news-scanner.md` § Source Matrix § T4-official 表底 + Step 2.1。

详细规则见 `skills/daily-news-intelligence/references/rubric.md`。

---

## 质量钩子（hooks/hooks.json）

| Hook | 流水线 | 触发 | 行为 |
|---|---|---|---|
| word-count-check | A | PostToolUse:Write | 超过 5000 字 / 7500 中文字符则阻断 |
| entity-coverage-check | A | PostToolUse:Write | 实体无专节或提及 <3 次则警告 |
| reference-validator | A | PostToolUse:Write | 内文 `[N]` 与参考条目不一致则警告 |
| news-freshness-check | B | PostToolUse:Write | 近 7 天内无来源则警告 |
| **daily-news-format-check** | **C** | **PostToolUse:Write + Edit** | **Writer/Editor 输出格式违规即阻断。基础校验：blockquote 来源 / 斜体 in-text / 全局 `## 参考文献` / 缺 `[N]` / `[N]` 不连续 / 缺 URL / `### == 摘要 == **References**` 数目不符。**1.11.0 新增**：(a) 引号 canonical 字符级校验（按 H1 探测 lang，非 canonical 字符即阻断，配对不平衡即阻断；URL / APA / 代码块剥离）；(b) 引用完整性启发式（story 有引语但 0 URL → 阻断；≥5 带单位数字 + ≤1 URL → 阻断）。Edit 事件下从磁盘读文件（Edit 不带 tool_input.content）。** |
| **weekly-report-format-check** | **F** | **PostToolUse:Write** | **Pipeline F Markdown 格式违规即阻断（参见 `skills/weekly-report/` spec）** |
| **email-send-guard** | **C & D & E & F** | **PreToolUse:Bash** | **Bash 命令里检测到 inline `smtplib` / `email.message` / `MIMEMultipart` / `sendmail` / `mail -s` 且未调用 `send-*-email.py` → 阻断。防止 orchestrator 绕过 sanctioned 脚本导致附件 noname** |
| research-summary | A & B | Stop | 异步记录会话元数据（非阻断） |

---

## 开发约定

- **Agent 文件**：Markdown + YAML frontmatter（`name`, `description`, `tools`, `model`）
- **Skill 文件**：Markdown 明确分段（When to Activate / Workflow / Quality Rules）
- **Command 文件**：Markdown + description frontmatter
- **Hook 配置**：JSON，含 matcher 条件
- **文件命名**：全小写 + 连字符（kebab-case）
- **六条流水线完全独立**：修改一条流水线的 Agent 不影响其他流水线
- **多语言**：默认支持 zh / en / ja，新增语言需同步更新 `writer.md`、`news-analyst.md`、`daily-news-writer.md`、`weekly-report-writer.md` 与 `set-lang.md`
- **Pipeline C 规范文档**：集中在 `skills/daily-news-intelligence/references/` 目录下，修改前需通读相关 spec
- **Pipeline F 规范文档**：集中在 `skills/weekly-report/` 目录下；F 严格依赖 Pipeline C 前一周已跑过
- **China 外部视角是结构性约定**：改动 Source Matrix 时不要为了"对称"重新加入中国本土媒体或政府域名 — 这是 Pipeline C 的结构性设计而非疏漏

---

## 常见修改入口

| 目标 | 修改文件 |
|---|---|
| 调整 A 字数限制 | `scripts/hooks/word-count-check.js`（`WORD_LIMIT` / `CHAR_LIMIT_ZH`） |
| 调整 B 新鲜度窗口 | `scripts/hooks/news-freshness-check.js`（7 天常量） |
| 增加 A 对比维度 | `skills/sci-research/agents/comparator.md`（Section 1 Dimension Selection） |
| 新增输出语言 | `skills/sci-research/agents/writer.md` + `skills/news-scan/agents/news-analyst.md` + `skills/daily-news-intelligence/agents/daily-news-writer.md` + `commands/set-lang.md` + `skills/daily-news-intelligence/references/language-spec.md` |
| 调整 A 来源分级 | `rules/research/source-credibility.md` |
| 调整 B 新闻来源规则 | `rules/research/news-source.md` |
| 调整 C 来源分级与日期核验 | `skills/daily-news-intelligence/agents/daily-news-scanner.md` + `skills/daily-news-intelligence/references/rubric.md` |
| 调整 C 付费墙补救逻辑（Step 3.5，Lead-eligibility + Body-source） | `skills/daily-news-intelligence/agents/daily-news-scanner.md` § Source Matrix § Paywall Status + § Search Process § Step 3.5 + § Output Schema（`Body-source` 字段）；同步 `references/schemas.md`（Scanner/Verifier 两段都加 Body-source）+ `agents/news-verifier.md`（透传 Body-source）+ `agents/daily-fact-extractor.md`（按 body_source scale 期望）+ `agents/daily-news-writer.md`（paywall-stub 时 ≥2 次 WebSearch 强制）+ `agents/daily-editor.md`（Pass 3 paywall-stub 引语降级） |
| 调整 C Corroborated by 透传 | `skills/daily-news-intelligence/agents/news-verifier.md` + `skills/daily-news-intelligence/agents/daily-news-writer.md` + `skills/daily-news-intelligence/references/schemas.md`（三处必须同时改） |
| 调整 C Verifier 筛选逻辑 | `skills/daily-news-intelligence/agents/news-verifier.md` |
| 调整 C 输出格式 / Markdown 语法 | `skills/daily-news-intelligence/references/output-spec.md` |
| 调整 C Writer 文笔约束（自由度 vs 事实纪律） | `skills/daily-news-intelligence/agents/daily-news-writer.md` + `skills/daily-news-intelligence/references/output-spec.md` + `skills/daily-news-intelligence/references/language-spec.md`（三处同步） |
| 调整 C Fact Manifest schema / 抽取规则 | `skills/daily-news-intelligence/agents/daily-fact-extractor.md`（schema、kind 分类、locked_urls 约定都在 agent prompt 内） |
| 调整 C Editor 五道核查的判定 / 预算 | `skills/daily-news-intelligence/agents/daily-editor.md`（Pass 1-4 的判定阈值、WebSearch/WebFetch 预算上限；Pass 5 的 5 类缺陷白名单、每-story / 每-文档 Edit 上限、6 个回滚不变量） |
| 调整 C Editor Pass 5 缺陷类目（增/删/改 5 类缺陷判定） | `skills/daily-news-intelligence/agents/daily-editor.md` § Pass 5（5 类白名单是 Pass 5 的唯一 scope；删类需同时审视 Writer self-check 能否补位；加类需写明触发条件 + 允许动作 + 禁止动作 + 与现有 Pass 1-4 的非重叠证明） |
| 调整 C 引号 canonical 字符表 | `skills/daily-news-intelligence/references/language-spec.md` § Canonical Quote Marks + `skills/daily-news-intelligence/agents/daily-news-writer.md`（多处引用）+ `scripts/hooks/daily-news-format-check.js`（`forbiddenByLang` map） |
| 调整 C Writer 引用契约（search URL 是否进 References） | `skills/daily-news-intelligence/agents/daily-news-writer.md`（多处明文 + Quality Rules 第 4 条）+ `skills/daily-news-intelligence/references/output-spec.md` § Cited Search URLs |
| 调整 C 编排顺序（插入/移除 agent） | `skills/daily-news-intelligence/SKILL.md`（Quick Reference Checklist + Data Handoff Between Stages + Workflow Steps + Stage → Agent → Reference Map 四处同步） |
| 调整 C Scanner 顺序扫描拓扑（跨类去重 / 路由逻辑） | `skills/daily-news-intelligence/agents/daily-news-scanner.md`（§ Step 6）+ `skills/daily-news-intelligence/SKILL.md`（Step 2-3）+ `references/schemas.md`（§ Scanner Bundle） |
| 调整 C 源发现模型 / Pass B / 正版性 rubric | `references/rubric.md` § Source Discovery Model + § Source Legitimacy（真源）；镜像机制在 `skills/daily-news-intelligence/agents/daily-news-scanner.md` § Pass B — Free Discovery；Verifier 第 4 检查在 `skills/daily-news-intelligence/agents/news-verifier.md` |
| 调整 C China 外部视角矩阵 | `skills/daily-news-intelligence/agents/daily-news-scanner.md` § Source Matrix（T4 China 子表、T1-wire / T1-flagship / T3 行的增删、Paywall Status 三表） |
| 调整 C 邮件投递 | `skills/daily-news-intelligence/references/email-spec.md` + `scripts/send-report-email.py` |
| 调整 C 双语模式（1.18.0+ 新增/删除语言组合、修改双语 subject/body 模板、附件分发） | `skills/daily-news-intelligence/references/language-spec.md` § Bilingual Mode（解析 + 派生字段）+ `references/email-spec.md` § Bilingual subject + § Bilingual body（subject + body + attach 规则）+ `SKILL.md` Step 1 / 8 / 8.5 / 9 / 10（编排器 fan-out 循环）+ `commands/daily-news-intelligence.md`（`--lang` 校验 + 示例）；`send-report-email.py` 已是 `nargs="*"`，无需改 |
| 调整 C 栏目目录 / 命名 / 排序 / 编号 / 本地化 | `skills/daily-news-intelligence/references/language-spec.md` § Category Catalog & Selection（真源）；镜像在 `skills/daily-news-intelligence/agents/daily-news-writer.md` § Category Catalog & Selection |
| 调整 C 条件化类目规则（china_nexus 资格/排除/关键产业、ipo_ma 门槛、Cat5↔Cat6 路由） | `skills/daily-news-intelligence/references/rubric.md` § Conditional & Topical Categories（真源，Scanner/Verifier 引用）；搜索机制在 `skills/daily-news-intelligence/agents/daily-news-scanner.md` § Conditional Categories — Search Mechanics |
| 调整 C 类目集（增/删栏目、改国家派生规则） | `references/language-spec.md` § Category Catalog（active 规则）+ 同步 `daily-news-scanner.md` / `news-verifier.md` / `schemas.md` / `daily-news-writer.md` / `output-spec.md` / `verification.md` / `email-spec.md` / `SKILL.md` / `commands/daily-news-intelligence.md` / `daily-fact-extractor.md`（enum） |
| 调整 C Reference 格式校验规则 | `scripts/hooks/daily-news-format-check.js` + `skills/daily-news-intelligence/references/output-spec.md` § Self-Check Checksum |
| 调整邮件发送守卫（禁止 inline SMTP） | `scripts/hooks/email-send-guard.js` + 四份 SKILL.md（C/D/E/F）的 email Step 里的 "Hard rule" 段 |
| 修改 A 文章格式 | `rules/research/output-format.md` |
| 调整 D 品牌模板 | `skills/daily-briefing/template/briefing-template.docx` |
| 调整 D 新闻筛选逻辑 | `skills/daily-briefing/agents/briefing-curator.md` |
| 调整 D docx 生成 | `skills/daily-briefing/scripts/generate-branded-docx.py` |
| 调整 D 邮件投递 | `skills/daily-briefing/references/email-spec.md` + `skills/daily-briefing/scripts/send-briefing-email.py` |
| 调整 E 负面分类/严重度 | `skills/reputation-track/references/negativity-rubric.md` |
| 调整 E 数据源（News/Reddit/X）搜索模板 | `skills/reputation-track/references/source-matrix.md` |
| 调整 E HTML 邮件模板 | `skills/reputation-track/references/html-template.md` |
| 调整 E 实体消歧/高管抓取 | `skills/reputation-track/references/entity-resolution.md` + `skills/reputation-track/agents/reputation-resolver.md` |
| 调整 E 邮件投递 | `skills/reputation-track/references/email-spec.md` + `scripts/send-report-email.py`（`--body-html-file` 支持） |
| 调整 F 行情数据采集（FRED / BoE / BoJ / yfinance） | `skills/weekly-report/agents/market-data-collector.md` + `skills/weekly-report/scripts/*.py`（如有） |
| 调整 F 周报输出格式 / 分节 | `skills/weekly-report/references/output-spec.md`（或对应 spec） + `scripts/hooks/weekly-report-format-check.js` |
| 调整 F 多语言本地化 | `skills/weekly-report/agents/weekly-report-writer.md` + `skills/weekly-report/references/language-spec.md`（如有） |
| 调整 F 邮件投递 | `skills/weekly-report/references/email-spec.md`（如有） + `scripts/send-report-email.py` |

---

## 环境要求

- Claude Code CLI
- Node.js ≥ 18（运行 hook 脚本）
- Python 3（Pipeline C / D / E / F 邮件发送脚本 + Pipeline F 行情采集脚本；仅在使用 `--email` 或 F 时需要）
- pandoc（Pipeline C 和 F 的 docx 导出）
- 能访问外网（供 WebSearch / WebFetch / FRED / yfinance）
- Gmail SMTP 凭据（仅 Pipeline C / D / E / F `--email` 时需要，见 `.env.example`）
- FRED API key / BoE / BoJ 行情接口访问（仅 Pipeline F 需要）

---

## 参考文件

- **README.md** — 面向最终用户的使用文档（安装、示例、自定义）
- **examples/** — 两个完整产出样例（Pipeline A），撰写新功能时可作为格式基准
- **.env.example** — Pipeline C / D / E / F 邮件投递所需的环境变量模板

Agent 链的流程图与工具表请直接看本文件的"六条流水线的 Agent 编排"段，或 README.md 的"How It Works"段 — 不再单独维护 AGENTS.md。
