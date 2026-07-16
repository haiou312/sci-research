# sci-research — Codex 项目指引

这是一个 Codex 插件，包含三条彼此独立的新闻情报流水线。以当前 skill、TOML agent 和引用规范为准；不要恢复旧平台的 agent 注册、嵌入式 prompt 或专用社交媒体 MCP 配置。

## 当前架构

| 流水线 | 命令 | 目标 | 输出 |
|---|---|---|---|
| C | $sci-research:daily-news-intelligence | 单国单日新闻情报 | Markdown、可选 docx 与邮件 |
| D | $sci-research:daily-briefing | 多国品牌新闻简报 | SPD Bank 品牌 docx、可选邮件 |
| E | $sci-research:reputation-track | 公司声誉风险监测 | 仅命中负面时生成 HTML 邮件正文 |

所有子 agent 都是带 `sci-research-` 命名空间的原生 Codex TOML 定义，源文件位于 `.codex/agents/*.toml`。Marketplace 更新后先用 `$sci-research:setup-sci-research-runtime` 同步到运行 workspace 的 `.codex/agents/`，再新开 Codex task。

- 每个 stage 通过 custom-agent selector 启动其精确命名 role，并使用 `fork_turns="none"`；模型与 model_reasoning_effort 从 TOML 读取。`task_name` 仅是线程标签。
- 上游输出原样传给下游 prompt；不要改成通用子 agent 或将 agent body 内嵌到 prompt。
- 所有文件创建或修改均使用 apply_patch。不要在 prompt 中要求 Write 或 Edit 工具。

## 模型分配

日常流水线使用 GPT-5.6 的明确变体：Sol（最高质量）、Terra（质量/成本平衡）与 Luna（高吞吐）。`gpt-5.6` 只是 Sol 的 alias，配置中一律写明确 ID；不将慢速 Pro 变体放入固定流水线。

| Agent | 模型 | effort | 取舍 |
|---|---|---:|---|
| sci-research-daily-news-scanner | gpt-5.6-luna | medium | 高吞吐检索、日期核验与候选汇总 |
| sci-research-news-verifier | gpt-5.6-terra | high | 来源、影响力与去重规则裁决 |
| sci-research-daily-fact-extractor | gpt-5.4-mini | medium | 结构化事实与引语抽取 |
| sci-research-daily-news-writer | gpt-5.6-sol | high | 多语言新闻写作与背景整合 |
| sci-research-daily-editor | gpt-5.6-sol | high | 事实、引语、引用与局部修订 |
| sci-research-briefing-curator | gpt-5.6-sol | high | 跨国筛选与品牌化改写 |
| sci-research-reputation-scanner | gpt-5.6-luna | medium | Yahoo 企业/高管确认与非中国大陆媒体、公开社交媒体搜索 |
| sci-research-reputation-verifier | gpt-5.6-terra | high | 声誉相关性、低中高严重度与去重判断 |
| sci-research-reputation-writer | gpt-5.6-terra | medium | 专业风险邮件渲染 |

## 流水线契约

### C — Daily News Intelligence

流程：Scanner → Verifier → Fact Extractor → Writer × language → Editor × language → pandoc → 可选邮件。

- Scanner、Verifier、Fact Extractor 只运行一次；双语模式下 Writer 和 Editor 按语言并行。
- Scanner 使用简短、高自由度提示：每个栏目只给一句大致搜索方向，由 GPT-5.6 Luna 自行决定查询、媒体、语言、深度和跟进路径。
- Scanner 只执行这些硬门槛：日期必须精确等于目标日；来源必须是权威媒体；页面必须有可读事实正文；付费或仅摘要线索必须找到权威免费同事件报道，否则删除；不得编造。
- Scanner 不做新闻价值评分、交易或影响门槛、候选配额、去重、Lead 选择、最终分类或 `china_nexus`/`ipo_ma` 路由；每个合格 URL 独立交给 Verifier。
- country=China 必须采用外部视角：只查询和使用外国媒体，不查询或使用中国本土媒体及中国政府域名。
- country=Europe 使用 Europe-ex-UK 地域契约：英国为唯一或主要地域主体的事件必须排除，且该门槛不得被 Coverage Review 放宽；英国媒体仍可作为欧洲新闻来源，英国仅作为背景或外部交易对手时不自动排除。
- 非中国报告有 6 个栏目；中国报告在第 5 位增加 china_nexus，并保留 ipo_ma。
- Verifier 独立判断来源可信度、新闻价值和具体新事实，并负责 Lead 选择、同事件去重、最终栏目路由、`china_nexus`/`ipo_ma` 资格及 Coverage Review。
- Scanner Bundle 与 Verifier KEEP/DROP 报告必须原样保存到日报目录的 `audit/*.txt`；不要使用 `.md`，避免 Pipeline D 将审计文件当作国家日报。
- Writer 必须遵守 Fact Manifest；Editor 使用 apply_patch 运行五道检查。引用、引号和输出格式规范以 skills/daily-news-intelligence/references/ 为准。
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

## 默认目录

| 用途 | 默认路径 |
|---|---|
| C 日报 | ~/.sci-research/reports/daily-news/{date}/ |
| D 输入 | ~/.sci-research/reports/daily-news/{date}/ |
| D 输出 | ~/.sci-research/reports/daily-briefings/{date}/ |
| E 声誉报告 | ~/.sci-research/reports/reputation/{date}/ |

- 输出目录可被相应的 --out-dir 或 --source-dir 覆盖。

## 邮件、依赖与安全

- 所有邮件一律通过受控脚本：C/E 使用 scripts/send-report-email.py，D 使用 skills/daily-briefing/scripts/send-briefing-email.py。
- 不要内嵌 smtplib、sendmail 或 mail -s。email-send-guard hook 会阻断这类调用。
- 真实邮件必须由用户明确请求；验证使用 --email-dry-run。
- 安装或更新 D 依赖：python3 -m pip install --user --upgrade -r requirements.txt。不要自动修改用户 Python 环境。

## 质量钩子

| Hook | 触发 | 作用 |
|---|---|---|
| daily-news-format-check | PostToolUse: apply_patch + 交付前直接检查 | 编辑后反馈格式错误；直接 `--file` 检查阻断不合格 Markdown 的导出和邮件 |
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
| Runtime 安装与检查 | skills/setup-sci-research-runtime/、scripts/codex/check-plugin-bundle.py |
| 插件清单与市场条目 | .codex-plugin/plugin.json、.agents/plugins/marketplace.json |

## 验证顺序

1. 静态检查：TOML、JSON、Python、Node、Bash 语法与 git diff --check。
2. Runtime 验证：在隔离 workspace 安装、检查、升级、冲突与卸载；新 task 逐一验证命名 agent selector、模型与 effort。
3. C 最小首跑：无邮件，确认原生 agent 串联、apply_patch、hook、直接格式门与 pandoc 输出。
4. D 验证：先安装 requirements.txt，使用 C 产出的样例 Markdown，邮件只做 dry-run。
5. E 验证：测试 Yahoo 企业/高管确认、非中国大陆媒体与公开社交媒体搜索、低中高判断、干净结果静默退出与邮件 dry-run。

当前只完成了静态与安装打包验证；三条流水线的真实端到端首跑仍待执行。
