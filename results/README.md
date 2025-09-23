# CodexBridge Plan Results

The CodexBridge watcher records the outcome of each processed plan inside this directory.
Files follow the naming convention `ISO_TIMESTAMP__PLAN_NAME__STATUS.json` and include a
summary of macro paths, test execution results, and failure diagnostics. GPT planners can
use these artefacts to adjust subsequent plans and avoid repeating errors.
