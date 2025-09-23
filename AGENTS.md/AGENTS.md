## Codex Instructions

- 🧠 Always use functional React components. No class-based components allowed.
- 🎨 Use Tailwind CSS only — no inline styles or external CSS modules.
- 🧪 Every new utility function in `/utils/` must be accompanied by Jest tests with 100% coverage.
- 🧼 Ensure all code passes ESLint and Prettier before commit.
- 🧾 Follow naming conventions:
  - `camelCase` for variables/functions
  - `PascalCase` for components
- 🧱 New files must follow project structure (`/src`, `/api`, `/schemas`, etc.).
- 🧪 Run all tests using: `npm test`.
- 🔐 Never hardcode secrets or keys. Use `process.env` or secure vaults.
- 🧭 Architecture changes or PRs that touch more than 2 modules require `QA` agent review.

Codex agents should refer to these instructions before generating, refactoring, or completing tasks. Human overrides are permitted with justification.