#!/usr/bin/env bash
set -euo pipefail

mkdir -p "$PNPM_STORE_PATH"
pnpm config set store-dir "$PNPM_STORE_PATH"
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
