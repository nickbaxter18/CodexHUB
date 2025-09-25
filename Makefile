.PHONY: install install-python dev lint lint-python typecheck test test-python clean docker-build docker-run status format format-python security cursor-status quality quality-node quality-python quality-docs

install:
	pnpm install --frozen-lockfile

install-python:
	python -m pip install -r requirements.txt
	python -m pip install -r requirements-dev.txt

bootstrap:
	pnpm run setup

dev:
	pnpm run dev

lint:
	pnpm run lint

lint-python:
        python -m ruff check src packages/automation scripts agents meta_agent macro_system qa_engine

typecheck:
	python -m mypy

format:
        pnpm run format
        python -m ruff format src packages/automation scripts agents meta_agent macro_system qa_engine

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
        python -m src.performance.cli quality || { \
        pnpm run lint && \
        python -m ruff check src packages/automation scripts agents meta_agent macro_system qa_engine && \
        python -m pytest && \
        python -m mypy; \
        }

quality-node:
	python -m src.performance.cli node-quality || pnpm run lint

quality-python:
        python -m src.performance.cli python-quality || { \
        python -m ruff check src packages/automation scripts agents meta_agent macro_system qa_engine && \
        python -m pytest && \
        python -m mypy; \
        }

quality-docs:
	python -m src.performance.cli docs-quality || pnpm run lint:md

clean:
	rm -rf node_modules .pytest_cache .mypy_cache coverage results/performance
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +

docker-build:
	docker build -t codexhub .

docker-run:
	docker run -p 4000:4000 codexhub

status:
	pnpm run codex:status
