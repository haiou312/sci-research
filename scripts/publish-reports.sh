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

# 3. Build a commit message that lists touched dates.
#    `core.quotepath=false` keeps non-ASCII filenames literal (no \344\270\255 octal
#    escapes), so the date-prefix regex can match the YYYY-MM-DD/ leading segment.
TOUCHED_DATES=$(git -c core.quotepath=false diff --cached --name-only \
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
  git -c core.quotepath=false diff --cached --name-only | head -30
  exit 0
fi

# 4. Commit
git commit -m "$MSG"

# 5. Push, with one auto-rebase retry if the remote moved.
#    The reports repo's GitHub Actions workflow auto-commits index.json after
#    every push, so a second run can find origin ahead. Rebase + retry handles
#    that case without bothering the user.
push_with_retry() {
  if git push origin main 2>&1; then
    return 0
  fi
  echo "publish-reports: push rejected, pulling --rebase and retrying once..."
  git pull --rebase --autostash origin main
  git push origin main
}
push_with_retry

echo "publish-reports: pushed — $MSG"
echo "GitHub Actions will refresh index.json shortly."
