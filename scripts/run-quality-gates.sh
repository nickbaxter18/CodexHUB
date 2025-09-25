#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
STAGE="${1:-pre-commit}"
shift || true

run() {
  echo "[quality-gates] $*"
  "$@"
}

codex/codify-project-improvements-and-upgrades-pgjoca
should_skip_cursor_validation() {
  case "${CURSOR_SKIP_VALIDATE:-false}" in
    1|true|TRUE|True|yes|YES)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

run_cursor_validation() {
  if should_skip_cursor_validation; then
    echo "[quality-gates] Skipping Cursor validation (CURSOR_SKIP_VALIDATE set)"
    return
  fi

  if ! command -v pnpm >/dev/null 2>&1; then
    echo "[quality-gates] pnpm not available; skipping Cursor validation" >&2
    return
  fi

  run pnpm run cursor:validate
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
codex/codify-project-improvements-and-upgrades-pgjoca
    run_cursor_validation
    run pnpm run scan:sast
    run pnpm run scan:secrets -- --report-format sarif --report-path "$ROOT_DIR/results/security/gitleaks-pre-push.sarif"
    ;;
  *)
    echo "Unknown quality gate stage: $STAGE" >&2
    exit 1
    ;;
esac
