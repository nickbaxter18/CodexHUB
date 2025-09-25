#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(git rev-parse --show-toplevel)
OUTPUT_DIR="$ROOT_DIR/.context-bundle"
CREATE_ARCHIVE=false
ARCHIVE_PATH=""

POSITIONAL_SET=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --archive)
      CREATE_ARCHIVE=true
      shift
      ;;
    --archive-path)
      CREATE_ARCHIVE=true
      ARCHIVE_PATH=${2:-}
      shift 2 || true
      ;;
    --archive-path=*)
      CREATE_ARCHIVE=true
      ARCHIVE_PATH="${1#*=}"
      shift
      ;;
    *)
      if [[ "$POSITIONAL_SET" = false ]]; then
        OUTPUT_DIR="$1"
        POSITIONAL_SET=true
        shift
      else
        echo "Unexpected argument: $1" >&2
        exit 1
      fi
      ;;
  esac
done

if [[ -z "$ARCHIVE_PATH" && "$CREATE_ARCHIVE" = true ]]; then
  ARCHIVE_PATH="$OUTPUT_DIR.tar.gz"
fi

CONTEXT_PATHS=(
  "AGENT.md"
  "AGENTS.md"
  "ARCHITECTURE.md"
  "README.md"
  "SECURITY.md"
  "docs/context"
  "docs/architecture.md"
  "docs/setup.md"
  "docs/usage.md"
  "docs/api.md"
  "docs/GOVERNANCE.md"
  "cursor/CODEX_CURSOR_MANDATE.md"
  "cursor/CURSOR_INTEGRATION_INSTRUCTIONS.md"
  "cursor/CURSOR_INTEGRATION_README.md"
  "cursor/CURSOR_INTEGRATION_STATUS.md"
  "cursor/CURSOR_INTEGRATION_COMPLETE_GUIDE.md"
  "scripts/fetch-context.sh"
  "scripts/scan-secrets.sh"
  "scripts/auto_setup_cursor.py"
  "package.json"
  "pnpm-workspace.yaml"
  "turbo.json"
  ".pre-commit-config.yaml"
  ".husky"
)

if [[ ! "$OUTPUT_DIR" = /* ]]; then
  OUTPUT_DIR="$ROOT_DIR/${OUTPUT_DIR#./}"
fi

if [[ -n "$ARCHIVE_PATH" && ! "$ARCHIVE_PATH" = /* ]]; then
  ARCHIVE_PATH="$ROOT_DIR/${ARCHIVE_PATH#./}"
fi

rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

MANIFEST="$OUTPUT_DIR/context-manifest.json"
{
  echo '{'
  echo '  "generatedAt": '"\"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\""','
  echo '  "root": '"\"$ROOT_DIR\""','
  echo '  "outputDir": '"\"$OUTPUT_DIR\""','
  if [[ "$CREATE_ARCHIVE" = true ]]; then
    echo '  "archivePath": '"\"$ARCHIVE_PATH\""','
  fi
  echo '  "files": ['
} >"$MANIFEST"

first_entry=true
for path in "${CONTEXT_PATHS[@]}"; do
  SOURCE_PATH="$ROOT_DIR/$path"
  if [[ ! -e "$SOURCE_PATH" ]]; then
    echo "[fetch-context] Skipping missing path: $path" >&2
    continue
  fi

  DEST_PATH="$OUTPUT_DIR/$path"
  mkdir -p "$(dirname "$DEST_PATH")"
  cp -R "$SOURCE_PATH" "$DEST_PATH"

  if [[ "$first_entry" = true ]]; then
    first_entry=false
  else
    echo ',' >>"$MANIFEST"
  fi

  if [[ -d "$SOURCE_PATH" ]]; then
    ENTRY_TYPE="directory"
    ENTRY_SIZE=$(du -sk "$SOURCE_PATH" | awk '{print $1 * 1024}')
  else
    ENTRY_TYPE="file"
    ENTRY_SIZE=$(stat -c%s "$SOURCE_PATH")
  fi

  printf '    {"path": "%s", "type": "%s", "size": %s}' \
    "$path" "$ENTRY_TYPE" "$ENTRY_SIZE" >>"$MANIFEST"
done

echo '' >>"$MANIFEST"
echo '  ]' >>"$MANIFEST"
echo '}' >>"$MANIFEST"

if [[ "$CREATE_ARCHIVE" = true ]]; then
  mkdir -p "$(dirname "$ARCHIVE_PATH")"
  tar -czf "$ARCHIVE_PATH" -C "$OUTPUT_DIR" .
  echo "Context archive created at: $ARCHIVE_PATH"
fi

echo "Context bundle created at: $OUTPUT_DIR"
echo "Manifest written to: $MANIFEST"
