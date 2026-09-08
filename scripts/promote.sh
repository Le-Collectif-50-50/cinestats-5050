#!/usr/bin/env bash
# Promotes `main` onto a deployment branch (preview or production),
# which triggers the corresponding GitHub Actions deploy workflow
# (deploy-preview.yml / deploy.yml). Fast-forward only by default —
# use --force only if you know why the branch has diverged.
#
# Usage:
#   scripts/promote.sh preview
#   scripts/promote.sh production --watch
#   scripts/promote.sh preview --force   # non-fast-forward, overwrites history
#
# Requires: git remote 'origin' pointing at the repo, gh CLI authenticated
# (only needed for --watch).

set -euo pipefail

REPO="Le-Collectif-50-50/cinestats-5050"
TARGET="${1:-}"
FORCE=false
WATCH=false

for arg in "${@:2}"; do
  case "$arg" in
    --force) FORCE=true ;;
    --watch) WATCH=true ;;
    *)
      echo "Error: unknown argument '$arg'" >&2
      exit 1
      ;;
  esac
done

if [[ "$TARGET" != "preview" && "$TARGET" != "production" ]]; then
  echo "Usage: $0 <preview|production> [--force] [--watch]" >&2
  exit 1
fi

echo "==> Fetching main and $TARGET"
git fetch origin main "$TARGET" --quiet

MAIN_SHA=$(git rev-parse origin/main)
TARGET_SHA=$(git rev-parse "origin/$TARGET")

if [[ "$MAIN_SHA" == "$TARGET_SHA" ]]; then
  echo "$TARGET is already up to date with main ($MAIN_SHA:0:7)."
  exit 0
fi

if ! $FORCE; then
  if ! git merge-base --is-ancestor "origin/$TARGET" origin/main; then
    echo "Error: origin/$TARGET is not an ancestor of origin/main — this would not be a fast-forward." >&2
    echo "main may be missing commits that are only on $TARGET, or the two have diverged." >&2
    echo "Investigate with: git log origin/main..origin/$TARGET --oneline" >&2
    echo "If you're sure you want to overwrite $TARGET anyway, rerun with --force." >&2
    exit 1
  fi
fi

echo "==> Promoting main (${MAIN_SHA:0:7}) onto $TARGET (was ${TARGET_SHA:0:7})"
if $FORCE; then
  git push origin "origin/main:refs/heads/$TARGET" --force
else
  git push origin "origin/main:refs/heads/$TARGET"
fi

WORKFLOW="Deploy"
if [[ "$TARGET" == "preview" ]]; then
  WORKFLOW="Deploy Preview"
fi

if ! $WATCH; then
  echo "==> Done. Watch it with: gh run watch --repo $REPO \$(gh run list --repo $REPO --branch $TARGET --workflow \"$WORKFLOW\" --limit 1 --json databaseId -q '.[0].databaseId')"
  exit 0
fi

echo "==> Waiting for the '$WORKFLOW' run to appear..."
for _ in $(seq 1 15); do
  RUN_ID=$(gh run list --repo "$REPO" --branch "$TARGET" --workflow "$WORKFLOW" --limit 1 --json databaseId,headSha -q ".[] | select(.headSha == \"$MAIN_SHA\") | .databaseId" || true)
  [[ -n "$RUN_ID" ]] && break
  sleep 2
done

if [[ -z "${RUN_ID:-}" ]]; then
  echo "Could not find the triggered run automatically — check: gh run list --repo $REPO --branch $TARGET" >&2
  exit 1
fi

echo "==> Watching run $RUN_ID"
gh run watch "$RUN_ID" --repo "$REPO" --exit-status
