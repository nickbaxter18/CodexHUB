# CodexHUB Agent Guidelines

## Repository-wide Conventions

- Prefer async file watchers (`watchfiles`) for long-running automation instead of manual polling loops.
- Keep configuration in version control; new settings should be documented in `README.md` and `.env.example`.
- Python linting and formatting are handled by Ruff (`python -m ruff check|format`).
- Use `pnpm` for all JavaScript/TypeScript dependency management.
- Large knowledge artefacts belong under `data/knowledge/` and should be excluded from commits by default.

## Pull Request Checklist

1. Run the relevant formatters and linters (`pnpm run lint`, `python -m ruff check`, and the project test suites).
2. Update documentation when behaviour or configuration changes.
3. Keep commits focused; avoid committing generated artefacts or vendor directories.
