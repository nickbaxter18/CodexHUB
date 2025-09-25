#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(git rev-parse --show-toplevel)
OUTPUT_DIR=${1:-"$ROOT_DIR/.context-bundle"}

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
  "scripts/fetch-context.sh"
  "scripts/scan-secrets.sh"
  "scripts/auto_setup_cursor.py"
  "package.json"
  "pnpm-workspace.yaml"
  "turbo.json"
  ".pre-commit-config.yaml"
  ".husky"
)

rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

MANIFEST="$OUTPUT_DIR/context-manifest.json"
{
  echo '{'
  echo '  "generatedAt": '"\"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\""','
  echo '  "root": '"\"$ROOT_DIR\""','
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

echo "Context bundle created at: $OUTPUT_DIR"
echo "Manifest written to: $MANIFEST"
