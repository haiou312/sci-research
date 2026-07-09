#!/usr/bin/env bash
# Publish an explicitly selected report directory to a GitHub Pages repository.
#
# The report pipelines write locally by default. Publishing is opt-in: the
# caller must provide REPORTS_REPO and --source-dir <YYYY-MM-DD directory>.
# The source contents are copied to
# REPORTS_REPO/<date>/ before staging, committing, and pushing.
#
# Usage:
#   REPORTS_REPO=/absolute/path/to/reports-repo \
#     bash scripts/publish-reports.sh --source-dir /absolute/path/2026-04-16
#
#   REPORTS_REPO=/absolute/path/to/reports-repo \
#     bash scripts/publish-reports.sh --source-dir /absolute/path/2026-04-16 --dry-run
#
# Exit codes:
#   0 success, dry run, or nothing to publish
#   2 REPORTS_REPO missing or invalid arguments
#   3 REPORTS_REPO is not a Git repository
#   4 source directory invalid
#   5 target repository already has staged changes

set -euo pipefail

usage() {
  echo "Usage: REPORTS_REPO=/absolute/path bash scripts/publish-reports.sh --source-dir /path/YYYY-MM-DD [--dry-run]" >&2
}

REPO="${REPORTS_REPO:-}"
SOURCE_DIR=""
DRY_RUN=false

while (($#)); do
  case "$1" in
    --source-dir)
      if [[ -z "${2:-}" ]]; then
        echo "ERROR: --source-dir requires a directory path." >&2
        usage
        exit 2
      fi
      SOURCE_DIR="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "ERROR: unknown argument: $1" >&2
      usage
      exit 2
      ;;
  esac
done

if [[ -z "$REPO" ]]; then
  echo "ERROR: REPORTS_REPO is required. Publishing is intentionally opt-in." >&2
  exit 2
fi

if [[ -z "$SOURCE_DIR" ]]; then
  echo "ERROR: --source-dir is required. Publishing an arbitrary repository state is not supported." >&2
  exit 2
fi

if [[ ! -d "$REPO/.git" ]]; then
  echo "ERROR: $REPO is not a git repository. Aborting." >&2
  exit 3
fi

SOURCE_DIR="${SOURCE_DIR%/}"
if [[ ! -d "$SOURCE_DIR" ]]; then
  echo "ERROR: source directory does not exist: $SOURCE_DIR" >&2
  exit 4
fi

REPORT_DATE="$(basename "$SOURCE_DIR")"
if [[ ! "$REPORT_DATE" =~ ^20[0-9]{2}-[0-9]{2}-[0-9]{2}$ ]]; then
  echo "ERROR: --source-dir must end in an ISO date directory (YYYY-MM-DD): $SOURCE_DIR" >&2
  exit 4
fi
TARGET_DIR="$REPO/$REPORT_DATE"

cd "$REPO"

if [[ "$DRY_RUN" == true ]]; then
  echo "would copy: $SOURCE_DIR/. -> $TARGET_DIR/"
  echo "source files:"
  find "$SOURCE_DIR" -maxdepth 2 -type f | sort | head -30
  echo "current repository changes:"
  git status --short
  exit 0
fi

# Sync first: the remote workflow may have updated index.json after the
# previous publishing run.
echo "publish-reports: syncing with origin/main..."
git pull --rebase --autostash origin main

if ! git diff --cached --quiet; then
  echo "ERROR: target repository has staged changes; refusing to include them in a report publish." >&2
  exit 5
fi

mkdir -p "$TARGET_DIR"
cp -pR "$SOURCE_DIR"/. "$TARGET_DIR"/
echo "publish-reports: copied $SOURCE_DIR -> $TARGET_DIR"

git add -- "$REPORT_DATE"

if git diff --cached --quiet; then
  echo "publish-reports: nothing to publish ($(date -u +%FT%TZ))"
  exit 0
fi

TOUCHED_DATES=$(git -c core.quotepath=false diff --cached --name-only \
  | awk -F/ '/^20[0-9]{2}-[0-9]{2}-[0-9]{2}\// {print $1}' \
  | sort -u \
  | paste -sd, -)
if [[ -z "$TOUCHED_DATES" ]]; then
  TOUCHED_DATES="(meta)"
fi

MSG="publish reports — $TOUCHED_DATES"
git commit -m "$MSG"

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
