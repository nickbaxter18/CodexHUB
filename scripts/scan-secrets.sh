#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(git rev-parse --show-toplevel)
DEFAULT_REPORT_DIR="$ROOT_DIR/results/security"

if [[ $# -gt 0 ]]; then
  case "$1" in
    --)
      shift
      ;;
    -* )
      # treat as option; keep default report dir
      ;;
    * )
      DEFAULT_REPORT_DIR=${1%/}
      shift
      ;;
  esac
fi

DEFAULT_REPORT_PATH="$DEFAULT_REPORT_DIR/gitleaks-report.sarif"
mkdir -p "$DEFAULT_REPORT_DIR"

ARGS=("$@")
FORMAT_SET=false
REPORT_SET=false
OUTPUT_PATH="$DEFAULT_REPORT_PATH"

for ((i = 0; i < ${#ARGS[@]}; i++)); do
  arg="${ARGS[$i]}"
  case "$arg" in
    --report-format*)
      FORMAT_SET=true
      ;;
    --report-path)
      REPORT_SET=true
      if (( i + 1 < ${#ARGS[@]} )); then
        OUTPUT_PATH="${ARGS[$((i + 1))]}"
      fi
      ;;
    --report-path=*)
      REPORT_SET=true
      OUTPUT_PATH="${arg#*=}"
      ;;
  esac
done

if [[ "$FORMAT_SET" = false ]]; then
  ARGS+=("--report-format" "sarif")
fi

if [[ "$REPORT_SET" = false ]]; then
  ARGS+=("--report-path" "$DEFAULT_REPORT_PATH")
  OUTPUT_PATH="$DEFAULT_REPORT_PATH"
fi

if [[ ! "$OUTPUT_PATH" = /* ]]; then
  OUTPUT_PATH="$ROOT_DIR/$OUTPUT_PATH"
fi

run_gitleaks() {
  if command -v gitleaks >/dev/null 2>&1; then
    gitleaks detect --source "$ROOT_DIR" --log-opts="--all" "${ARGS[@]}"
  elif command -v docker >/dev/null 2>&1; then
    local docker_args=("${ARGS[@]}")
    local docker_path="/repo/${OUTPUT_PATH#$ROOT_DIR/}"
    for ((i = 0; i < ${#docker_args[@]}; i++)); do
      case "${docker_args[$i]}" in
        --report-path)
          if (( i + 1 < ${#docker_args[@]} )); then
            docker_args[$((i + 1))]="$docker_path"
          fi
          ;;
        --report-path=*)
          docker_args[$i]="--report-path=$docker_path"
          ;;
      esac
    done
    docker run --rm -v "$ROOT_DIR:/repo" zricethezav/gitleaks:latest \
      detect --source=/repo --log-opts="--all" "${docker_args[@]}"
  else
    echo "gitleaks is not installed and Docker is unavailable. Install gitleaks from https://github.com/gitleaks/gitleaks/releases." >&2
    exit 1
  fi
}

run_gitleaks

echo "Gitleaks report written to $OUTPUT_PATH"
