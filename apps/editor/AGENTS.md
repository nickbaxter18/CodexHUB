## Codex Instructions

### 🚨 **MANDATORY CURSOR IDE INTEGRATION**
- 🎯 **ALL CODING TASKS MUST USE CURSOR IDE** - No exceptions, no bypasses
- 🔧 **Start every task with**: `python scripts/codex_cursor_startup.py`
- 🧠 **Query knowledge systems**: Use `src/knowledge/auto_loader.py` and `src/knowledge/brain_blocks_integration.py`
- 📱 **Use mobile control**: Use `src/mobile/mobile_app.py` for goal management
- 🎯 **Select correct Cursor agent**: FRONTEND for .tsx/.jsx, BACKEND for .py, KNOWLEDGE for .md, QA for tests
- 🚨 **Enforce Cursor usage**: Use `@require_cursor_agent(agent_type="...")` decorator
- ✅ **Validate compliance**: Ensure 100% Cursor usage before any coding

### 🎨 **Frontend Development (React/TypeScript)**
- 🧠 Always use functional React components. No class-based components allowed.
- 🎨 Use Tailwind CSS only — no inline styles or external CSS modules.
- 🎯 **Use Cursor FRONTEND agent** for all React/TypeScript development
- 🔧 **Start with**: `@require_cursor_agent(agent_type="FRONTEND")`

### 🐍 **Backend Development (Python)**
- 🎯 **Use Cursor BACKEND agent** for all Python development
- 🔧 **Start with**: `@require_cursor_agent(agent_type="BACKEND")`
- 🧪 Every new utility function in `/utils/` must be accompanied by Jest tests with 100% coverage.

### 📚 **Knowledge Management**
- 🎯 **Use Cursor KNOWLEDGE agent** for all documentation and knowledge tasks
- 🔧 **Start with**: `@require_cursor_agent(agent_type="KNOWLEDGE")`
- 📖 **Query knowledge systems**: Use `src/knowledge/auto_loader.py` for NDJSON data
- 🧠 **Query brain blocks**: Use `src/knowledge/brain_blocks_integration.py` for context

### 🧪 **Quality Assurance**
- 🎯 **Use Cursor QA agent** for all testing and quality tasks
- 🔧 **Start with**: `@require_cursor_agent(agent_type="QA")`
- 🧼 Ensure all code passes ESLint and Prettier before commit.

### 🏗️ **Architecture & CI/CD**
- 🎯 **Use Cursor ARCHITECT agent** for architecture decisions
- 🎯 **Use Cursor CICD agent** for CI/CD and deployment tasks
- 🔧 **Start with**: `@require_cursor_agent(agent_type="ARCHITECT")` or `@require_cursor_agent(agent_type="CICD")`

### 🧾 **Naming Conventions**
- `camelCase` for variables/functions
- `PascalCase` for components
- 🧱 New files must follow project structure (`/src`, `/api`, `/schemas`, etc.).

### 🧪 **Testing & Quality**
- 🧪 Run all tests using: `npm test` or `pnpm test`
- 🔐 Never hardcode secrets or keys. Use `process.env` or secure vaults.
- 🧭 Architecture changes or PRs that touch more than 2 modules require `QA` agent review.

### 🚀 **Cursor Integration Commands**
```bash
# Setup and Configuration
pnpm run cursor:setup        # Setup Cursor integration
pnpm run cursor:start        # Start Cursor integration
pnpm run cursor:validate     # Validate Cursor integration

# Testing and Enforcement
pnpm run cursor:test         # Test Cursor integration
pnpm run cursor:enforce      # Enforce Cursor usage
pnpm run cursor:auto         # Auto-setup Cursor integration
```

### 🎯 **Agent Selection Protocol**
```python
# MANDATORY: Select correct agent based on file type
def select_cursor_agent(file_path: str) -> str:
    if file_path.endswith(('.tsx', '.jsx', '.ts', '.js')):
        return "FRONTEND"
    elif file_path.endswith(('.py', '.pyx')):
        return "BACKEND"
    elif file_path.endswith(('.md', '.rst', '.txt')):
        return "KNOWLEDGE"
    elif file_path.endswith(('.yml', '.yaml', '.json')):
        return "CICD"
    elif 'test' in file_path.lower():
        return "QA"
    else:
        return "ARCHITECT"
```

### 🚨 **CRITICAL REQUIREMENTS**
- ❌ **NEVER** start coding without Cursor integration active
- ❌ **NEVER** use any agent other than Cursor agents
- ❌ **NEVER** skip knowledge system queries
- ❌ **NEVER** skip mobile control usage
- ❌ **NEVER** skip brain blocks integration
- ✅ **ALWAYS** start with Cursor integration
- ✅ **ALWAYS** query knowledge systems
- ✅ **ALWAYS** use mobile control
- ✅ **ALWAYS** query brain blocks
- ✅ **ALWAYS** select correct Cursor agent
- ✅ **ALWAYS** enforce Cursor usage
- ✅ **ALWAYS** validate compliance

Codex agents should refer to these instructions before generating, refactoring, or completing tasks. Human overrides are permitted with justification.