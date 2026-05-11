#!/usr/bin/env bash
# deploy.sh — commit generated sites + push to GitHub Pages.
#
# Usage:
#   ./scripts/deploy.sh                     # commit + push to current branch
#   BRANCH=gh-pages ./scripts/deploy.sh     # override target branch
#
# What this does:
#   1. Stages sites/, data/prospects.csv, dashboard.md
#   2. Commits with a timestamped message
#   3. Pushes to origin <branch> (default: gh-pages)
#   4. Prints live URLs for any newly added site folders

set -euo pipefail

cd "$(dirname "$0")/.."

BRANCH="${BRANCH:-gh-pages}"

# Detect repo URL → derive the GitHub Pages URL base.
REMOTE_URL="$(git config --get remote.origin.url || true)"
if [[ -z "$REMOTE_URL" ]]; then
  echo "ERROR: no 'origin' remote configured. Run:"
  echo "  git remote add origin git@github.com:<user>/<repo>.git"
  exit 1
fi

# Parse "git@github.com:user/repo.git" or "https://github.com/user/repo.git"
if [[ "$REMOTE_URL" =~ github\.com[:/]([^/]+)/([^/.]+)(\.git)?$ ]]; then
  GH_USER="${BASH_REMATCH[1]}"
  GH_REPO="${BASH_REMATCH[2]}"
else
  echo "WARN: could not parse GitHub user/repo from: $REMOTE_URL"
  GH_USER=""
  GH_REPO=""
fi

PAGES_BASE=""
if [[ -n "$GH_USER" && -n "$GH_REPO" ]]; then
  if [[ "$GH_REPO" == "${GH_USER}.github.io" ]]; then
    PAGES_BASE="https://${GH_USER}.github.io"
  else
    PAGES_BASE="https://${GH_USER}.github.io/${GH_REPO}"
  fi
fi

# Find new site dirs (untracked or added since last commit on this branch).
NEW_SITES=()
while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  NEW_SITES+=("$line")
done < <(git status --porcelain sites/ | awk '/^(\?\?|A )/ {sub("^.. ", "", $0); print}' \
         | awk -F/ '/^sites\// {print $2}' | sort -u)

# Stage
git add sites/ data/prospects.csv dashboard.md 2>/dev/null || true

if git diff --cached --quiet; then
  echo "Nothing to deploy — no staged changes."
  exit 0
fi

STAMP="$(date '+%Y-%m-%d %H:%M:%S')"
git commit -m "Deploy site batch — $STAMP"

CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
if [[ "$CURRENT_BRANCH" != "$BRANCH" ]]; then
  echo "Pushing $CURRENT_BRANCH → origin/$BRANCH"
  git push origin "HEAD:$BRANCH"
else
  git push origin "$BRANCH"
fi

echo
echo "Deployed. Newly published previews:"
if [[ ${#NEW_SITES[@]} -eq 0 ]]; then
  echo "  (no new site directories detected — content updates only)"
else
  for slug in "${NEW_SITES[@]}"; do
    if [[ -n "$PAGES_BASE" ]]; then
      echo "  $PAGES_BASE/sites/$slug/"
    else
      echo "  sites/$slug/"
    fi
  done
fi
