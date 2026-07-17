# sci-research — Codex 项目指引

这是一个 Codex 插件，包含四条专业情报流水线。以当前 skill、TOML agent 和引用规范为准；不要恢复旧平台的 agent 注册、嵌入式 prompt 或专用社交媒体 MCP 配置。

## 当前架构

| 流水线 | 命令 | 目标 | 输出 |
|---|---|---|---|
| C | $sci-research:daily-news-intelligence | 单国单日新闻情报 | Markdown、可选 docx 与邮件 |
| D | $sci-research:daily-briefing | 多国品牌新闻简报 | SPD Bank 品牌 docx、可选邮件 |
| E | $sci-research:reputation-track | 公司声誉风险监测 | 仅命中负面时生成 HTML 邮件正文 |
| F | $sci-research:china-outbound-opportunity-briefing | 中资企业英国及欧洲商机拓展情报 | Markdown、机构化 docx、可选邮件 |

所有子 agent 都是带 `sci-research-` 命名空间的原生 Codex TOML 定义，源文件位于 `.codex/agents/*.toml`。Marketplace 更新后先用 `$sci-research:setup-sci-research-runtime` 同步到运行 workspace 的 `.codex/agents/`，并校验项目级 `.codex/config.toml` 中 `agents.max_threads >= 10`，再新开 Codex task。

- 每个 stage 通过 custom-agent selector 启动其精确命名 role，并使用 `fork_turns="none"`；模型与 model_reasoning_effort 从 TOML 读取。`task_name` 仅是线程标签。
- 每个 stage 的输出和文件交接完成后必须调用 `close_agent`；并行组全部收齐后逐一关闭，失败或 schema 无效的尝试也要先关闭再重试。关闭失败时停止继续 spawn。
- 上游输出原样传给下游 prompt；不要改成通用子 agent 或将 agent body 内嵌到 prompt。
- 所有文件创建或修改均使用 apply_patch。不要在 prompt 中要求 Write 或 Edit 工具。

## 模型分配

日常流水线使用 GPT-5.6 的明确变体：Sol（最高质量）、Terra（质量/成本平衡）与 Luna（高吞吐）。`gpt-5.6` 只是 Sol 的 alias，配置中一律写明确 ID；不将慢速 Pro 变体放入固定流水线。

| Agent | 模型 | effort | 取舍 |
|---|---|---:|---|
| sci-research-daily-news-scanner | gpt-5.6-luna | medium | 按栏目并行的高吞吐检索、日期核验与候选收集 |
| sci-research-news-verifier | gpt-5.6-terra | high | 来源、影响力与去重规则裁决 |
| sci-research-daily-fact-extractor | gpt-5.4-mini | medium | 结构化事实与引语抽取 |
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

## 流水线契约

### C — Daily News Intelligence

流程：Scanner × category → 机械汇总 → Verifier → Fact Extractor → Writer × language → Editor × language → pandoc → 可选邮件。

- Scanner 按 active category 一栏一个并行运行；该 fan-out 每份报告只执行一次。Verifier、Fact Extractor 各运行一次；双语模式下 Writer 和 Editor 按语言并行。
- 每个 Scanner 使用简短、高自由度提示，只接收一个栏目及其一句大致搜索方向，由 GPT-5.6 Luna 自行决定查询、媒体、语言、深度和跟进路径。
- Scanner 只执行这些硬门槛：日期必须精确等于目标日；来源必须是权威媒体；页面必须有可读事实正文；付费或仅摘要线索必须找到权威免费同事件报道，否则删除；不得编造。
- Scanner 不做新闻价值评分、交易或影响门槛、候选配额、去重、Lead 选择、最终分类或 `china_nexus`/`ipo_ma` 路由；每个合格 URL 独立交给 Verifier。
- 编排器只按栏目顺序原样包裹各 Scanner 输出并计算汇总计数，不新增 Merger agent，不改写、去重或路由候选；这些判断仍由 Verifier 完成。
- country=China 必须采用外部视角：只查询和使用外国媒体，不查询或使用中国本土媒体及中国政府域名。
- country=Europe 使用 Europe-ex-UK 地域契约：英国为唯一或主要地域主体的事件必须排除，且该门槛不得被 Coverage Review 放宽；英国媒体仍可作为欧洲新闻来源，英国仅作为背景或外部交易对手时不自动排除。
- 非中国报告有 6 个栏目；中国报告在第 5 位增加 china_nexus，并保留 ipo_ma。
- Verifier 独立判断来源可信度、新闻价值和具体新事实，并负责 Lead 选择、同事件去重、最终栏目路由、`china_nexus`/`ipo_ma` 资格及 Coverage Review。
- Scanner Batch（含每栏原始输出及 search/open_page 计数）与 Verifier KEEP/DROP 报告必须原样保存到日报目录的 `audit/*.txt`；不要使用 `.md`，避免 Pipeline D 将审计文件当作国家日报。
- Writer 必须遵守 Fact Manifest；Editor 使用 apply_patch 运行五道检查。引用、引号和输出格式规范以 skills/daily-news-intelligence/references/ 为准。
- 英文每篇正文不得少于 250 个词，中文每篇正文不得少于 400 个 Unicode 汉字，不设最高字数。材料不足时先打开 Lead 和相关佐证原文，再按需补充搜索；只能用可引用的实质内容达到底线，不得重复、空泛扩写或编造。
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

## 默认目录

| 用途 | 默认路径 |
|---|---|
| C 日报 | ~/.sci-research/reports/daily-news/{date}/ |
| D 输入 | ~/.sci-research/reports/daily-news/{date}/ |
| D 输出 | ~/.sci-research/reports/daily-briefings/{date}/ |
| E 声誉报告 | ~/.sci-research/reports/reputation/{date}/ |
| F 商机简报 | ~/.sci-research/reports/china-opportunity-briefings/{date_to}/ |

- 输出目录可被相应的 --out-dir 或 --source-dir 覆盖。

## 邮件、依赖与安全

- 所有邮件一律通过受控脚本：C/E/F 使用 scripts/send-report-email.py，D 使用 skills/daily-briefing/scripts/send-briefing-email.py。
- 不要内嵌 smtplib、sendmail 或 mail -s。email-send-guard hook 会阻断这类调用。
- 真实邮件必须由用户明确请求；验证使用 --email-dry-run。
- 安装或更新 D/F 的 docx 依赖：python3 -m pip install --user --upgrade -r requirements.txt。不要自动修改用户 Python 环境。

## 质量钩子

| Hook | 触发 | 作用 |
|---|---|---|
| daily-news-format-check | PostToolUse: apply_patch + 交付前直接检查 | 编辑后反馈格式错误；直接 `--file` 检查阻断不合格 Markdown 的导出和邮件 |
| opportunity-briefing-format-check | PostToolUse: apply_patch + 交付前直接检查 | 检查 F 的章节、表格、逐条摘要/影响/商机/关注、Companies House 字段、图片与免责声明 |
| email-send-guard | PreToolUse: Bash | 阻断绕过受控邮件脚本的内联 SMTP |

变更 hook 后运行 node --check scripts/hooks/*.js。变更 TOML 后用 tomllib 解析全部 .codex/agents/*.toml；所有改动都必须通过 git diff --check。

## 目录导航

| 需求 | 真源文件 |
|---|---|
| C 编排、参数、输出与邮件 | skills/daily-news-intelligence/SKILL.md |
| C Scanner 硬门槛与一句话栏目方向 | .codex/agents/sci-research-daily-news-scanner.toml |
| C Verifier 来源、新闻价值、去重、路由和 Coverage Review 规则 | skills/daily-news-intelligence/references/rubric.md |
| C agent 行为 | .codex/agents/sci-research-daily-*.toml、.codex/agents/sci-research-news-verifier.toml |
| D 编排与参数 | skills/daily-briefing/SKILL.md |
| D docx 模板与生成器 | skills/daily-briefing/template/、skills/daily-briefing/scripts/generate-branded-docx.py |
| E 编排与来源规则 | skills/reputation-track/SKILL.md、skills/reputation-track/references/ |
| E agent 行为 | .codex/agents/sci-research-reputation-*.toml |
| F 编排、参数、输出与邮件 | skills/china-outbound-opportunity-briefing/SKILL.md |
| F 选择、Companies House、图片与输出规范 | skills/china-outbound-opportunity-briefing/references/ |
| F agent 行为 | .codex/agents/sci-research-opportunity-*.toml、.codex/agents/sci-research-companies-house-analyst.toml |
| F Companies House 与 docx 脚本 | skills/china-outbound-opportunity-briefing/scripts/ |
| Runtime 安装与检查 | skills/setup-sci-research-runtime/、skills/setup-sci-research-runtime/runtime/config.toml、scripts/codex/check-plugin-bundle.py |
| 插件清单与市场条目 | .codex-plugin/plugin.json、.agents/plugins/marketplace.json |

## 验证顺序

1. 静态检查：TOML、JSON、Python、Node、Bash 语法与 git diff --check。
2. Runtime 验证：在隔离 workspace 安装、检查、升级、配置冲突与卸载；确认 `agents.max_threads >= 10`，并在新 task 逐一验证命名 agent selector、模型、effort 与 close-agent 生命周期。
3. C 最小首跑：无邮件，确认原生 agent 串联、apply_patch、hook、直接格式门与 pandoc 输出。
4. D 验证：先安装 requirements.txt，使用 C 产出的样例 Markdown，邮件只做 dry-run。
5. E 验证：测试 Yahoo 企业/高管确认、非中国大陆媒体与公开社交媒体搜索、低中高判断、干净结果静默退出与邮件 dry-run。
6. F 验证：测试五 lane 并行、Companies House 有/无 API key、watchlist 与 snapshot diff、confirmed/probable/unverified、格式门、图片回退、docx 渲染和邮件 dry-run。

当前 C/D/E 只完成了静态与安装打包验证，真实端到端首跑仍待执行；F 已完成静态检查、Companies House 脚本测试、格式门和样例 docx 视觉验证，原生 agent 联网首跑仍待执行。
