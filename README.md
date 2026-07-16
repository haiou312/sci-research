# sci-research

> A **Codex plugin** with **three independent multi-agent pipelines** for daily news intelligence, branded briefings, and company reputation monitoring.

Given a country, a company, or a date, this plugin orchestrates specialised agents to produce a polished, sourced deliverable — daily news briefing, branded Word document, or reputational risk email.

*(The plugin name is a historical artifact — the original `/sci-research` deep-research pipeline has been removed; the name is kept for marketplace identity and install-path stability.)*

---

## Three Pipelines

| | `$sci-research:daily-news-intelligence` | `$sci-research:daily-briefing` | `$sci-research:reputation-track` |
|---|---|---|---|
| **Purpose** | Single-country daily news briefing | Multi-country branded briefing (SPD Bank) | Company reputation risk monitor |
| **Time focus** | Single date | Single date (reads existing reports) | Single date |
| **Sources** | Authoritative media with exact-date and readable-body verification | Country reports from Pipeline C | News (T1-T4) + Reddit + X |
| **Output** | 6/7-section Markdown + docx (+email); mono- or bilingual | 13-15-story branded Word document (+email) | Inline HTML email (only when negative) |
| **Default lang** | `zh` | `zh` | `zh` |
| **Languages** | zh / en / ja + 6 bilingual combos (`zh+en` …) | zh / en | zh / en |

All three pipelines are **completely independent** — they don't share agents and changes to one don't affect the others.

Pipeline C also writes raw Scanner and Verifier audit artifacts under `daily-news/{date}/audit/` as `.txt` files. They show the Scanner candidate pool and coverage notes, then the Verifier's source assessment, KEEP/DROP reasons, Coverage Review decisions, and remaining gaps; Pipeline D ignores them because it reads report Markdown rather than audit text files.

---

## Why This Plugin

- **10 specialised agents** across three pipelines, each agent narrowly scoped
- **High-freedom Luna Scanner** — one short direction per category, with no outlet list, source tier, candidate quota, impact threshold, deduplication, or routing logic
- **Per-URL date verification** in `$sci-research:daily-news-intelligence` — neighbouring days are discarded
- **Readable free reporting** — paid or stub-only leads are replaced with an authoritative free same-event article or excluded
- **Editorial second-pass filter** (`sci-research-news-verifier`) for daily news — evidence fit / new information / contextual news value / originality / dedup
- **Fact Manifest + 5-pass Editor** — numbers / names / dates / quotes locked to a verbatim YAML manifest, then fact-checked and style-repaired post-Writer
- **External-view China gate** — `$sci-research:daily-news-intelligence --country "China"` uses foreign media only and excludes Chinese-domestic outlets and Chinese government domains
- **Free-prose Writer** — daily news Writer composes explanatory prose in the target language, not a mechanical translation
- **Bilingual mode (1.18.0+)** — `--lang zh+en` runs upstream once, fans Writer/Editor out per language in parallel, ships one email with a stacked bilingual body + up to 4 attachments
- **Branded Word output** via SPD Bank template (`$sci-research:daily-briefing`)
- **Gmail SMTP email delivery** built into all three pipelines
- **Quality hooks** enforce daily-news Markdown format and email-send safety
- **Multilingual** — Chinese / English / Japanese output

---

## Deployment

Sci-Research has two deployment layers:

1. The Codex marketplace installs the plugin skills and hooks.
2. The runtime setup skill copies the plugin's 10 namespaced TOML agents into the project where the pipelines will run.

Marketplace installation alone is therefore not sufficient. Complete every step below before the first pipeline run.

### First-Time Installation From GitHub

#### Step 1 — Check the required executables

```bash
codex --version
python3 --version
node --version
```

These three commands must succeed. Node.js is required by the quality hooks. Python is required by the runtime setup, email scripts, and Pipeline D.

Check the optional Pipeline C docx exporter separately:

```bash
pandoc --version
```

If `pandoc` is unavailable, Pipeline C can still produce Markdown but skips docx export.

#### Step 2 — Add the Git marketplace

Run this once:

```bash
codex plugin marketplace add haiou312/sci-research --ref main
codex plugin marketplace list
```

Confirm that the list contains `sci-research-marketplace`. The marketplace name comes from `.agents/plugins/marketplace.json`; it is not the GitHub repository name.

#### Step 3 — Install the plugin from that marketplace

```bash
codex plugin add sci-research@sci-research-marketplace
codex plugin list
```

Confirm that `sci-research@sci-research-marketplace` is shown as `installed, enabled`. Record the displayed version; it should match `.codex-plugin/plugin.json` in the marketplace revision.

#### Step 4 — Create and enter the dedicated runtime workspace

```bash
mkdir -p ~/.sci-research
cd ~/.sci-research
codex
```

For the Codex macOS App, run only `mkdir -p ~/.sci-research`, then open `~/.sci-research` as the workspace in the App instead of running the `codex` CLI command.

The same workspace must be used for runtime setup and pipeline execution. The default report directories also live under `~/.sci-research/reports/`.

#### Step 5 — Install the project-scoped agents from inside Codex

Enter this in the Codex task, not in the shell:

```text
Use $sci-research:setup-sci-research-runtime to install the project-scoped runtime in this workspace.
```

The setup performs a bundle check and dry-run before installing. It creates:

```text
~/.sci-research/.codex/agents/sci-research-*.toml
~/.sci-research/.codex/sci-research-runtime.json
```

It does not modify global `~/.codex/config.toml`, install Python packages, or run a news pipeline. If it reports an unmanaged-file conflict or a locally modified managed agent, resolve the named file instead of overwriting it manually.

#### Step 6 — Review plugin hooks

Inside Codex, open:

```text
/hooks
```

Review and trust the two Sci-Research hooks if Codex asks:

- `email-send-guard` — blocks inline SMTP implementations.
- `daily-news-format-check` — reports invalid Pipeline C Markdown after edits.

#### Step 7 — Start a new Codex task in the same workspace

End the current task, keep `~/.sci-research` as the workspace, and start a new task. Project custom agents are discovered when a task starts; the setup task is not accepted as proof that the new agent registry has loaded.

In the new task, run a runtime-only check:

```text
Use $sci-research:setup-sci-research-runtime to check the project-scoped runtime in this workspace. Do not run a news pipeline.
```

The check must report 10 agents and a matching plugin version before first use.

#### Step 8 — Run a no-email smoke test

Enter this in Codex:

```text
Use $sci-research:daily-news-intelligence --country "Japan" --lang en
```

Do not add `--email` to the first run. Pipeline C uses its default output directory under `~/.sci-research/reports/daily-news/{date}/`.

### Updating an Existing Git Marketplace Installation

An update has three distinct steps: refresh the Git marketplace snapshot, reinstall the plugin cache version, and resync the project agents.

#### Step 1 — Refresh the Git marketplace

```bash
codex plugin marketplace upgrade sci-research-marketplace
```

The correct subcommand is `upgrade`. Codex does not provide `codex plugin update` or `codex plugin marketplace update`.

#### Step 2 — Reinstall the plugin from the refreshed snapshot

```bash
codex plugin add sci-research@sci-research-marketplace
codex plugin list
```

Confirm that the displayed plugin version changed. If it did not, confirm that the pushed `.codex-plugin/plugin.json` has a new `+codex.<cachebuster>` suffix.

#### Step 3 — Update the project-scoped agents

Open `~/.sci-research` in Codex and enter:

```text
Use $sci-research:setup-sci-research-runtime to update and check the project-scoped runtime in this workspace.
```

The updater backs up managed files before replacing them and refuses to overwrite local changes. Review `/hooks` again if Codex requests trust for the updated hook definitions.

#### Step 4 — Start another new task

Start a new Codex task in `~/.sci-research` after every plugin/runtime update. The new task is the boundary where updated skills, hooks, and project agents are all loaded together.

### Local Marketplace Development

Use this instead of the GitHub marketplace flow when testing an unpushed checkout:

```bash
git clone https://github.com/haiou312/sci-research.git
cd sci-research
codex plugin marketplace add "$PWD"
codex plugin add sci-research@sci-research-marketplace
```

After changing the checkout, update the cachebuster in `.codex-plugin/plugin.json`, run `codex plugin add sci-research@sci-research-marketplace` again, then repeat runtime setup in `~/.sci-research`. `marketplace upgrade` refreshes Git marketplaces and is not needed for a local-path marketplace.

### Pipeline D Dependency (optional)

Pipeline D alone requires `python-docx`. If no source checkout exists yet, create one, then install the declared dependency before starting Codex:

```bash
git clone https://github.com/haiou312/sci-research.git /path/to/sci-research
cd /path/to/sci-research
python3 -m pip install --user --upgrade -r requirements.txt
```

Skip the `git clone` command when the checkout already exists. The pipeline only checks the dependency; it never runs `pip install` itself. If using a virtual environment, activate it before launching the Codex CLI so `python3` inside the task resolves to that environment.

### Email Delivery (optional)

The email scripts read exported environment variables; they do not automatically load a repository `.env` file. Add the required values to the shell profile used to launch the Codex CLI:

```bash
export GOOGLE_EMAIL_USERNAME='you@gmail.com'
export GOOGLE_EMAIL_APP_PASSWORD='your-16-character-app-password'
export GOOGLE_EMAIL_FROM_NAME='Your Name'
```

Reload the profile, verify that the required variables are exported, and launch Codex from that shell:

```bash
source ~/.zshrc
[ -n "$GOOGLE_EMAIL_USERNAME" ] && echo "username: set"
[ -n "$GOOGLE_EMAIL_APP_PASSWORD" ] && echo "password: set"
cd ~/.sci-research
codex
```

Never commit real credentials or place them in the marketplace repository. The shell-profile example applies to Codex CLI sessions started from that shell. For the macOS App, the variables must be present in the App process environment; use the CLI for email-enabled runs if they are not. Real email is sent only when explicitly requested. Use `--email-dry-run` for the first email-path test.

---

## Usage

### Pipeline C — `$sci-research:daily-news-intelligence` (Single-Country Daily Briefing)

```
$sci-research:daily-news-intelligence --country "<name>" [--date YYYY-MM-DD] \
  [--lang zh|en|ja|zh+en|en+zh|zh+ja|ja+zh|en+ja|ja+en] \
  [--out-dir <path>] [--min-per-category <N>] \
  [--email <a@x.com,b@y.com>] [--email-attach both|docx|md|none] [--email-dry-run]
```

```text
# Today's UK briefing in Chinese, dry-run the email
$sci-research:daily-news-intelligence --country "United Kingdom" --email you@gmail.com --email-dry-run

# China briefing — external-view by design (eligible external sources only)
$sci-research:daily-news-intelligence --country "China" --date 2026-05-11 --lang zh

# Japanese briefing for Japan, English output
$sci-research:daily-news-intelligence --country "Japan" --lang en

# Bilingual (1.18.0+) — Chinese primary, ships 4 attachments (zh+en md+docx) + stacked zh+en email body
$sci-research:daily-news-intelligence --country "China" --lang zh+en --email boss@company.com
```

**Note on `--country "China"`**: Pipeline C scans China from an outside-observer perspective. The Scanner uses foreign media only; Chinese-domestic outlets and Chinese government domains are **not queried or used**. There is no fixed foreign-outlet list.

### Pipeline D — `$sci-research:daily-briefing` (Multi-Country Branded Word Document)

```
$sci-research:daily-briefing [--date YYYY-MM-DD] [--countries "中国,英国,美国,欧洲,日本,韩国"] [--total 14] \
  [--source-dir <path>] [--out-dir <path>] [--email <a@x.com>] [--email-subject <text>] \
  [--email-dry-run] [--no-wait]
```

Reads existing Pipeline C reports from a directory, curates the most impactful 13-15 stories across countries, and emits a branded Word document via the SPD Bank template.

By default, local output is independent of the plugin install location and any Git checkout:

| Pipeline | Default location |
|---|---|
| C daily news | `~/.sci-research/reports/daily-news/{date}/` |
| D source reports | `~/.sci-research/reports/daily-news/{date}/` |
| D branded briefing | `~/.sci-research/reports/daily-briefings/{date}/` |
| E reputation report | `~/.sci-research/reports/reputation/{date}/` |

```text
# Today's multi-country briefing with default countries and 14 stories
$sci-research:daily-briefing --email you@gmail.com

# Specific date with custom country selection
$sci-research:daily-briefing --date 2026-05-11 --countries "中国,日本,韩国" --total 12
```

### Pipeline E — `$sci-research:reputation-track` (Company Reputation Risk Monitor)

```
$sci-research:reputation-track --company "<name|ticker>" [--date YYYY-MM-DD] [--lang zh|en] \
  [--sources news,reddit,x] [--severity-min low|medium|high] \
  [--email <a@x.com>] [--email-dry-run]
```

Resolves the company + executives, scans News + Reddit + X for adverse content, classifies category and severity. **Silent when clean** — only emails a report if negative findings exist.

```text
# Scan Tesla for today's negative coverage
$sci-research:reputation-track --company "TSLA" --email you@gmail.com

# Scan Alibaba for a specific date, low-severity threshold
$sci-research:reputation-track --company "BABA" --date 2026-05-10 --severity-min low --lang en
```

---

## How It Works

### Pipeline C — `$sci-research:daily-news-intelligence`

```
sci-research-daily-news-scanner → sci-research-news-verifier → sci-research-daily-fact-extractor → sci-research-daily-news-writer → sci-research-daily-editor → pandoc → email (optional)
   (Luna / medium)      (Terra / high)  (5.4 mini / medium)    (Sol / high, ×langs) (Sol / high, ×langs)

Bilingual mode (--lang zh+en …): Scanner/Verifier/Fact-Extractor run ONCE; Writer ×langs in parallel → Editor ×langs in parallel → pandoc ×langs
```

| Agent | Codex configuration | Role |
|---|---|---|
| `sci-research-daily-news-scanner` | gpt-5.6-luna / medium | Single high-freedom agent scanning all active categories sequentially. It follows one short direction per category and only hard-gates exact date, authoritative media, readable body, paid-to-free replacement, China foreign-media-only sourcing, and Europe-ex-UK scope. Every qualifying URL is handed to the Verifier separately |
| `sci-research-news-verifier` | gpt-5.6-terra / high | Editorial second-pass filter: independent source assessment, concrete new information, contextual daily-news value, originality/corroboration, Lead selection, deduplication, final category routing, and Coverage Review for short categories |
| `sci-research-daily-fact-extractor` | gpt-5.4-mini / medium | Extracts every number / name / date / quote from the Verifier KEEP set into a locked-values YAML Fact Manifest (no web access) |
| `sci-research-daily-news-writer` | gpt-5.6-sol / high | Consumes Verifier KEEP set + Fact Manifest, composes explanatory prose in target language with 1-3 background searches per story, emits Markdown + APA refs. One instance per language in bilingual mode |
| `sci-research-daily-editor` | gpt-5.6-sol / high | 5-pass post-Writer editor: manifest-fact drift / search-fact backing / quote verbatim / quote-mark normalization / local fluency repair. `apply_patch`-only. One instance per language in bilingual mode |

### Pipeline D — `$sci-research:daily-briefing`

```
daily-news-reports/YYYY-MM-DD/*.md  (existing country reports)
  │
  └─→ sci-research-briefing-curator → generate-branded-docx.py → send-briefing-email.py
      (Sol / high)          (python-docx)              (Gmail SMTP)
```

`sci-research-briefing-curator` uses gpt-5.6-sol / high.

### Pipeline E — `$sci-research:reputation-track`

```
sci-research-reputation-resolver → sci-research-reputation-scanner × requested sources (parallel; default: news / reddit / x) → sci-research-reputation-classifier → sci-research-reputation-writer → email (only if findings)
   (Terra / high)      (Luna / medium)                                                              (Terra / high)          (Terra / medium)
```

Silent exit when `total_items_kept == 0`. Reddit and X use Codex WebSearch `search` to discover publicly indexed posts and `open_page` to inspect canonical threads. Unindexed, login-gated, or unopenable content is recorded as a coverage gap.

| Agent | Codex configuration |
|---|---|
| `sci-research-reputation-resolver` | gpt-5.6-terra / high |
| `sci-research-reputation-scanner` | gpt-5.6-luna / medium |
| `sci-research-reputation-classifier` | gpt-5.6-terra / high |
| `sci-research-reputation-writer` | gpt-5.6-terra / medium |

---

## Pipeline C Discovery And Verification

The Pipeline C Scanner is intentionally short. GPT-5.6 Luna chooses its own queries, media sources, search languages, search depth, and follow-up paths. Each category receives only one sentence describing the general subject area.

The Scanner applies only these hard rules:

- the article publication date must equal the requested date;
- the source must be authoritative, editorially accountable media;
- the page must expose enough readable article body to verify facts;
- a paid or stub-only lead must be replaced with an authoritative free same-event article;
- China reports use foreign media only;
- Europe reports exclude UK-only and UK-primary events, while UK media may report eligible non-UK European events;
- unverifiable facts, dates, sources, and URLs must never be invented.

The Scanner does not score news value, enforce transaction or impact thresholds, decide final category eligibility, merge duplicate coverage, choose a Lead, or route `china_nexus` and `ipo_ma`. It returns each qualifying URL separately. The Verifier then judges credibility and news value, selects Leads, deduplicates events, performs final category routing, and runs Coverage Review.

Detailed rules:
- Pipeline C Scanner hard rules and category directions: [`.codex/agents/sci-research-daily-news-scanner.toml`](./.codex/agents/sci-research-daily-news-scanner.toml)
- Pipeline C Verifier editorial rules: [`skills/daily-news-intelligence/references/rubric.md`](./skills/daily-news-intelligence/references/rubric.md)
- Pipeline E news tiering: [`skills/reputation-track/references/news-source.md`](./skills/reputation-track/references/news-source.md)

---

## Quality Hooks

| Hook | Pipeline | Trigger | What It Does |
|---|---|---|---|
| `daily-news-format-check` | C | PostToolUse:apply_patch + direct pre-delivery check | Reports format violations after edits; the direct `--file` check hard-stops export/email on count, numbering, URL, quote-mark, or body-length failures |
| `email-send-guard` | C / D / E | PreToolUse:Bash | **Blocks** inline `smtplib` / `MIMEMultipart` / `sendmail` Bash commands that bypass the sanctioned `send-*-email.py` scripts |

---

## Project Structure

```
sci-research/
├── .codex-plugin/
│   └── plugin.json                          # Codex plugin manifest (skills + hooks + interface)
├── .agents/plugins/
│   └── marketplace.json                     # Codex install manifest
├── .codex/agents/                           # Native Codex subagents (TOML — dispatched by the skills)
│   ├── sci-research-daily-news-scanner.toml
│   ├── sci-research-news-verifier.toml
│   ├── sci-research-daily-fact-extractor.toml
│   ├── sci-research-daily-news-writer.toml
│   ├── sci-research-daily-editor.toml
│   ├── sci-research-briefing-curator.toml
│   ├── sci-research-reputation-resolver.toml
│   ├── sci-research-reputation-scanner.toml
│   ├── sci-research-reputation-classifier.toml
│   └── sci-research-reputation-writer.toml
├── skills/                                  # 3 pipelines + project runtime setup
│   ├── daily-news-intelligence/             # Pipeline C
│   │   ├── SKILL.md
│   │   ├── agents/openai.yaml               # skill metadata (display_name, default_prompt)
│   │   └── references/                      # Pipeline C specs
│   │       ├── email-spec.md
│   │       ├── language-spec.md
│   │       ├── output-spec.md
│   │       ├── rubric.md
│   │       ├── schemas.md
│   │       └── verification.md
│   ├── daily-briefing/                      # Pipeline D
│   │   ├── SKILL.md
│   │   ├── agents/openai.yaml
│   │   ├── template/briefing-template.docx  # SPD Bank brand template
│   │   ├── references/email-spec.md
│   │   └── scripts/
│   │       ├── generate-branded-docx.py
│   │       └── send-briefing-email.py
│   ├── reputation-track/                    # Pipeline E
│   │   ├── SKILL.md
│   │   ├── agents/openai.yaml
│   │   └── references/                      # Pipeline E specs
│   │       ├── entity-resolution.md
│   │       ├── source-matrix.md
│   │       ├── news-source.md
│   │       ├── negativity-rubric.md
│   │       ├── html-template.md
│   │       ├── email-spec.md
│   │       └── schemas.md
│   └── setup-sci-research-runtime/           # Installs/checks project-scoped agents
│       ├── SKILL.md
│       └── scripts/sync_runtime.py
├── hooks/hooks.json                         # Plugin lifecycle hook config
├── scripts/
│   ├── codex/check-plugin-bundle.py         # Installed-cache integrity check
│   ├── hooks/                               # Hook implementations (Node.js)
│   │   ├── daily-news-format-check.js
│   │   └── email-send-guard.js
│   └── send-report-email.py                 # Gmail SMTP (Pipelines C / E)
├── tests/
│   ├── test_hooks.py                        # Codex hook protocol tests
│   └── test_runtime_sync.py                 # Isolated setup/update/uninstall tests
├── .env.example                             # Gmail SMTP environment template
├── requirements.txt                         # Pipeline D dependency (latest at install time)
├── AGENTS.md                                # Project guidance for Codex
├── PORTING-NOTES.md                         # Runtime-validation status and open checks
├── README.md
└── LICENSE
```

---

## Customization

| Goal | Edit |
|---|---|
| Pipeline C Scanner hard rules / category directions | `.codex/agents/sci-research-daily-news-scanner.toml` |
| Pipeline C Verifier source / news-value / dedup / routing rules | `skills/daily-news-intelligence/references/rubric.md` + `.codex/agents/sci-research-news-verifier.toml` |
| Pipeline C external-view China rules | `.codex/agents/sci-research-daily-news-scanner.toml` § China report + `skills/daily-news-intelligence/references/rubric.md` § China External-View Gate |
| Pipeline C output format / Markdown contract | `skills/daily-news-intelligence/references/output-spec.md` |
| Pipeline C language localisation / bilingual mode | `skills/daily-news-intelligence/references/language-spec.md` (§ Bilingual Mode) |
| Pipeline C email delivery / bilingual email | `skills/daily-news-intelligence/references/email-spec.md` + `scripts/send-report-email.py` |
| Pipeline D brand template | `skills/daily-briefing/template/briefing-template.docx` |
| Pipeline D curator rules | `.codex/agents/sci-research-briefing-curator.toml` |
| Pipeline E negativity rubric | `skills/reputation-track/references/negativity-rubric.md` |
| Pipeline E news source tiering | `skills/reputation-track/references/news-source.md` |
| Pipeline E HTML email template | `skills/reputation-track/references/html-template.md` |
| Pipeline E entity resolution | `skills/reputation-track/references/entity-resolution.md` + `.codex/agents/sci-research-reputation-resolver.toml` |
| New output language (Pipeline C) | `.codex/agents/sci-research-daily-news-writer.toml` + `skills/daily-news-intelligence/references/language-spec.md` |
| Adding hook / changing email-send guard | `scripts/hooks/email-send-guard.js` + the relevant SKILL.md email step |

---

## Requirements

- [Codex](https://developers.openai.com/codex) CLI
- Node.js ≥ 18 (for hook scripts)
- Python 3 (for email delivery scripts + Pipeline D docx generation; only required when `--email` or Pipeline D is used)
- Pipeline D dependency (install or update from the plugin root): `python3 -m pip install --user --upgrade -r requirements.txt`
- `pandoc` (for Markdown → docx conversion in Pipeline C)
- Internet access (for WebSearch `search` / `open_page`)
- Gmail SMTP credentials (only when `--email` is used; see `.env.example`)
- No separate social-media MCP configuration is required. Pipeline E's Reddit/X coverage is limited to publicly indexed, openable content.

---


## License

MIT
