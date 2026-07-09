# sci-research — Codex 项目指引

这是一个 Codex 插件，包含三条彼此独立的新闻情报流水线。以当前 skill、TOML agent 和引用规范为准；不要恢复旧平台的 agent 注册、嵌入式 prompt 或专用社交媒体 MCP 配置。

## 当前架构

| 流水线 | 命令 | 目标 | 输出 |
|---|---|---|---|
| C | /daily-news-intelligence | 单国单日新闻情报 | Markdown、可选 docx 与邮件 |
| D | /daily-briefing | 多国品牌新闻简报 | SPD Bank 品牌 docx、可选邮件 |
| E | /reputation-track | 公司声誉风险监测 | 仅命中负面时生成 HTML 邮件正文 |

所有子 agent 都是原生 Codex TOML 定义，位于 .codex/agents/*.toml。

- 每个 stage 由其命名 TOML agent 启动；模型与 model_reasoning_effort 从 TOML 读取。
- 上游输出原样传给下游 prompt；不要改成通用子 agent 或将 agent body 内嵌到 prompt。
- 所有文件创建或修改均使用 apply_patch。不要在 prompt 中要求 Write 或 Edit 工具。

## 流水线契约

### C — Daily News Intelligence

流程：Scanner → Verifier → Fact Extractor → Writer × language → Editor × language → pandoc → 可选邮件。

- Scanner、Verifier、Fact Extractor 只运行一次；双语模式下 Writer 和 Editor 按语言并行。
- country=China 必须采用外部视角：不查询中国本土媒体或中国政府域名。权威来源、拒绝列表和日期门见 .codex/agents/daily-news-scanner.toml 与 skills/daily-news-intelligence/references/rubric.md。
- 非中国报告有 6 个栏目；中国报告在第 5 位增加 china_nexus，并保留 ipo_ma。
- Writer 必须遵守 Fact Manifest；Editor 使用 apply_patch 运行五道检查。引用、引号和输出格式规范以 skills/daily-news-intelligence/references/ 为准。
- --email-attach none 表示仅发送正文，必须省略 --attach。

### D — Daily Briefing

流程：Pipeline C Markdown → briefing-curator → generate-branded-docx.py → 可选邮件。

- 仅读取 Pipeline C 的 Markdown，不进行网页搜索。
- 使用 requirements.txt 中固定的 python-docx 依赖。运行前只预检；缺少依赖时停止并给出安装命令，绝不在流水线内运行 pip install。
- D 的 source_dir 与 out_dir 分离，避免将品牌 docx 写回 C 的输入目录。

### E — Reputation Track

流程：Resolver → Scanner × requested sources → Classifier → Writer → 可选邮件。

- News 使用 T1–T4；Reddit 与 X 使用 WebSearch 发现、WebFetch 核验公开且可抓取的原帖或线程。
- 不使用 MCP、平台 API、浏览器自动化或直接抓取。未被索引、需登录、无法抓取或无法核验日期的社交内容必须记录为 coverage gap。
- --sources 是 news,reddit,x 的非空子集；仅启动被请求的 Scanner。
- total_items_kept == 0 时静默退出，不写 HTML、不发邮件。

## 默认目录与发布

| 用途 | 默认路径 |
|---|---|
| C 日报 | ~/.sci-research/reports/daily-news/{date}/ |
| D 输入 | ~/.sci-research/reports/daily-news/{date}/ |
| D 输出 | ~/.sci-research/reports/daily-briefings/{date}/ |
| E 声誉报告 | ~/.sci-research/reports/reputation/{date}/ |

- 输出目录可被相应的 --out-dir 或 --source-dir 覆盖。
- GitHub Pages 发布默认关闭。只有显式传入 --publish --publish-repo <git-path> 时，C 或 D 才调用 scripts/publish-reports.sh。
- 发布脚本要求 REPORTS_REPO 与一个以 ISO 日期命名的 --source-dir；只暂存该日期目录。测试中不得执行真实发布。

## 邮件、依赖与安全

- 所有邮件一律通过受控脚本：C/E 使用 scripts/send-report-email.py，D 使用 skills/daily-briefing/scripts/send-briefing-email.py。
- 不要内嵌 smtplib、sendmail 或 mail -s。email-send-guard hook 会阻断这类调用。
- 真实邮件必须由用户明确请求；验证使用 --email-dry-run。
- 安装 D 依赖：python3 -m pip install --user -r requirements.txt。不要自动修改用户 Python 环境。

## 质量钩子

| Hook | 触发 | 作用 |
|---|---|---|
| daily-news-format-check | PostToolUse: apply_patch | 阻断 C 的 Markdown 栏目、引用、URL 和引号规范错误 |
| email-send-guard | PreToolUse: Bash | 阻断绕过受控邮件脚本的内联 SMTP |

变更 hook 后运行 node --check scripts/hooks/*.js。变更 TOML 后用 tomllib 解析全部 .codex/agents/*.toml；所有改动都必须通过 git diff --check。

## 目录导航

| 需求 | 真源文件 |
|---|---|
| C 编排、参数、输出与邮件 | skills/daily-news-intelligence/SKILL.md |
| C 来源、栏目、日期和 fallback 规则 | skills/daily-news-intelligence/references/rubric.md |
| C agent 行为 | .codex/agents/daily-news-*.toml、.codex/agents/news-verifier.toml |
| D 编排与参数 | skills/daily-briefing/SKILL.md |
| D docx 模板与生成器 | skills/daily-briefing/template/、skills/daily-briefing/scripts/generate-branded-docx.py |
| E 编排与来源规则 | skills/reputation-track/SKILL.md、skills/reputation-track/references/ |
| E agent 行为 | .codex/agents/reputation-*.toml |
| 插件清单与市场条目 | .codex-plugin/plugin.json、.agents/plugins/marketplace.json |

## 验证顺序

1. 静态检查：TOML、JSON、Python、Node、Bash 语法与 git diff --check。
2. C 最小首跑：无邮件、无发布，确认原生 agent 发现与串联、apply_patch、hook 和 pandoc 输出。
3. D 验证：先安装 requirements.txt，使用 C 产出的样例 Markdown，邮件只做 dry-run。
4. E 验证：测试 News、Reddit、X 的 WebSearch/WebFetch 路径、干净结果静默退出与邮件 dry-run。

当前只完成了静态与安装打包验证；三条流水线的真实端到端首跑仍待执行。
