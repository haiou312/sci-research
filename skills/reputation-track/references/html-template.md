# HTML Email Body Template

Loaded by the Writer. Describes the HTML shape that becomes the `text/html` part of the `multipart/alternative` email body.

## Hard Constraints

- **Inline CSS only.** Email clients (Gmail, Outlook) strip `<style>` blocks and `<link>` tags.
- **No external resources.** No remote images, fonts, or scripts.
- **Table-based layout.** Outlook does not reliably support flexbox or grid. Use `<table role="presentation">` for columns.
- **Max width 600px.** Keeps mobile clients from horizontal scrolling.
- **UTF-8.** All CJK content renders correctly.
- **No emojis, no icons.** Use colored left-borders and uppercase labels for severity instead.

## Required Skeleton

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{company_display} Reputation Alert — {date_display}</title>
</head>
<body style="margin:0;padding:0;background:#f5f5f5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;color:#1a1a1a;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f5f5f5;">
    <tr><td align="center" style="padding:24px 12px;">
      <table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background:#ffffff;border-radius:8px;overflow:hidden;">

        <!-- HEADER -->
        <tr><td style="padding:24px 32px;border-bottom:3px solid #d32f2f;">
          <div style="font-size:11px;font-weight:700;color:#d32f2f;letter-spacing:1.5px;">{alert_label}</div>
          <h1 style="margin:8px 0 6px;font-size:24px;line-height:1.2;color:#1a1a1a;">{company_display}</h1>
          <div style="font-size:13px;color:#666;">
            {date_display} · {items_kept_label} · {sources_label}
          </div>
        </td></tr>

        <!-- TL;DR -->
        <tr><td style="padding:20px 32px;background:#fff5f5;border-left:4px solid #d32f2f;">
          <div style="font-size:12px;font-weight:700;color:#d32f2f;letter-spacing:1.2px;text-transform:uppercase;">{tldr_label}</div>
          <p style="margin:8px 0 0;font-size:15px;line-height:1.6;color:#333;">{tldr_paragraph}</p>
        </td></tr>

        <!-- REPEAT: one section per non-empty category -->
        <tr><td style="padding:24px 32px 8px;">
          <h2 style="margin:0 0 16px;font-size:17px;color:#1a1a1a;border-bottom:1px solid #eee;padding-bottom:8px;">{category_label}</h2>

          <!-- REPEAT: one card per kept item within this category -->
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:14px;background:#fafafa;border-left:4px solid {severity_color};border-radius:4px;">
            <tr><td style="padding:14px 18px;">
              <div style="font-size:10px;font-weight:700;color:{severity_color};letter-spacing:1.2px;text-transform:uppercase;">
                {severity_label} · {subject_label}
              </div>
              <blockquote style="margin:10px 0 10px;padding:0;font-size:14px;line-height:1.55;color:#333;font-style:italic;">
                &ldquo;{verbatim_quote}&rdquo;
              </blockquote>
              <div style="font-size:12px;color:#666;line-height:1.5;">
                <a href="{source_url}" style="color:#1a73e8;text-decoration:none;">{source_outlet}</a>
                &nbsp;·&nbsp; {source_tier_label}
                &nbsp;·&nbsp; {published_at}
                {corroborating_html}
              </div>
            </td></tr>
          </table>

        </td></tr>

        <!-- FOOTER -->
        <tr><td style="padding:20px 32px 24px;background:#f9f9f9;border-top:1px solid #eee;">
          <div style="font-size:11px;color:#999;line-height:1.5;">
            {footer_disclaimer}
          </div>
        </td></tr>

      </table>
    </td></tr>
  </table>
</body>
</html>
```

## Severity Color Palette (inline)

| Severity | Hex | Used for border + label |
|---|---|---|
| `critical` | `#b71c1c` | deep red |
| `high` | `#d32f2f` | red |
| `medium` | `#f57c00` | orange |
| `low` | `#fbc02d` | amber |

## Category Order

Render non-empty categories in this precedence order:

1. Legal
2. Financial
3. Operational
4. Ethics
5. Leadership
6. Product
7. Activism

## Localised Labels

| Slot | `lang=zh` | `lang=en` |
|---|---|---|
| `alert_label` | `声誉预警` | `REPUTATION ALERT` |
| `tldr_label` | `要点摘要` | `SUMMARY` |
| `items_kept_label` | `{N} 项负面信号` | `{N} adverse signal(s)` |
| `sources_label` | `扫描源：{comma-joined sources}` | `Sources: {comma-joined sources}` |
| Category — Legal | `法律` | `Legal` |
| Category — Financial | `财务` | `Financial` |
| Category — Operational | `运营` | `Operational` |
| Category — Ethics | `伦理合规` | `Ethics` |
| Category — Leadership | `领导层` | `Leadership` |
| Category — Product | `产品` | `Product` |
| Category — Activism | `行动主义` | `Activism` |
| Severity — critical | `危急` | `CRITICAL` |
| Severity — high | `高` | `HIGH` |
| Severity — medium | `中` | `MEDIUM` |
| Severity — low | `低` | `LOW` |
| `subject_label` (company) | `公司` | `COMPANY` |
| `subject_label` (executive) | `高管：{name}` | `EXEC: {name}` |
| `source_tier_label` | `T1 通讯社` / `T2 财经媒体` / `T3 行业媒体` / `T4 其他` / `社交` | `Wire (T1)` / `Financial (T2)` / `Industry (T3)` / `Other (T4)` / `Social` |

## Corroborating Sources Rendering

When `corroborating_urls` is non-empty, append to the item's metadata line:

```
&nbsp;·&nbsp; {corroborating_label}：<a href="{url1}" style="color:#1a73e8;">+1</a> <a href="{url2}" style="color:#1a73e8;">+2</a>
```

Localise `corroborating_label` as `佐证` (zh) or `Corroborated by` (en).

## Footer Disclaimer (required)

Localised disclaimer explaining coverage limits. `lang=zh`:

> 覆盖范围：新闻（T1-T4）、Reddit（公开 subreddit）、X（Google 索引的公开推文）。Facebook 和 Threads 因公开 API 受限未纳入 v1 覆盖。每条负面判断均附源文件逐字引用，收件人应自行核实 URL 后再行动。本报告由 Claude Code `sci-research` 插件（`reputation-track`）自动生成。

`lang=en`:

> Coverage: News (T1-T4), Reddit (public subreddits), X (Google-indexed public posts). Facebook and Threads are intentionally excluded in v1 due to sparse public-post discoverability. Each adverse finding includes a verbatim quote from the source; recipients should verify the URL before acting. Generated by Claude Code `sci-research` plugin (`reputation-track`).

## Plain-Text Fallback

Not the Writer's job — the email script auto-generates a `text/plain` fallback by stripping tags and collapsing whitespace before send.
