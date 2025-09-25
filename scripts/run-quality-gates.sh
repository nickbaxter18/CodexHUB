#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
STAGE="${1:-pre-commit}"
shift || true

run() {
  echo "[quality-gates] $*"
  "$@"
}

cd "$ROOT_DIR"

case "$STAGE" in
  pre-commit)
    run pnpm lint-staged
    run python -m pre_commit run --hook-stage commit --show-diff-on-failure
    ;;
  pre-push)
    run pnpm lint
    run pnpm check-format
    run pnpm test
    run pnpm run typecheck
    run python -m pytest
    run pnpm run scan:sast
    run pnpm run scan:secrets -- --report-format sarif --report-path "$ROOT_DIR/results/security/gitleaks-pre-push.sarif"
    ;;
  *)
    echo "Unknown quality gate stage: $STAGE" >&2
    exit 1
    ;;
esac
