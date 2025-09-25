#!/usr/bin/env bash
set -euo pipefail

pnpm exec prettier --write "**/*.{js,ts,tsx,json,md,yaml,yml,css,scss}"
pnpm exec stylelint "**/*.{css,scss}" --fix
pnpm exec markdownlint "**/*.md" --fix
python -m yamllint .
python -m ruff format .
python -m ruff check --fix .
