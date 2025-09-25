#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
STAGE="${1:-pre-commit}"
shift || true

LOG_SCRIPT="$ROOT_DIR/scripts/metrics/record_quality_gate.py"
COMMAND_DETAILS=()
START_EPOCH=$(date +%s)
FAILED_COMMAND=""

encode_command() {
  printf "%s" "$1" | base64 | tr -d '\n'
}

run() {
  if [[ $# -eq 0 ]]; then
    return 0
  fi
  echo "[quality-gates] $*"
  local label
  label=$(printf "%s " "$@")
  label=${label%% }
  local encoded
  encoded=$(encode_command "$label")
  local start
  start=$(date +%s)
  set +e
  "$@"
  local exit_code=$?
  set -e
  local end
  end=$(date +%s)
  COMMAND_DETAILS+=("${encoded}:${start}:${end}:${exit_code}")
  if [[ $exit_code -ne 0 ]]; then
    FAILED_COMMAND="$encoded"
    return $exit_code
  fi
  return 0
}

finish() {
  local exit_code=$?
  local end_epoch
  end_epoch=$(date +%s)
  if [[ -f "$LOG_SCRIPT" ]]; then
    python "$LOG_SCRIPT" \
      --stage "$STAGE" \
      --exit-code "$exit_code" \
      --started-at "$START_EPOCH" \
      --ended-at "$end_epoch" \
      ${FAILED_COMMAND:+--failed-command "$FAILED_COMMAND"} \
      $(for entry in "${COMMAND_DETAILS[@]}"; do printf ' --command-entry %s' "$entry"; done) || true
  fi
  exit "$exit_code"
}

trap finish EXIT

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
