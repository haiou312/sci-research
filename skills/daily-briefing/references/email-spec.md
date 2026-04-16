# Email Spec — Daily Briefing Email Delivery

Independent email specification for the `/daily-briefing` pipeline.

## When This Step Runs

Only when the `email` parameter is non-empty. If `email` is empty or missing, skip silently — the local docx file is still delivered.

## Environment Variables

Same as Gmail SMTP standard: `GOOGLE_EMAIL_USERNAME`, `GOOGLE_EMAIL_APP_PASSWORD`, `GOOGLE_EMAIL_FROM_NAME` (optional), `GOOGLE_EMAIL_HOST` (default `smtp.gmail.com`), `GOOGLE_EMAIL_PORT` (default `587`), `GOOGLE_EMAIL_START_TLS` (default `true`).

## Subject Template

Default (override via `--email-subject`):

```
新闻简报 — {date_display}
```

Example: `新闻简报 — 2026年4月16日`

## Body Template (success)

```
你好，

附件是今日新闻简报，由 Claude Code sci-research 插件自动生成。

· 日期: {date}
· 新闻条数: {story_count} 条
· 覆盖地区: {countries}
· 附件: {filename}

— sci-research daily-briefing
```

## Body Template (no report available)

Used when no source Markdown files were found for the target date.

```
你好，

今日（{date}）的每日新闻源文件未找到，新闻简报未生成。

可能原因：
· 各国新闻情报尚未运行或未完成
· 源文件目录 ({source_dir}/{date}/) 中无 Markdown 文件

请确认各国新闻报告已生成后重试。

— sci-research daily-briefing
```

Subject for this case: `⚠️ 新闻简报未生成 — {date_display}`

## Attachment

Always attach only the branded docx file. No Markdown attachment.

## Exit Code Handling

| Script exit | Orchestrator action |
|---|---|
| 0 | Print confirmation |
| 1 | Print missing env vars warning — do NOT delete docx |
| 2 | Print invalid recipient warning — do NOT delete docx |
| 3 | Print SMTP error — do NOT delete docx |
| 4 | Print attachment not found — do NOT delete docx |
| 5 | Print body file not found — do NOT delete docx |

Email failure never deletes the local docx file.

## Security

- Never log or echo `GOOGLE_EMAIL_APP_PASSWORD`.
- The Python subprocess inherits env vars implicitly — do NOT pass the password via command-line flags.
