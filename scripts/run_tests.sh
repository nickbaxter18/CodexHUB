#!/usr/bin/env bash
set -euo pipefail

pnpm lint
pnpm check-format
pnpm test
python -m pytest
