# Reputation Alert HTML

The Writer produces a compact email body with inline CSS and no external resources.

Required content:

1. Company name, date, and highest severity.
2. A short overall summary.
3. Findings ordered `high`, `medium`, `low`.
4. For each finding: severity, company or executive subject, headline, what happened, reputation impact, verbatim evidence excerpt, source name, publication time, and clickable URL.
5. A short footer telling the recipient to review the linked source before acting.

Use Chinese labels for `lang=zh` and English labels for `lang=en`. Social findings must visibly say that the source is a social-media post or allegation.

Severity colors:

| Severity | Color |
|---|---|
| `high` | `#c62828` |
| `medium` | `#ef6c00` |
| `low` | `#b58900` |

Technical constraints:

- Start with `<!DOCTYPE html>`.
- UTF-8.
- Inline CSS only.
- Maximum content width 640px.
- No scripts, external images, fonts, icons, source tiers, risk categories, confidence scores, or coverage matrix.
