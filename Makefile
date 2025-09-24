.PHONY: install install-python dev lint lint-python typecheck test test-python clean docker-build docker-run status

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

test:
pnpm test

test-python:
python -m pytest

clean:
rm -rf node_modules .pytest_cache .mypy_cache coverage results/performance
find . -type d -name "__pycache__" -prune -exec rm -rf {} +

docker-build:
docker build -t codexhub .

docker-run:
docker run -p 4000:4000 codexhub

status:
pnpm run codex:status
