# sci-research — Codex 项目指引

这是一个 Codex 插件，包含五条专业情报流水线和一项独立 CRD VI 监管转化追踪 skill。以当前 skill、TOML agent 和引用规范为准；不要恢复旧平台的 agent 注册、嵌入式 prompt 或专用社交媒体 MCP 配置。

## 当前架构

| 流水线 | 命令 | 目标 | 输出 |
|---|---|---|---|
| C | $sci-research:daily-news-intelligence | 单国单日新闻情报 | Markdown、可选 docx 与邮件 |
| D | $sci-research:daily-briefing | 多国品牌新闻简报 | SPD Bank 品牌 docx、可选邮件 |
| E | $sci-research:reputation-track | 公司声誉风险监测 | 仅命中负面时生成 HTML 邮件正文 |
| F | $sci-research:china-outbound-opportunity-briefing | 中资企业英国及欧洲商机拓展情报 | Markdown、机构化 docx、可选邮件 |
| G | $sci-research:monthly-news-intelligence | 单国或地区指定月份热点新闻 | 与 Pipeline C 同结构的 Markdown、可选 docx 与邮件 |

独立监管追踪：`$sci-research:crd-vi-transposition` 每周按 Europe/London 固定 ISO 周合并欧盟委员会、EUR-Lex、EY 与成员国官方来源，先比较上次成功快照，再按 `Weekly Changes → Regulatory News & Market Commentary → Country / Current Status / Summary` 输出。新闻层只收录本周材料并单独审计，不能脱离官方后续证据改变国家状态；它不使用自定义 TOML agent，也不属于 C-G 流水线。

所有子 agent 都是带 `sci-research-` 命名空间的原生 Codex TOML 定义，源文件位于 `.codex/agents/*.toml`。Marketplace 更新后先用 `$sci-research:setup-sci-research-runtime` 同步到运行 workspace 的 `.codex/agents/`，并校验项目级 `.codex/config.toml` 中 `web_search = "live"` 与 `agents.max_threads >= 10`，再新开 Codex task。Pipeline C 还要求用户级启用名为 `google_news` 的 MCP，并让新 task 暴露 `mcp__google_news__search_news` 与 `mcp__google_news__get_news_article`；Pipeline C 不再使用 Codex 原生 WebSearch。

- 每个 stage 通过 custom-agent selector 启动其精确命名 role，并使用 `fork_turns="none"`；模型与 model_reasoning_effort 从 TOML 读取。`task_name` 仅是线程标签。
- 每个 stage 的输出和文件交接完成后必须调用 `close_agent`；并行组全部收齐后逐一关闭，失败或 schema 无效的尝试也要先关闭再重试。关闭失败时停止继续 spawn。
- 上游输出原样传给下游 prompt；Pipeline C 只允许文档规定的 Scanner 规范化、Verifier mechanical fallback 和 Manifest fallback。不要改成通用子 agent 或将 agent body 内嵌到 prompt。
- 所有文件创建或修改均使用 apply_patch。不要在 prompt 中要求 Write 或 Edit 工具。

## 模型分配

日常流水线使用 GPT-5.6 的明确变体：Sol（最高质量）、Terra（质量/成本平衡）与 Luna（高吞吐）。`gpt-5.6` 只是 Sol 的 alias，配置中一律写明确 ID；不将慢速 Pro 变体放入固定流水线。

| Agent | 模型 | effort | 取舍 |
|---|---|---:|---|
| sci-research-daily-news-scanner | gpt-5.6-terra | high | 按栏目并行的一句话 Google News MCP 当日搜索；最多两次查询、优先不同事件并封顶 10 条，不为凑数堆叠近似报道 |
| sci-research-news-verifier | gpt-5.6-terra | high | 同事件查重并按直接相关性、具体进展、实质影响和事实清晰度将每栏筛至 3–6 条；不联网、不核验、不路由 |
| sci-research-daily-fact-extractor | gpt-5.6-luna | medium | 从搜索结果摘要抽取结构化值并标记 search-results 证据基础 |
| sci-research-daily-news-writer | gpt-5.6-sol | high | 多语言母语化新闻写作与按需背景补充 |
| sci-research-daily-editor | gpt-5.6-sol | high | 事实、来源、引语、格式与完整母语编辑 |
| sci-research-briefing-curator | gpt-5.6-sol | high | 跨国筛选与品牌化改写 |
| sci-research-reputation-scanner | gpt-5.6-luna | medium | Yahoo 企业/高管确认与非中国大陆媒体、公开社交媒体搜索 |
| sci-research-reputation-verifier | gpt-5.6-terra | high | 声誉相关性、低中高严重度与去重判断 |
| sci-research-reputation-writer | gpt-5.6-terra | medium | 专业风险邮件渲染 |
| sci-research-opportunity-scanner | gpt-5.6-luna | medium | 五条 lane 并行检索英国经济、欧洲出海、跨境并购、投资布局与英国实体线索 |
| sci-research-companies-house-analyst | gpt-5.6-terra | high | 中资归属证据链与英国实体变化研判 |
| sci-research-opportunity-verifier | gpt-5.6-terra | high | 来源、交易阶段、商业重要性、去重与商机评级 |
| sci-research-opportunity-fact-extractor | gpt-5.4-mini | medium | 交易、登记、图片和来源事实清单 |
| sci-research-opportunity-writer | gpt-5.6-sol | high | 中文机构化商机简报写作 |
| sci-research-opportunity-editor | gpt-5.6-sol | high | 事实、阶段、实体身份、商机措辞、引用与版式检查 |
| sci-research-monthly-curator | gpt-5.6-sol | high | 按栏目将现有日报故事聚类为月度事件并提出正选/备选 |
| sci-research-monthly-verifier | gpt-5.6-terra | high | 跨栏目去重、最终路由、证据集与月度故事选择 |
| sci-research-monthly-fact-extractor | gpt-5.4-mini | medium | 从最终证据日报锁定时间线、阶段、事实、引语与引用 |
| sci-research-monthly-writer | gpt-5.6-sol | high | 基于日报证据生成与 Pipeline C 同结构的多语言月报 |
| sci-research-monthly-editor | gpt-5.6-sol | high | 本地证据事实、月度时间线、引用、格式与母语质量检查 |

## 流水线契约

### C — Daily News Intelligence

流程：Scanner × category → 机械汇总 → Verifier → Fact Extractor → Writer × language → Editor × language → pandoc → 可选邮件。

- Scanner 按 active category 一栏一个并行运行；该 fan-out 每份报告只执行一次。Verifier、Fact Extractor 各运行一次；双语模式下 Writer 和 Editor 按语言并行。
- 每个 Scanner 在必需的 runtime path header 后只接收一句搜索任务，由 GPT-5.6 Terra 自行执行一次 `google_news.search_news` 主搜索；仅当直接相关的不同结果不足 3 条时可补搜一次。不得追加来源或正文获取规则。
- Scanner 只用 `mcp__google_news__search_news` 搜索指定日期，清理完全相同的 URL/标准化标题并最多转交 10 条；十条是上限而非配额，明显属于同一人物、行动和进展的近似报道应优先保留信息最完整的一条，宁可少交也不凑数。不确定是否同事件时交给 Verifier。
- Scanner 不做来源等级、正文核验、严格事件级去重、Lead 选择、最终分类或 `china_nexus`/`ipo_ma` 路由；页面被阻挡、付费、仅摘要、动态渲染或暂时打不开仍然保留。
- 编排器按栏目顺序包裹 Scanner 输出并计算汇总计数；超过 10 条时机械封顶，部分或结构不完整时保留所有可解析故事并修正机械字段，完全失败时插入 `unavailable` 零候选占位。单栏的质量、结构或失败状态只记入审计，绝不阻断 Verifier。
- country=China 必须采用外部视角：只查询和使用外国媒体，不查询或使用中国本土媒体及中国政府域名。
- country=Europe 使用 Europe-ex-UK 搜索范围：排除以英国为唯一或主要对象的结果；英国媒体仍可报道非英国欧洲新闻。
- 非中国报告有 6 个栏目；中国报告在第 5 位增加 china_nexus，并保留 ipo_ma。
- Verifier 不联网、不核验事实日期、不使用媒体等级或数值评分。它先按 Batch 顺序将同事件后续报道标记为 `DROP_DUPLICATE`，再按直接相关性、具体当日进展、实质影响和事实清晰度在每栏保留 3–6 个事件；超过 6 个的独立事件标记 `DROP_NOT_SELECTED`。Verifier 输出错误或 schema 不完整时不重试、不停止，由编排器按每栏前 6 条生成 `mechanical-fallback` 后继续 Fact Extractor。
- Pipeline C 的候选数量、schema、计数和最终格式检查均为诊断与修正信号，不是中止门槛；Fact Extractor 失败时生成空事实 fallback Manifest，Editor 或格式检查失败时保留 Writer Markdown 并继续可用输出。只有全栏目无任何候选、必需工具不存在或输出路径不可写等客观无内容/基础设施条件才停止受影响输出。
- Scanner Batch 与 Verifier 查重筛选报告必须原样保存到日报目录的 `audit/*.txt`；不要使用 `.md`，避免 Pipeline D 将审计文件当作国家日报。
- Writer 必须遵守 Fact Manifest；Editor 使用 apply_patch 运行五道检查。Writer 与 Editor 的新闻搜索和正文获取只用 `google_news.search_news` / `google_news.get_news_article`，不得回退到 Codex 原生 WebSearch；引用、引号和输出格式规范以 skills/daily-news-intelligence/references/ 为准。
- `get_news_article` 的 `article_id` 只在产生它的 MCP 会话内有效；Writer/Editor 必须按标题和媒体重新搜索并立即取文，不得复用 Scanner ID。英文每篇正文不得少于 250 个词，中文每篇正文不得少于 400 个 Unicode 汉字，不设最高字数。材料不足时先通过 MCP 重新搜索并取 Lead 正文，再按需补充同事件搜索；只能用返回的可引用实质正文达到底线，不得重复、空泛扩写或编造。
- --email-attach none 表示仅发送正文，必须省略 --attach。

### D — Daily Briefing

流程：Pipeline C Markdown → briefing-curator → generate-branded-docx.py → 可选邮件。

- 仅读取 Pipeline C 的 Markdown，不进行网页搜索。
- 使用 requirements.txt 中声明的最新版 python-docx 依赖。运行前只预检；缺少依赖时停止并给出安装命令，绝不在流水线内运行 pip install。
- D 的 source_dir 与 out_dir 分离，避免将品牌 docx 写回 C 的输入目录。

### E — Reputation Track

流程：Scanner → Verifier → Writer → 邮件。

- Scanner 使用 Yahoo Finance 确认企业正式名称、Ticker 和当前高管，然后自由搜索目标日关于企业及高管的非中国大陆媒体报道与公开社交媒体内容。
- 排除中国大陆媒体、中国大陆政府域名和中国大陆社交平台；香港、澳门、台湾及其他国家和地区的媒体可用。Yahoo Finance 只用于身份和高管确认。
- Scanner 不使用来源矩阵、T1–T4、固定查询、平台配额或候选上限，也不判断负面程度或去重。
- Verifier 只保留真实声誉风险，判断 `low`、`medium`、`high`，合并同一事件，并确保社交媒体说法不被写成已确认事实。
- 不使用 `critical`、七类风险 taxonomy、confidence、来源加权、--sources 或 --severity-min。
- `findings: []` 时静默退出，不写 HTML、不发邮件；有结果时 Writer 生成简洁 HTML，必须由受控邮件脚本发送。

### F — China Outbound Opportunity Briefing

流程：Scanner × 5 lanes → Companies House 结构化采集 → Companies House Analyst → Verifier → Fact Extractor → Writer → Editor → 机构化 docx → 可选邮件。

- 五个 Scanner lane 为 `uk_economy`、`outbound_europe`、`cross_border_ma`、`investment_footprint` 与 `companies_house_discovery`，并行运行一次。
- Scanner 负责日期范围、可读正文、权威来源和候选收集；不做最终去重、商机评级或交易阶段裁决。
- Companies House API 采集由 skill 内脚本执行，Agent 只负责中资关系和变化意义判断；不得根据姓名、国籍、地址或拼音相似直接认定中资控股。
- 英国实体使用 `confirmed`、`probable`、`unverified` 三档；未验证实体不得进入最终中资企业表。
- Verifier 负责来源、日期、交易阶段、同事件去重、商机优先级及潜在银行产品判断；不得虚构现有客户关系或已确认需求。
- Writer 必须遵守 Fact Manifest 和固定 Markdown 结构；图片优先使用官方图表或企业官方图片，版权不明时仅链接或写无合规配图。
- Editor 完成事实、交易阶段、Companies House 身份、商机措辞、引用、图片与中文表达检查；导出前运行直接格式门。

### G — Monthly News Intelligence

流程：Pipeline C 最终 Markdown → 确定性月度索引 → Curator × active category → Verifier → Fact Extractor → Writer × language → Editor × language → pandoc → 可选邮件。

- 只读取 `~/.sci-research/reports/daily-news/{YYYY-MM-DD}/` 顶层的 Pipeline C 最终 Markdown；每个日期最多选择同一国家的一种语言版本。不得读取 audit 文本、邮件正文或 docx。
- 全流水线禁止 WebSearch 和打开来源 URL；现有日报正文与逐条 References 是完整证据边界。
- 收集脚本只读运行，严格校验日报 H1、国家派生栏目及故事引用，并输出文件 SHA-256、日期覆盖、缺失日期和结构化故事索引。
- `source_lang=auto` 时按 primary output language → English → Chinese → Japanese 回退，每个日期只取第一份匹配日报，避免双语日报重复计数。
- Curator 按 active category 并行一次，将同一事件的月内进展聚类，默认每栏提出 3 个正选和最多 2 个备选；重复频率本身不是新闻价值。
- Verifier 负责跨栏目同事件去重、最终路由、备选晋级和一至五条代表性证据日报选择；一个 source story ID 不得支持两篇最终月报新闻。
- Fact Extractor 从最终 evidence story IDs 锁定事实、日期、阶段、引语与 URL 并去重；Writer/Editor 不得使用未入选日报或外部知识。
- 最终 H2/H3/正文/逐条 APA References/分隔线与 Pipeline C 相同，只将 H1 和文件名改为月份，并在首个 H2 前保留一条本地化资料覆盖说明。中英文正文底线与 Pipeline C 相同。
- 当前月份允许通过 `as_of` 生成，但必须明确资料截至日；`require_complete_month=true` 时任何应覆盖日期缺少可用日报均停止。
- source index、Curator Bundle、Verifier 报告与 Fact Manifest 保存到月报目录 `audit/`，均不得使用 `.md`。

## 默认目录

| 用途 | 默认路径 |
|---|---|
| C 日报 | ~/.sci-research/reports/daily-news/{date}/ |
| D 输入 | ~/.sci-research/reports/daily-news/{date}/ |
| D 输出 | ~/.sci-research/reports/daily-briefings/{date}/ |
| E 声誉报告 | ~/.sci-research/reports/reputation/{date}/ |
| F 商机简报 | ~/.sci-research/reports/china-opportunity-briefings/{date_to}/ |
| G 月度热点新闻 | ~/.sci-research/reports/monthly-news/{month}/ |

- 输出目录可被相应的 --out-dir 或 --source-dir 覆盖。

## 邮件、依赖与安全

- 所有邮件一律通过受控脚本：C/E/F/G 使用 scripts/send-report-email.py，D 使用 skills/daily-briefing/scripts/send-briefing-email.py。
- 不要内嵌 smtplib、sendmail 或 mail -s。email-send-guard hook 会阻断这类调用。
- 真实邮件必须由用户明确请求；验证使用 --email-dry-run。
- 安装或更新 D/F 的 docx 依赖：python3 -m pip install --user --upgrade -r requirements.txt。不要自动修改用户 Python 环境。

## 质量钩子

| Hook | 触发 | 作用 |
|---|---|---|
| daily-news-format-check | PostToolUse: apply_patch + 交付前直接检查 | 编辑后和交付前报告格式问题；Pipeline C 记录 `FORMAT_WARNING` 后仍继续导出已有内容 |
| monthly-news-format-check | PostToolUse: apply_patch + 交付前直接检查 | 复用 C 的故事/引用/长度规则，并检查月度 H1、资料覆盖说明和国家派生栏目顺序 |
| opportunity-briefing-format-check | PostToolUse: apply_patch + 交付前直接检查 | 检查 F 的章节、表格、逐条摘要/影响/商机/关注、Companies House 字段、图片与免责声明 |
| email-send-guard | PreToolUse: Bash | 阻断绕过受控邮件脚本的内联 SMTP |

变更 hook 后运行 node --check scripts/hooks/*.js。变更 TOML 后用 tomllib 解析全部 .codex/agents/*.toml；所有改动都必须通过 git diff --check。

## 目录导航

| 需求 | 真源文件 |
|---|---|
| C 编排、参数、输出与邮件 | skills/daily-news-intelligence/SKILL.md |
| C Scanner 极简 Google News MCP 搜索提示 | .codex/agents/sci-research-daily-news-scanner.toml |
| C 一句话栏目方向与编排 | skills/daily-news-intelligence/SKILL.md |
| C Scanner 封顶、Verifier 查重筛选 schema 与中欧范围规则 | skills/daily-news-intelligence/references/schemas.md、skills/daily-news-intelligence/references/rubric.md |
| C agent 行为 | .codex/agents/sci-research-daily-*.toml、.codex/agents/sci-research-news-verifier.toml |
| D 编排与参数 | skills/daily-briefing/SKILL.md |
| D docx 模板与生成器 | skills/daily-briefing/template/、skills/daily-briefing/scripts/generate-branded-docx.py |
| E 编排与来源规则 | skills/reputation-track/SKILL.md、skills/reputation-track/references/ |
| E agent 行为 | .codex/agents/sci-research-reputation-*.toml |
| F 编排、参数、输出与邮件 | skills/china-outbound-opportunity-briefing/SKILL.md |
| F 选择、Companies House、图片与输出规范 | skills/china-outbound-opportunity-briefing/references/ |
| F agent 行为 | .codex/agents/sci-research-opportunity-*.toml、.codex/agents/sci-research-companies-house-analyst.toml |
| F Companies House 与 docx 脚本 | skills/china-outbound-opportunity-briefing/scripts/ |
| G 编排、参数、输出与邮件 | skills/monthly-news-intelligence/SKILL.md |
| G 月度选择、schema、输出与验证规范 | skills/monthly-news-intelligence/references/ |
| G 日报只读索引脚本 | skills/monthly-news-intelligence/scripts/collect-monthly-reports.py |
| G agent 行为 | .codex/agents/sci-research-monthly-*.toml |
| CRD VI 周度编排、状态、日期、新闻方法与来源登记 | skills/crd-vi-transposition/SKILL.md、skills/crd-vi-transposition/references/ |
| CRD VI 周期、搜索队列、快照差异、国家表与新闻验证 | skills/crd-vi-transposition/scripts/weekly-period.py、skills/crd-vi-transposition/scripts/build-weekly-search-plan.py、skills/crd-vi-transposition/scripts/diff-weekly-state.py、skills/crd-vi-transposition/scripts/validate-country-table.py、skills/crd-vi-transposition/scripts/validate-news-section.py |
| Runtime 安装与检查 | skills/setup-sci-research-runtime/、skills/setup-sci-research-runtime/runtime/config.toml、scripts/codex/check-plugin-bundle.py |
| 插件清单与市场条目 | .codex-plugin/plugin.json、.agents/plugins/marketplace.json |

## 验证顺序

1. 静态检查：TOML、JSON、Python、Node、Bash 语法与 git diff --check。
2. Runtime 验证：在隔离 workspace 安装、检查、升级、配置冲突与卸载；确认 `web_search = "live"`、`agents.max_threads >= 10` 与用户级 `google_news` MCP 已启用，并在新 task 逐一验证两个 MCP 工具、命名 agent selector、模型、effort 与 close-agent 生命周期。
3. C 最小首跑：无邮件，确认 Scanner 只调用 `search_news`、Writer/Editor 只用 `search_news` + `get_news_article`、无原生 WebSearch 回退，以及原生 agent 串联、apply_patch、hook、直接格式门与 pandoc 输出。
4. D 验证：先安装 requirements.txt，使用 C 产出的样例 Markdown，邮件只做 dry-run。
5. E 验证：测试 Yahoo 企业/高管确认、非中国大陆媒体与公开社交媒体搜索、低中高判断、干净结果静默退出与邮件 dry-run。
6. F 验证：测试五 lane 并行、Companies House 有/无 API key、watchlist 与 snapshot diff、confirmed/probable/unverified、格式门、图片回退、docx 渲染和邮件 dry-run。
7. G 验证：用完整月和当前不完整月测试单日单语言选择、缺失日期、6/7 栏目 Curator 并行、跨栏目去重、Fact Manifest、双语一致性、月报格式门、docx 与邮件 dry-run。
8. CRD VI 验证：测试固定周一至周日周期与回补、27国来源登记、基线/状态变化/来源失败/禁止无理由倒退、27国全表、成员国子集、欧委会与成员国官方进度冲突、来源更新时间早于核查日、本周新闻日期与事件去重、新闻/状态证据隔离，以及国家表/当前快照/周度差异/新闻四重格式门。

当前 C/D/E 只完成了静态与安装打包验证，真实端到端首跑仍待执行；F 已完成静态检查、Companies House 脚本测试、格式门和样例 docx 视觉验证，原生 agent 联网首跑仍待执行；G 已完成静态与安装打包验证、日报收集脚本真实样本检查及格式门单元测试，原生 agent 离线首跑仍待执行；CRD VI 已完成静态、周周期/来源登记/快照差异/新闻层/四重格式门单元测试、marketplace 集成及德国/法国/荷兰三国独立联网前向测试，含新闻层的 27 国周度联网首跑仍待执行。
