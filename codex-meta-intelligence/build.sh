#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT=$(cd "$(dirname "$0")" && pwd)
STAGE_FILE="$PROJECT_ROOT/stage.json"
PROMOTE_STAGE=${PROMOTE_STAGE:-1}

if ! command -v jq >/dev/null 2>&1; then
  echo "jq is required to run the build orchestrator" >&2
  exit 1
fi

run_stage_one() {
  echo "Executing Stage 1 tasks for Codex Meta-Intelligence"
  echo "----------------------------------------------------"
  cd "$PROJECT_ROOT"

  if ! command -v pnpm >/dev/null 2>&1; then
    echo "pnpm is required. Enable it via \`corepack enable\`." >&2
    exit 1
  fi

  if ! pnpm install --filter codex-meta-intelligence...; then
    echo "Primary pnpm install command failed, falling back to workspace install" >&2
    CI=1 pnpm install
  fi
  pnpm lint
  pnpm test
  pnpm typecheck
  pnpm build
}

run_stage_two() {
  echo "Stage 2 tasks are not yet implemented. Prepare advanced integrations before promoting." >&2
  exit 2
}

run_stage_three() {
  echo "Stage 3 tasks are not yet implemented. Complete prior stages first." >&2
  exit 3
}

advance_stage() {
  local current_stage next_stage tmp_file timestamp
  current_stage=$(jq -r '.stage' "$STAGE_FILE")
  next_stage=$((current_stage + 1))
  timestamp=$(date -u +%FT%TZ)
  tmp_file=$(mktemp)
  jq \
    --arg current "stage_${current_stage}" \
    --arg time "$timestamp" \
    --argjson next "$next_stage" \
    '
    .stage = $next
    | .completed |= (. // {})
    | .completed[$current] = { "completedAt": $time }
  ' "$STAGE_FILE" >"$tmp_file"
  mv "$tmp_file" "$STAGE_FILE"
  echo "Promoted to stage $next_stage (recorded completion for stage $current_stage)"
}

current_stage=$(jq -r '.stage' "$STAGE_FILE")

case "$current_stage" in
  1)
    run_stage_one
    if [[ "$PROMOTE_STAGE" == "1" ]]; then
      advance_stage
    fi
    ;;
  2)
    run_stage_two
    ;;
  3)
    run_stage_three
    ;;
  *)
    echo "Unknown stage: $current_stage" >&2
    exit 10
    ;;
esac
