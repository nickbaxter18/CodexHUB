.PHONY: install install-python dev lint lint-python typecheck test test-python clean docker-build docker-run status format format-python security cursor-status quality quality-node quality-python quality-docs

install:
pnpm install --frozen-lockfile

install-python:
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt

dev:
pnpm run dev

lint:
pnpm run lint

lint-python:
python -m flake8 src agents meta_agent macro_system qa_engine

typecheck:
python -m mypy

format:
pnpm run format
python -m black src agents meta_agent macro_system qa_engine scripts
python -m isort src agents meta_agent macro_system qa_engine scripts

security:
pnpm run audit:js
python -m pip_audit -r requirements.txt

cursor-status:
python scripts/codex_status.py --json

test:
pnpm test

test-python:
    python -m pytest

quality:
    python -m src.performance.cli quality

quality-node:
    python -m src.performance.cli node-quality

quality-python:
    python -m src.performance.cli python-quality

quality-docs:
    python -m src.performance.cli docs-quality

clean:
    rm -rf node_modules .pytest_cache .mypy_cache coverage results/performance
find . -type d -name "__pycache__" -prune -exec rm -rf {} +

docker-build:
docker build -t codexhub .

docker-run:
docker run -p 4000:4000 codexhub

status:
pnpm run codex:status
