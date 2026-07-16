# sci-research

> A **Codex plugin** with **four specialised multi-agent workflows** for daily news intelligence, branded briefings, company reputation monitoring, and China-outbound commercial opportunity development.

Given a country, company, date, or reporting window, this plugin orchestrates specialised agents to produce a polished, sourced deliverable: daily news briefing, branded Word document, reputational risk email, or UK/Europe opportunity briefing.

*(The plugin name is a historical artifact — the original `/sci-research` deep-research pipeline has been removed; the name is kept for marketplace identity and install-path stability.)*

---

## Four Pipelines

| Pipeline | Command | Purpose | Output |
|---|---|---|---|
| C | `$sci-research:daily-news-intelligence` | Single-country, exact-date news intelligence | 6/7-section Markdown + docx (+email); mono- or bilingual |
| D | `$sci-research:daily-briefing` | Multi-country branded briefing from Pipeline C | 13-15-story SPD Bank Word document (+email) |
| E | `$sci-research:reputation-track` | Company and current-executive reputation risk monitor | Inline HTML email, only when negative |
| F | `$sci-research:china-outbound-opportunity-briefing` | UK economy, China outbound Europe, cross-border M&A, investment footprints, and Companies House entity changes | Chinese Markdown + institutional Word document (+email) |

The four pipelines use separate agent chains and stage contracts. Pipeline D intentionally consumes Pipeline C report files. Pipeline F performs its own date-range discovery and uses a scoped Companies House API/watchlist monitor; it does not claim exhaustive discovery of every Chinese-backed UK entity.

Pipeline C also writes raw Scanner and Verifier audit artifacts under `daily-news/{date}/audit/` as `.txt` files. They show the Scanner candidate pool and coverage notes, then the Verifier's source assessment, KEEP/DROP reasons, Coverage Review decisions, and remaining gaps; Pipeline D ignores them because it reads report Markdown rather than audit text files.

---

## Why This Plugin

- **15 specialised agents** across four pipelines, each agent narrowly scoped
- **Parallel high-freedom Luna Scanners** — one focused agent and one short direction per category, with no outlet list, source tier, candidate quota, impact threshold, deduplication, or routing logic
- **Per-URL date verification** in `$sci-research:daily-news-intelligence` — neighbouring days are discarded
- **Readable free reporting** — paid or stub-only leads are replaced with an authoritative free same-event article or excluded
- **Editorial second-pass filter** (`sci-research-news-verifier`) for daily news — evidence fit / new information / contextual news value / originality / dedup
- **Fact Manifest + 5-pass Editor** — numbers / names / dates / quotes locked to a verbatim YAML manifest, then fact-checked and style-repaired post-Writer
- **External-view China gate** — `$sci-research:daily-news-intelligence --country "China"` uses foreign media only and excludes Chinese-domestic outlets and Chinese government domains
- **Free-prose Writer** — daily news Writer composes explanatory prose in the target language, not a mechanical translation
- **Bilingual mode (1.18.0+)** — `--lang zh+en` runs the category Scanner fan-out once per report, then fans Writer/Editor out per language in parallel and ships one email with a stacked bilingual body + up to 4 attachments
- **Branded Word output** via SPD Bank template (`$sci-research:daily-briefing`)
- **Commercial opportunity pipeline** for China-to-UK/Europe expansion, M&A, investment, and Companies House changes
- **Evidence-first Companies House radar** with confirmed/probable/unverified Chinese-nexus labels and explicit coverage limits
- **Gmail SMTP email delivery** built into all four pipelines
- **Quality hooks** enforce Pipeline C/F Markdown format and email-send safety
- **Multilingual** — Chinese / English / Japanese output

---

## Deployment

Sci-Research has two deployment layers:

1. The Codex marketplace installs the plugin skills and hooks.
2. The runtime setup skill copies the plugin's 15 namespaced TOML agents into the project where the pipelines will run and ensures enough project-scoped subagent concurrency for Pipelines C and F.

Marketplace installation alone is therefore not sufficient. Complete every step below before the first pipeline run.

### First-Time Installation From GitHub

#### Step 1 — Check the required executables

```bash
codex --version
python3 --version
node --version
```

These three commands must succeed. Python **3.11 or newer** is required because the runtime installer parses TOML with the standard-library `tomllib` module. Node.js is required by the quality hooks.

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

#### Step 4 — Create and enter a runtime workspace

```bash
mkdir -p ~/.sci-research
cd ~/.sci-research
codex
```

`~/.sci-research` is the recommended default, not a mandatory location. For the Codex macOS App, run only `mkdir -p ~/.sci-research`, then open it as the workspace in the App instead of running the `codex` CLI command.

Whichever workspace you choose must be used for both runtime setup and pipeline execution because the custom agents are project-scoped. To run the plugin in another workspace, install the runtime there as well. The default report directories remain under `~/.sci-research/reports/` unless overridden.

#### Step 5 — Install the project-scoped agents from inside Codex

Enter this in the Codex task, not in the shell:

```text
Use $sci-research:setup-sci-research-runtime to install the project-scoped runtime in this workspace.
```

The setup performs a bundle check and dry-run before installing. It creates:

```text
<runtime-workspace>/.codex/agents/sci-research-*.toml
<runtime-workspace>/.codex/config.toml
<runtime-workspace>/.codex/sci-research-runtime.json
```

With the recommended default workspace, `<runtime-workspace>` is `~/.sci-research`.

The project config sets `agents.max_threads = 10` and `agents.max_depth = 1`. China reports need seven concurrent category Scanner threads; the extra slots allow clean stage handoff without using recursive delegation. If `.codex/config.toml` already exists, setup preserves it byte-for-byte and requires `agents.max_threads >= 10`; a lower or missing value produces the exact TOML block to add.

It does not modify global `~/.codex/config.toml`, install Python packages, or run a news pipeline. If it reports an unmanaged-file conflict, a locally modified managed agent, or an insufficient existing thread limit, resolve the named file instead of overwriting it manually.

#### Step 6 — Review plugin hooks

Inside Codex, open:

```text
/hooks
```

Review and trust the three Sci-Research hooks if Codex asks:

- `email-send-guard` — blocks inline SMTP implementations.
- `daily-news-format-check` — reports invalid Pipeline C Markdown after edits.
- `opportunity-briefing-format-check` — reports invalid Pipeline F Markdown and blocks DOCX/email delivery in direct-check mode.

#### Step 7 — Start a new Codex task in the same workspace

End the current task, keep the same runtime workspace open, and start a new task. Project custom agents are discovered when a task starts; the setup task is not accepted as proof that the new agent registry has loaded.

In the new task, run a runtime-only check:

```text
Use $sci-research:setup-sci-research-runtime to check the project-scoped runtime in this workspace. Do not run a news pipeline.
```

The check must report 15 agents, `max_threads` of at least 10, and a matching plugin version before first use.

#### Step 8 — Run a no-email smoke test

Enter this in Codex:

```text
Use $sci-research:daily-news-intelligence --country "Japan" --lang en
```

Do not add `--email` to the first run. Pipeline C uses its default output directory under `~/.sci-research/reports/daily-news/{date}/`.

### Updating an Existing Git Marketplace Installation

An update crosses two task-reload boundaries. First refresh and reinstall the plugin outside the old task. Then start a fresh setup task to update the project agents. Finally start another fresh task to run a pipeline with the updated agent registry.

#### Step 1 — Refresh the Git marketplace

```bash
codex plugin marketplace upgrade sci-research-marketplace
```

The correct subcommand is `upgrade`. Codex does not provide `codex plugin update` or `codex plugin marketplace update`.

#### Step 2 — Reinstall the plugin from the refreshed snapshot

```bash
codex plugin add sci-research@sci-research-marketplace
codex plugin list --marketplace sci-research-marketplace
```

Confirm that the displayed plugin version changed and the plugin is installed and enabled. If it did not change, confirm that the pushed `.codex-plugin/plugin.json` has a new `+codex.<cachebuster>` suffix.

#### Step 3 — Start a fresh setup task

Close or leave any Codex task that was open before Step 2. Open the runtime workspace, normally `~/.sci-research`, and start a **new task**. This boundary is required so the updated setup skill and plugin bundle are loaded.

#### Step 4 — Update and check the project-scoped agents

In that new setup task, enter:

```text
Use $sci-research:setup-sci-research-runtime to update and check the project-scoped runtime in this workspace.
```

The updater backs up managed files before replacing them, refuses to overwrite local changes, and verifies that the runtime manifest version, agent hashes, and project thread limit match the newly installed plugin. Review `/hooks` again if Codex requests trust for updated hook definitions.

#### Step 5 — Start a fresh pipeline task

End the setup task and start another new task in the same workspace before running Pipeline C, D, E, or F. This second boundary loads the newly copied project agents. A successful runtime check inside the setup task does not prove that the setup task itself has refreshed its agent registry.

#### Diagnose a partial update

The installed plugin and project runtime must report the same version. Check the plugin in the shell:

```bash
codex plugin list --marketplace sci-research-marketplace
```

Then use a fresh Codex task in the runtime workspace:

```text
Use $sci-research:setup-sci-research-runtime to check the project-scoped runtime in this workspace. Do not run a news pipeline.
```

A version mismatch, missing agent, or agent hash mismatch means the update stopped before runtime resync. Repeat Steps 3-5; do not run a pipeline from the half-updated workspace.

### Local Marketplace Development

Use this instead of the GitHub marketplace flow when testing an unpushed checkout. The local checkout and Git marketplace both declare the name `sci-research-marketplace`, so only one of those sources can be configured under that name at a time.

```bash
git clone https://github.com/haiou312/sci-research.git
cd sci-research
codex plugin marketplace list
```

If `sci-research-marketplace` is already listed, remove that configured source before adding the checkout:

```bash
codex plugin marketplace remove sci-research-marketplace
```

The command removes the configured marketplace source, not your checkout. Then register and install the local source:

```bash
codex plugin marketplace add "$PWD"
python3 scripts/codex/update-plugin-cachebuster.py
codex plugin add sci-research@sci-research-marketplace
codex plugin list --marketplace sci-research-marketplace
```

After each checkout change:

```bash
python3 scripts/codex/update-plugin-cachebuster.py
codex plugin add sci-research@sci-research-marketplace
```

Then follow the same two-task sequence as a normal update: start a fresh setup task, update/check the runtime, end that task, and start a fresh pipeline task. `marketplace upgrade` is only for Git marketplace sources and is not used while the configured source is the local path.

To switch back to the Git marketplace:

```bash
codex plugin marketplace remove sci-research-marketplace
codex plugin marketplace add haiou312/sci-research --ref main
codex plugin add sci-research@sci-research-marketplace
```

Then repeat the setup-task and pipeline-task boundaries so the runtime and loaded agents match the restored Git version.

### Pipelines D/F Dependency (optional)

Pipelines D and F require the additional `python-docx` package. If no source checkout exists yet, create one, then install the declared dependency before starting Codex:

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

### Companies House API (optional for Pipeline F)

Create an API key at the [Companies House Developer Hub](https://developer.company-information.service.gov.uk/) and export it before launching Codex:

```bash
export COMPANIES_HOUSE_API_KEY='your-api-key'
```

With `--companies-house auto` (the default), Pipeline F records registry coverage as unavailable when the key is absent and continues without fabricating findings. With `--companies-house required`, a missing key stops the run.

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
| F opportunity briefing | `~/.sci-research/reports/china-opportunity-briefings/{date_to}/` |

```text
# Today's multi-country briefing with default countries and 14 stories
$sci-research:daily-briefing --email you@gmail.com

# Specific date with custom country selection
$sci-research:daily-briefing --date 2026-05-11 --countries "中国,日本,韩国" --total 12
```

### Pipeline E — `$sci-research:reputation-track` (Company Reputation Risk Monitor)

```
$sci-research:reputation-track --company "<name|ticker>" --email <a@x.com> \
  [--date YYYY-MM-DD] [--lang zh|en] [--email-dry-run]
```

Uses Yahoo Finance to confirm the company and current executives, then searches exact-date non-mainland-China media and public social media. A Verifier keeps genuine reputation risks and grades them `high`, `medium`, or `low`. **Silent when clean** — HTML and email are produced only when findings exist.

```text
# Monitor Tesla and its current executives today
$sci-research:reputation-track --company "TSLA" --email you@gmail.com

# English dry-run for a specific date
$sci-research:reputation-track --company "9988.HK" --date 2026-05-10 --lang en --email you@gmail.com --email-dry-run
```

### Pipeline F — `$sci-research:china-outbound-opportunity-briefing`

```text
$sci-research:china-outbound-opportunity-briefing \
  [--date-from YYYY-MM-DD] [--date-to YYYY-MM-DD] [--total 12] \
  [--companies-house auto|required|off] [--watchlist <path>] \
  [--previous-ch-snapshot <path>] \
  [--images prefer|none] [--out-dir <path>] \
  [--email <a@x.com,b@y.com>] [--email-dry-run]
```

Pipeline F scans five lanes in parallel: UK economic and policy signals, Chinese expansion into Europe, cross-border M&A, UK/Europe investment footprints, and Companies House entity discovery. It then runs a scoped registry collector/diff, Chinese-nexus analyst, senior Verifier, locked Fact Manifest, Chinese Writer/Editor, format gate, and institutional DOCX exporter.

```text
# Default seven-day Chinese opportunity briefing
$sci-research:china-outbound-opportunity-briefing

# Require registry coverage and use a maintained parent/entity watchlist
$sci-research:china-outbound-opportunity-briefing --companies-house required \
  --watchlist ~/.sci-research/config/china-company-watchlist.json
```

---

## How It Works

### Pipeline C — `$sci-research:daily-news-intelligence`

```
sci-research-daily-news-scanner ×categories → mechanical batch → sci-research-news-verifier → sci-research-daily-fact-extractor → sci-research-daily-news-writer → sci-research-daily-editor → pandoc → email (optional)
   (Luna / medium, parallel)                               (Terra / high)  (5.4 mini / medium)    (Sol / high, ×langs) (Sol / high, ×langs)

Bilingual mode (--lang zh+en …): the category Scanner fan-out runs once per report; Verifier/Fact-Extractor run once; Writer ×langs in parallel → Editor ×langs in parallel → pandoc ×langs
```

| Agent | Codex configuration | Role |
|---|---|---|
| `sci-research-daily-news-scanner` | gpt-5.6-luna / medium | One parallel instance per active category. Each instance follows one short category direction; hard-gates exact date, authoritative media, readable body, paid-to-free replacement, China foreign-media-only sourcing, and Europe-ex-UK scope; and reports search/open-page counts. The orchestrator mechanically wraps all outputs before handing every qualifying URL to the Verifier |
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
sci-research-reputation-scanner → sci-research-reputation-verifier → sci-research-reputation-writer → email
       (Luna / medium)                    (Terra / high)                    (Terra / medium)
```

The Scanner resolves the company and current key executives through Yahoo Finance, then freely searches exact-date non-mainland-China media and public social content about every subject. It excludes mainland Chinese media, mainland Chinese government domains, and mainland Chinese social platforms. Hong Kong, Macao, Taiwan, and all other countries and regions remain eligible.

The Verifier removes non-risk content, deduplicates events, and grades findings `high`, `medium`, or `low`. There is no source matrix, outlet tier, risk-category taxonomy, `critical` level, confidence score, or minimum-severity filter. `findings: []` exits silently.

| Agent | Codex configuration |
|---|---|
| `sci-research-reputation-scanner` | gpt-5.6-luna / medium |
| `sci-research-reputation-verifier` | gpt-5.6-terra / high |
| `sci-research-reputation-writer` | gpt-5.6-terra / medium |

### Pipeline F — `$sci-research:china-outbound-opportunity-briefing`

```text
opportunity-scanner ×5 → Companies House collector/diff → Companies House analyst
       → opportunity-verifier → opportunity-fact-extractor → opportunity-writer
       → opportunity-editor → format gate → institutional DOCX → email (optional)
```

| Agent | Codex configuration | Role |
|---|---|---|
| `sci-research-opportunity-scanner` | gpt-5.6-luna / medium | One parallel instance per discovery lane |
| `sci-research-companies-house-analyst` | gpt-5.6-terra / high | Resolves Chinese nexus and material registry changes |
| `sci-research-opportunity-verifier` | gpt-5.6-terra / high | Revalidates, deduplicates, prioritises, and frames banking hypotheses |
| `sci-research-opportunity-fact-extractor` | gpt-5.4-mini / medium | Locks factual values, stages, registry facts, sources, and image provenance |
| `sci-research-opportunity-writer` | gpt-5.6-sol / high | Writes the Chinese institutional briefing |
| `sci-research-opportunity-editor` | gpt-5.6-sol / high | Runs six factual, identity, framing, format, and fluency passes |

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

---

## Quality Hooks

| Hook | Pipeline | Trigger | What It Does |
|---|---|---|---|
| `daily-news-format-check` | C | PostToolUse:apply_patch + direct pre-delivery check | Reports format violations after edits; the direct `--file` check hard-stops export/email on count, numbering, URL, quote-mark, or body-length failures |
| `opportunity-briefing-format-check` | F | PostToolUse:apply_patch + direct pre-delivery check | Enforces section order, action tables, story fields, sources, image provenance/fallback, Companies House confidence, and disclaimer |
| `email-send-guard` | C / D / E / F | PreToolUse:Bash | **Blocks** inline `smtplib` / `MIMEMultipart` / `sendmail` Bash commands that bypass the sanctioned `send-*-email.py` scripts |

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
│   ├── sci-research-reputation-scanner.toml
│   ├── sci-research-reputation-verifier.toml
│   ├── sci-research-reputation-writer.toml
│   ├── sci-research-opportunity-scanner.toml
│   ├── sci-research-companies-house-analyst.toml
│   ├── sci-research-opportunity-verifier.toml
│   ├── sci-research-opportunity-fact-extractor.toml
│   ├── sci-research-opportunity-writer.toml
│   └── sci-research-opportunity-editor.toml
├── skills/                                  # 4 pipelines + project runtime setup
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
│   │       ├── severity-rules.md
│   │       ├── html-template.md
│   │       ├── email-spec.md
│   │       └── schemas.md
│   ├── china-outbound-opportunity-briefing/ # Pipeline F
│   │   ├── SKILL.md
│   │   ├── agents/openai.yaml
│   │   ├── references/                      # Rubric, schemas, registry, images, output
│   │   └── scripts/                         # Registry collector/diff + DOCX exporter
│   └── setup-sci-research-runtime/           # Installs/checks project-scoped agents
│       ├── SKILL.md
│       ├── runtime/config.toml                # Project-scoped agent concurrency template
│       └── scripts/sync_runtime.py
├── hooks/hooks.json                         # Plugin lifecycle hook config
├── scripts/
│   ├── codex/check-plugin-bundle.py         # Installed-cache integrity check
│   ├── codex/update-plugin-cachebuster.py    # Refresh local-development plugin version suffix
│   ├── hooks/                               # Hook implementations (Node.js)
│   │   ├── daily-news-format-check.js
│   │   ├── opportunity-briefing-format-check.js
│   │   └── email-send-guard.js
│   └── send-report-email.py                 # Gmail SMTP (Pipelines C / E / F)
├── tests/
│   ├── test_hooks.py                        # Codex hook protocol tests
│   ├── test_opportunity_scripts.py          # Companies House collector/diff tests
│   ├── test_runtime_sync.py                 # Isolated setup/update/uninstall tests
│   └── fixtures/opportunity-briefing-sample.md
├── .env.example                             # Gmail SMTP environment template
├── requirements.txt                         # Pipelines D/F dependency
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
| Pipeline E search and mainland-China exclusions | `.codex/agents/sci-research-reputation-scanner.toml` |
| Pipeline E severity judgement | `skills/reputation-track/references/severity-rules.md` + `.codex/agents/sci-research-reputation-verifier.toml` |
| Pipeline E HTML email template | `skills/reputation-track/references/html-template.md` |
| Pipeline F selection / opportunity rules | `skills/china-outbound-opportunity-briefing/references/rubric.md` |
| Pipeline F Companies House method | `skills/china-outbound-opportunity-briefing/references/companies-house-method.md` + collector/diff scripts |
| Pipeline F output / image / layout policy | `skills/china-outbound-opportunity-briefing/references/output-spec.md` + `references/image-policy.md` + `references/layout-benchmarks.md` |
| Pipeline F agent behavior | `.codex/agents/sci-research-opportunity-*.toml` + `.codex/agents/sci-research-companies-house-analyst.toml` |
| New output language (Pipeline C) | `.codex/agents/sci-research-daily-news-writer.toml` + `skills/daily-news-intelligence/references/language-spec.md` |
| Adding hook / changing email-send guard | `scripts/hooks/email-send-guard.js` + the relevant SKILL.md email step |

---

## Requirements

- [Codex](https://developers.openai.com/codex) CLI for marketplace installation and updates; pipelines may run in the CLI or macOS App after setup
- Node.js ≥ 18 (for hook scripts)
- Python ≥ 3.11 (required by runtime setup; also used by email delivery and Pipelines D/F)
- Pipelines D/F dependency (install or update from the plugin root): `python3 -m pip install --user --upgrade -r requirements.txt`
- `pandoc` is optional; without it Pipeline C still produces Markdown but skips docx export
- Internet access (for WebSearch `search` / `open_page`)
- Gmail SMTP credentials (only when `--email` is used; see `.env.example`)
- Companies House API key (optional in Pipeline F `auto` mode; required in `required` mode)
- No separate social-media MCP configuration is required. Pipeline E uses public, openable social content discovered through WebSearch.

---


## License

MIT
