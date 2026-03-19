---
description: Change the output language for the current research session. Usage: /set-lang en|zh|ja
---

# Set Language

Switch the output language for the current or next research article.

## Supported Languages

| Code | Language | Writing Style |
|------|----------|---------------|
| `zh` | 中文 | 学术科普风格，formal but accessible |
| `en` | English | Academic-accessible (Nature News level) |
| `ja` | 日本語 | 学術的だが一般読者向け (ですます調) |

## Behavior

1. Validate the language code
2. If a research session is active, offer to regenerate the article in the new language
3. If no session is active, set as default for the next `/sci-research` invocation

## Usage

```
/set-lang en
```
