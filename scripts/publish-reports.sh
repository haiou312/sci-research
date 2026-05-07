#!/usr/bin/env bash
# Publish daily-news-reports to GitHub Pages.
#
# Pipeline C (/daily-news-intelligence) writes per-country md+docx into
# ~/Desktop/github/daily-news-reports/{date}/ by default. Pipeline D
# (/daily-briefing) writes the SPD-branded summary docx into the same
# directory. After the day's run completes, this script commits and
# pushes everything in one shot. The GitHub Actions workflow on the
# remote repo (.github/workflows/update-index.yml) then refreshes
# index.json server-side, so no local index step is needed.
#
# Usage:
#   bash scripts/publish-reports.sh                # commit & push current state
#   bash scripts/publish-reports.sh --dry-run      # show what would be committed, do not push
#
# Idempotent: exits 0 cleanly when there is nothing to publish.

set -euo pipefail

REPO="${REPORTS_REPO:-$HOME/Desktop/github/daily-news-reports}"
DRY_RUN="${1:-}"

if [[ ! -d "$REPO/.git" ]]; then
  echo "ERROR: $REPO is not a git repository. Aborting." >&2
  exit 1
fi

cd "$REPO"

# 1. Stage everything except files matched by .gitignore
git add -A

# 2. Bail out cleanly when no changes are pending
if git diff --cached --quiet; then
  echo "publish-reports: nothing to publish ($(date -u +%FT%TZ))"
  exit 0
fi

# 3. Build a commit message that lists touched dates
TOUCHED_DATES=$(git diff --cached --name-only \
  | awk -F/ '/^20[0-9]{2}-[0-9]{2}-[0-9]{2}\// {print $1}' \
  | sort -u \
  | paste -sd, -)
if [[ -z "$TOUCHED_DATES" ]]; then
  TOUCHED_DATES="(meta)"
fi

MSG="publish reports — $TOUCHED_DATES"

if [[ "$DRY_RUN" == "--dry-run" ]]; then
  echo "would commit: $MSG"
  echo "staged files:"
  git diff --cached --name-only | head -30
  exit 0
fi

# 4. Commit and push
git commit -m "$MSG"
git push origin main

echo "publish-reports: pushed — $MSG"
echo "GitHub Actions will refresh index.json shortly."
