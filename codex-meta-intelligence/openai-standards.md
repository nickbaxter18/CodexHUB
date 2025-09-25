# OpenAI Standards Integration

## Compliance Goals

- Respect AGENTS.md hierarchy and merge order to ensure deterministic behaviour across Codex and Cursor environments.
- Enforce OpenAI safety guidance covering privacy, intellectual property, fairness and transparency.
- Provide auditable evidence (logs, citations, test results) for each automated change.

## Implementation Summary

- `src/agent/reader.ts` merges AGENTS.md files according to scope rules, caching results per directory and verifying command requirements.
- `src/openai-standards/guidelines.ts` exposes helper functions to validate compliance, track executed checks and enforce footnote generation.
- Build orchestration ensures linting, testing and typechecking before stage promotion, matching OpenAI trust and safety expectations.

## Operator Responsibilities

- Maintain AGENTS.md changelog entries for major rule updates.
- Validate that any external assets or dependencies respect licensing constraints.
- Review compliance reports generated during macro runs and escalate anomalies.

## Future Enhancements

Stage 2 introduces automated cross-checks with OpenAI policy APIs and Stage 3 adds interactive dashboards summarising compliance metrics.
