# Command Prompts for Codex Automation Runner

This reference document describes the automated workflow that every Codex task should follow when contributing to the Probabilistic Multi-Agent Runner. The first section lists the high-level commands that the automation runner executes to detect the current build stage and to advance the project. The remaining sections reproduce the full three-stage blueprint so that each stage can be cross-checked during audits.

## Automated Build Commands

The following steps guide the Codex automation in orchestrating the build process. They are presented as plain text so that the automation can parse them and run the appropriate actions.

1. **Ensure base project folder**
   - Check if a directory named `U-DIG-IT` exists in the repository root. If not, create it (`mkdir -p U-DIG-IT/runner_project`).
   - Navigate into `U-DIG-IT`. Inside it, ensure a subdirectory called `runner_project` exists for the runner source code. This separation keeps the runner files organised.
2. **Stage detection**
   - Determine which build stage (1, 2, or 3) the project is currently in by inspecting the contents of `runner_project/src/`:
     - If most modules (for example `knowledge/graph.py`, `decision/mdp.py`, `decision/simulation.py`, `execution/cursor_adapter.py`) are empty stubs that raise `NotImplementedError`, the project is in Stage 1.
     - If the knowledge, decision, and cursor modules contain substantive logic but there is no `ui/` directory or `plugins/` loader, the project is in Stage 2.
     - If a `ui/` directory, `templates/` directory, and `plugins/` loader exist and are implemented, the project is in Stage 3.
   - Optionally maintain a simple marker file (`.stage_complete`) in the root of `runner_project` recording the last completed stage (for example `stage1_complete` after finishing Stage 1).
3. **Execute next build tasks**
   - **If Stage 1 (prototype not yet implemented)**
     - Create the file and directory structure described in the Stage 1 plan below.
     - Implement the minimal modules: `config.py`, `types.py`, `errors.py`, logging, input validation, concurrency helper, command runner, Git actions, task manager, orchestrator skeleton, and FastAPI server with basic endpoints.
     - Stub out knowledge, decision, collective, and ethics agents by creating the files with placeholder classes that raise `NotImplementedError`.
     - Write basic tests for command execution, task management, and API endpoints. Use `pytest` to run them and ensure they pass.
   - **If Stage 2 (core prototype completed, intelligence missing)**
     - Implement knowledge graph loading, retrieval, and updates using NDJSON data; update `knowledge/graph.py` and `knowledge/retrieval.py`.
     - Implement decision logic: MDP value iteration, bandit strategies, Bayesian updates, Monte Carlo simulations, and Markov chains (`decision/mdp.py`, `decision/bayes.py`, `decision/simulation.py`).
     - Implement the knowledge, decision, collective, and ethics agents to call these modules and enforce fairness metrics.
     - Fill in `cursor_adapter.py` to wrap the Cursor CLI for code suggestions; add caching and error handling.
     - Extend the orchestrator to coordinate knowledge retrieval, decision selection, and ethics checks before executing commands.
     - Expand the API to include endpoints for knowledge queries, simulations, cursor operations, and fairness assessments.
     - Add tests for all new modules and update existing tests to cover edge cases and performance scenarios.
   - **If Stage 3 (intelligence present, needs polish)**
     - Implement user interface modules (`ui/dashboard.py` and HTML templates) to visualise knowledge graphs, decision trees, simulations, and fairness metrics.
     - Add a plugin system (`utils/plugin_loader.py` and `plugins/__init__.py`) to discover and load new agents or commands at runtime.
     - Extend collective and ethics agents for global intelligence sharing and advanced fairness metrics.
     - Add resilience features (health checks, auto-restart) via an `observer.py`.
     - Enhance the orchestrator and API to handle UI endpoints, plugin management, and health reporting.
     - Write tests for the UI, plugin loader, resilience routines, and update existing tests for cross-stage integration.
4. **Validate with tests**
   - After each implementation step, run the test suite (`pytest`) inside `runner_project/tests`. Fix any failing tests before proceeding to the next stage.
   - Run linting and formatting tools (for example pre-commit, Prettier, ESLint, and Black) to ensure code quality.
5. **Iterate**
   - Each time the blueprint is pasted into Codex, the automation should repeat these commands: re-detect stage, implement outstanding tasks, run tests, and linting. Continue until Stage 3 tasks are completed and all tests pass.
   - Once the project reaches Stage 3 completion, begin performance tuning, aesthetic refinement, and optional future hooks as described in the final section.

---

## Probabilistic Multi-Agent Runner: Three-Phase Build Plan

This document takes the full blueprint for the Probabilistic Multi-Agent Local Runner (with Cursor CLI integration) and breaks it into three sequential building stages. Each stage follows the same structural layout as the original blueprint—covering intent, file structure, variant analysis, detailed file outlines, security considerations, performance, test coverage, and metadata—but scopes the work according to development maturity. The goal is to guide an efficient and pain-free progression from concept to production, ensuring that core functionality is solid before system refinement and final polish.

### Stage 1: Core Functionality

1. **Canonical Intent & Specification**

- **Component Name**: Core Runner Prototype
- **Functional Goals**
  1. Secure Local Command Execution – Provide a minimal yet robust interface for safely running shell commands on the user’s machine. Commands must be whitelisted and sanitized; the system must use subprocess with shell=False to avoid injection. Timeouts and working-directory confinement apply. Git commands (fetch, merge, commit, push) and formatting tools (Prettier, ESLint, Black) are supported via wrappers, but advanced probabilistic reasoning is deferred to later stages.
  2. Task Queue & Basic Orchestration – Implement a simple asynchronous task manager that can run multiple commands concurrently without blocking. A minimal orchestrator dispatches requests to the command runner and records statuses; knowledge, decision and ethics agents are stubbed out with no-op logic.
  3. REST API & CLI Skeleton – Expose endpoints to schedule a command or Git action, check task status, and fetch logs. Provide a command-line interface (src/main.py) to trigger tasks from the terminal.
  4. Configuration & Logging – Centralize configuration (paths, timeouts, allowed commands) and set up structured logging. Ensure environment variables are read and validated at startup.
  5. Unit & Integration Tests – Deliver basic test coverage for command execution, configuration loading, task management, and API endpoints. Tests focus on happy paths, input validation, and error cases.
- **Non-Goals**
  - Probabilistic reasoning, Monte Carlo simulations, collective intelligence, and ethics filtering are not implemented yet; these will be added in Stages 2 and 3. Only stub classes exist to satisfy the module layout.
  - The runner does not support external network calls or remote crowdsourcing data sources. All data remains local.
- **Stakeholders**
  - Primary user – A developer or agent orchestrator who wants to automate local repository tasks and command execution securely.
  - Core System Designer – The engineer implementing the architecture, ensuring that future stages can plug in additional intelligence.
- **Rationale & Constraints**
  - Delivering a minimal prototype quickly allows verification of the asynchronous architecture, security boundaries, and integration with Git and formatting tools. It sets the foundation for advanced features in later stages. Constraints for Stage 1 mirror those of the full system but with simplified scope: runs locally with Python ≥ 3.9; must be cross-platform; commands are whitelisted; expected load is low to moderate (1–2 tasks per minute); network disabled except for Git operations.

2. **Modular File & Directory Plan (Stage 1)**

```
runner_project/
├── README.md                   # Overview, setup instructions, Stage 1 scope.
├── pyproject.toml              # Basic dependencies: fastapi, pydantic, pytest; excludes heavy probabilistic libs.
├── src/
│   ├── main.py                 # Entry point: parses CLI args and starts API server or CLI mode.
│   ├── config.py               # Central configuration.
│   ├── types.py                # Dataclasses for tasks and requests/responses.
│   ├── errors.py               # Custom exception definitions.
│   ├── utils/
│   │   ├── logger.py          # Structured logging utilities.
│   │   ├── validators.py      # Input sanitization (command names, file paths).
│   │   ├── concurrency.py     # Minimal async task queue; thread pool wrapper.
│   ├── agents/
│   │   ├── base.py            # Abstract Agent class (placeholder for now).
│   │   ├── knowledge_agent.py # Stub returning empty context.
│   │   ├── decision_agent.py  # Stub selecting a no-op action.
│   │   ├── collective_agent.py# Stub returning no external inputs.
│   │   ├── ethics_agent.py    # Stub always approving actions.
│   │   ├── orchestrator.py    # Coordinates command execution via task manager; invokes stub agents.
│   ├── execution/
│   │   ├── command_runner.py   # Implements secure command execution.
│   │   ├── git_actions.py      # Implements basic Git wrappers.
│   │   ├── task_manager.py     # Manages tasks, statuses, and logs.
│   │   ├── cursor_adapter.py   # Stub that raises a NotImplemented error (no cursor integration yet).
│   ├── api/
│   │   ├── server.py           # FastAPI server exposing `/run-command`, `/git-action`, `/tasks` endpoints.
│   │   ├── schemas.py          # Pydantic models for request/response.
│   └── __init__.py
├── tests/
│   ├── test_command_runner.py # Tests command execution (allowed/disallowed, timeout).
│   ├── test_git_actions.py    # Tests basic Git operations.
│   ├── test_task_manager.py   # Tests creating and retrieving tasks.
│   ├── test_api_endpoints.py  # Tests REST endpoints.
│   └── … (stubs for unimplemented modules)
├── .husky/
│   └── pre-commit              # Runs prettier/eslint/ruff using the runner’s command execution.
└── .gitignore
```

Modules such as knowledge/graph.py, decision/mdp.py, decision/bayes.py, decision/simulation.py and execution/cursor_adapter.py are included as empty files or simple stubs that raise NotImplementedError. Tests referencing these modules merely assert that their presence is acknowledged. This ensures the file layout remains stable and Stage 2 can fill in the logic.

3. **Variant Analysis & Decision Making (Stage 1)**

We still compare two design variants as in the full blueprint to justify early architectural choices:

- **Variant A (Synchronous Prototype)**
  - All commands and tasks run sequentially.
  - API requests block until completion.
  - Pros: Simpler code; easier debugging. Cons: The system becomes unresponsive if any command hangs; lacks concurrency needed for real workloads.
- **Variant B (Asynchronous Prototype)**
  - Commands run in separate threads using concurrency.run_in_thread() and tasks are scheduled via an asyncio queue.
  - API returns immediately with a task ID; results can be polled.
  - Pros: More responsive; tasks do not block each other. Cons: Slightly more complex; requires careful error handling.
- **Chosen for Stage 1**: The asynchronous prototype (Variant B) is adopted to lay the groundwork for Stage 2 and Stage 3. Even though initial workloads are small, concurrency is critical for scaling to simultaneous Git operations and formatting tasks.

4. **File Structure & Contents Format (Stage 1)**

In this stage, files follow the same section header structure but only implement the minimal functionality described above. For brevity, we outline the key files that contain substantive logic; files with stubs or placeholders note their deferred status.

- **File: src/command_runner.py**
  - SECTION 1: Header & Purpose – Executes shell commands securely (shell=False) with sanitized arguments and whitelisting; enforces working-directory confinement and timeouts; captures stdout/stderr and returns a CommandResult.
  - SECTION 2: Imports / Dependencies – subprocess, asyncio, typing, src/utils/validators, src/errors.
  - SECTION 3: Types, Interfaces, Contracts, Schema – Defines CommandRequest and CommandResult dataclasses.
  - SECTION 4: Core Logic / Implementation – Implements async run_command(request: CommandRequest) -> TaskID using subprocess.Popen via a thread pool.
  - SECTION 5: Error & Edge Case Handling – Raises CommandError for disallowed commands; kills processes on timeout.
  - SECTION 6: Performance / Resource Considerations – Uses concurrency.run_in_thread() to offload blocking calls.
  - SECTION 7: Exports / Public API – Exposes run_command() to orchestrator.
- **File: src/git_actions.py**
  - SECTION 1: Header & Purpose – Implements basic Git commands (fetch, merge, commit, push) via subprocess.
  - SECTION 2: Imports / Dependencies – subprocess, asyncio, src/utils/validators, src/errors.
  - SECTION 3: Types, Interfaces, Contracts, Schema – Defines GitActionRequest and GitActionResult.
  - SECTION 4: Core Logic / Implementation – Uses sanitized arguments to call Git; returns parsed output.
  - SECTION 5: Error & Edge Case Handling – Handles merge conflicts by setting status to pending and capturing conflict details.
  - SECTION 6: Performance / Resource Considerations – Offloads to threads and imposes a concurrency limit on Git operations.
  - SECTION 7: Exports / Public API – Exposes run_git_action().
- **File: src/agents/orchestrator.py**
  - SECTION 1: Header & Purpose – Provides async schedule(request: CommandRequest|GitActionRequest) -> TaskID; invokes stub agents; delegates to task_manager.create_task().
  - SECTION 2: Imports / Dependencies – asyncio, src/agents/…, src/execution/task_manager.
  - SECTION 3: Types, Interfaces, Contracts, Schema – Accepts requests and returns task IDs.
  - SECTION 4: Core Logic / Implementation – Basic dispatch: if request is a command, call run_command; if Git action, call run_git_action.
  - SECTION 5: Error & Edge Case Handling – Catches exceptions and logs them; returns TaskID with error status if immediate failure occurs.
  - SECTION 6: Performance / Resource Considerations – Minimal overhead; concurrency handled by concurrency.py.
  - SECTION 7: Exports / Public API – Exposes Orchestrator class.
- **File: src/api/server.py**
  - SECTION 1: Header & Purpose – Implements FastAPI server with endpoints /run-command, /git-action, /tasks/{id}.
  - SECTION 2: Imports / Dependencies – fastapi, pydantic, src/api/schemas, src/agents/orchestrator, src/execution/task_manager.
  - SECTION 3: Types, Interfaces, Contracts, Schema – Uses Pydantic models for requests; returns TaskResponse with id and status.
  - SECTION 4: Core Logic / Implementation – Calls orchestrator.schedule() and returns a task ID; provides get_task(id) endpoint.
  - SECTION 5: Error & Edge Case Handling – Returns HTTP 400 on invalid input; returns detailed error body.
  - SECTION 6: Performance / Resource Considerations – Ensures all endpoints are async; uses streaming responses for logs if necessary.
  - SECTION 7: Exports / Public API – Exposes app for deployment.

Other files (e.g. src/utils/logger.py, src/utils/concurrency.py, src/config.py) follow the section format but implement minimal logging, concurrency and configuration logic appropriate for Stage 1.

5. **Security, Risk & Threat Disclosure (Stage 1)**

Stage 1 emphasises secure execution. All command inputs must be sanitized; only whitelisted commands run. Path traversal is prohibited by resolving absolute paths and ensuring they reside within the project directory. The system does not yet implement advanced ethics checks or fairness metrics, but it logs all requests and results for auditing. Since the knowledge and decision layers are stubs, no data is processed that could cause bias or privacy violations.

6. **Performance & Scalability (Stage 1)**

Although Stage 1 handles low load, it sets up the asynchronous infrastructure. The concurrency helper uses a thread pool sized to CPU cores and sets per-command timeouts (default 60 s). There is no caching or graph memory overhead yet. The focus is on preventing blocking calls from stalling the API.

7. **Test Intelligence & Coverage (Stage 1)**

Tests cover command execution, Git actions, task manager, and API endpoints. Tests for knowledge, decision, collective and ethics agents are placeholders that simply assert the stubs exist and raise NotImplementedError when invoked.

8. **Stage 1 Summary**

Stage 1 delivers a working asynchronous prototype of the runner. It supports secure command execution, basic Git operations, task scheduling, and an API/CLI interface. The architecture is deliberately modular, matching the final file layout, so that Stage 2 can populate intelligence and refinement modules without structural changes. Extensive tests ensure that these core features operate correctly and safely.

9. **Future Hooks for Stage 2**

Implement knowledge graph loading, decision logic, cursor integration, ethics agents, and expanded tests.

10. **Metadata & Compliance (Stage 1)**

```
{
  "task_id": "codex-compiler-20250924-stage1",
  "feature": "Core Runner Prototype",
  "mode": "production",
  "variants_compared": true,
  "lint_passed": true,
  "test_coverage": "nominal+edge+negative+schema",
  "risk_surface_declared": true,
  "assumptions_listed": true
}
```

### Stage 2: System Refinement

1. **Canonical Intent & Specification**

- **Component Name**: Refined Probabilistic Multi-Agent Runner
- **Functional Goals**
  1. Knowledge Graph & Retrieval – Implement the knowledge subsystem: load NDJSON brain blocks into a directed Bayesian network; provide queries to retrieve relevant variables and update beliefs. The Knowledge Agent uses this graph to inform decisions.
  2. Decision Engine & Simulations – Implement Markov Decision Processes, multi-armed bandits and Bayesian updating. Add Monte Carlo and Markov simulation modules for forecasting. The Decision Agent uses these tools to recommend actions given current state and goals.
  3. Ethics & Collective Agents – Implement fairness metrics, governance constraints and external intelligence aggregation. The Ethics Agent evaluates proposed actions; the Collective Agent collects crowd or external data and merges it with local beliefs.
  4. Cursor CLI Integration & Code Ops – Fill in the cursor_adapter to call the installed cursor CLI for code generation or refactoring tasks. Provide commands such as runner cursor.run to modify code files safely.
  5. Expanded API & Agent Coordination – Extend REST endpoints to handle knowledge queries, simulation requests, and ethics checks. The orchestrator now coordinates knowledge retrieval, decision selection, ethical review and execution.
  6. Advanced Logging & Error Handling – Enhance logging to include priors and posteriors, fairness metrics, simulation results and decision explanations. Add granular error classes for knowledge, decision and ethics modules.
- **Non-Goals**
  - Deep UI/UX enhancements or aesthetic elevation (reserved for Stage 3).
  - Full global intelligence integration or dynamic plugin loading (these come later).
- **Stakeholders**
  - Data Scientists & Architects – Validate that probabilistic models are implemented correctly and produce useful recommendations.
  - Ethics & Compliance Officers – Ensure fairness metrics and governance rules are enforced.
  - Developers – Use cursor integration and decision support to augment coding workflows.
- **Rationale & Constraints**
  - Stage 2 brings the intelligence into the runner. It leverages the asynchronous architecture from Stage 1 while populating knowledge and decision modules. Constraints include increased computational requirements (Monte Carlo simulations), potential network calls for collective intelligence, and added complexity in managing dependencies (e.g. numpy, networkx, scipy). Performance must remain acceptable: tasks should still return promptly or run asynchronously; heavy simulations must not starve lighter tasks.

2. **Modular File & Directory Plan (Stage 2)**

```
runner_project/
├── src/
│   ├── knowledge/
│   │   ├── graph.py            # Now implemented: loads NDJSON to create a Bayesian network and supports queries/updates.
│   │   ├── retrieval.py        # Implements search and update functions using the graph.
│   ├── decision/
│   │   ├── mdp.py              # Implements value and policy iteration, bandit strategies.
│   │   ├── bayes.py            # Implements Bayesian updating functions (Beta, Dirichlet, etc.).
│   │   ├── simulation.py       # Provides Monte Carlo and Markov chain simulations.
│   ├── agents/
│   │   ├── knowledge_agent.py # Uses retrieval functions to update the graph; returns relevant context.
│   │   ├── decision_agent.py  # Uses MDP/bandit and Bayesian modules to select actions.
│   │   ├── collective_agent.py# Integrates external data sources or crowd inputs.
│   │   ├── ethics_agent.py    # Computes fairness metrics and blocks harmful actions.
│   │   ├── orchestrator.py    # Enhanced: orchestrates knowledge retrieval → decision → ethics → execution.
│   ├── execution/
│   │   ├── cursor_adapter.py   # Fully implemented wrapper around Cursor CLI.
│   │   ├── git_actions.py      # Extended to handle rebase and conflict resolution logic.
│   ├── utils/
│   │   ├── cache.py           # (New) Simple in-memory caching for knowledge queries and cursor results.
│   ├── api/
│   │   ├── server.py           # Adds new endpoints: `/knowledge/query`, `/simulate`, `/cursor-run`.
│   │   ├── schemas.py          # Adds models for knowledge and simulation requests/responses.
│   ├── config.py               # Adds settings for simulation parameters, fairness thresholds, external APIs.
│   ├── errors.py               # Adds `KnowledgeError`, `DecisionError`, `EthicsError`.
│   ├── utils/concurrency.py    # Refined: supports CPU vs I/O thread pools and cancellation.
│   └── … (unchanged)
├── tests/
│   ├── test_knowledge_graph.py # Tests loading and querying the Bayesian network.
│   ├── test_decision_agent.py  # Tests MDP, bandit and Bayesian updates.
│   ├── test_simulation.py      # Tests Monte Carlo and Markov simulations.
│   ├── test_cursor_adapter.py  # Tests integration with cursor CLI (mocked).
│   ├── test_ethics_agent.py    # Tests fairness checks and flagged actions.
│   ├── test_api_knowledge.py   # Tests new API endpoints.
│   ├── … (previous tests updated)
└── README.md                   # Extended documentation describing new features.
```

3. **Variant Analysis & Decision Making (Stage 2)**

- **Variant A: In-Memory Bayesian Graph & Eager Simulations**
  - The knowledge graph is built fully in memory using networkx. All simulations and decision calculations run in the main application process. The collective agent uses local heuristics rather than connecting to external data sources.
  - Pros: Simpler deployment, no external dependencies; faster memory access for small graphs.
  - Cons: Scalability limited by available RAM; large graphs or long simulations block other tasks; no global intelligence.
- **Variant B: Modular Probabilistic Engine & External Data (Chosen)**
  - The knowledge graph is loaded in a dedicated module, with caching and lazy loading. Monte Carlo simulations run in separate processes when CPU-heavy. External data retrieval happens via asynchronous HTTP calls with timeouts. Data from global intelligence sources is weighted and combined with local beliefs. A fairness library is used by the ethics agent.
  - Pros: More scalable; offloads heavy computations; integrates up-to-date global signals; fairness metrics come from established libraries.
  - Cons: Increased complexity and dependency management; requires internet access for collective agent; more error cases.

4. **File Structure & Contents Format (Stage 2)**

Highlights include:

- **knowledge/graph.py** – Loads NDJSON scaffolds into a Bayesian network, supports queries and updates, performs belief propagation, caches results, and handles validation.
- **decision/mdp.py**, **decision/bayes.py**, **decision/simulation.py** – Implement value iteration, bandit strategies, Bayesian updates, Monte Carlo, and Markov simulations with optimisation for large state spaces.
- **Agents** – Knowledge, decision, collective, and ethics agents now implement observe and act methods using the new modules and fairness metrics.
- **execution/cursor_adapter.py** – Invokes the Cursor CLI, validates file paths, constructs JSON input, handles errors, caches results, and applies patches when requested.
- **config.py**, **utils** – Expanded to include new settings, caching, and concurrency improvements.

5. **Security, Risk & Threat Disclosure (Stage 2)**

- **Inference Attacks** – Ensure the graph only contains anonymised or aggregate data; implement access controls.
- **External Data Validity** – Vet and weight external data; implement trust scores.
- **Cursor CLI Safety** – Sanitize prompts, review suggestions, and run linters/tests before applying changes.
- **Fairness & Governance** – Document fairness criteria; allow human override; log blocked actions for audit.

6. **Performance & Scalability (Stage 2)**

- Use caching for knowledge queries and cursor results.
- Offload simulations to separate processes; provide configuration for concurrency.
- Throttle external API calls with timeouts and backoff.
- Avoid locking the entire knowledge graph on updates; use fine-grained locks or copy-on-write updates.

7. **Test Intelligence & Coverage (Stage 2)**

- Tests for knowledge graph loading, decision algorithms, simulations, ethics & collective agents, cursor adapter, new API endpoints, and stress scenarios.

8. **Stage 2 Summary**

Stage 2 turns the prototype into a full probabilistic multi-agent system with operational intelligence and cursor integration.

9. **Future Hooks for Stage 3**

Add user experience enhancements, plugin system, distributed execution, resilience, and advanced ethics metrics.

10. **Metadata & Compliance (Stage 2)**

```
{
  "task_id": "codex-compiler-20250924-stage2",
  "feature": "Refined Probabilistic Runner",
  "mode": "production",
  "variants_compared": true,
  "lint_passed": true,
  "test_coverage": "nominal+edge+negative+schema+performance",
  "risk_surface_declared": true,
  "assumptions_listed": true
}
```

### Stage 3: Polishing & Elevation

1. **Canonical Intent & Specification**

- **Component Name**: Polished Multi-Agent Runner with Visual & Ethical Elevation
- **Functional Goals**
  1. User Interface & Visual Refinement – Provide rich dashboards or interactive CLI output to visualize knowledge graphs, decision trees, simulation outcomes, fairness reports, and system health. Use the Visual Refinement & Styling Cognition Protocol to ensure high aesthetic quality.
  2. Dynamic Plugin & Extension System – Implement a plugin loader that discovers and loads new agents or commands from a designated directory at runtime. Provide interface contracts for safe plugin integration.
  3. Global Intelligence & Collaboration – Extend the collective agent to allow network participation (if user opts in), sharing anonymized data or models with other local runners. Implement privacy and consent controls.
  4. Advanced Ethics & Governance – Expand fairness models with real-world data, dynamic thresholds, and cross-domain awareness. Implement transparency dashboards showing how decisions are made and what the fairness metrics are. Provide user controls to adjust fairness sensitivity.
  5. Resilience & Observability – Add auto-restart and self-healing for long-running tasks; include health endpoints; integrate monitoring tools for metrics on task throughput, error rates, and resource usage. Provide audit trails with tamper-proof logs.
  6. Optimization & Performance Polishing – Optimize caching strategies, simulation algorithms, and concurrency settings based on usage patterns. Benchmark and profile the system; adjust heuristics for GPU acceleration if available. Provide configuration UI or CLI for tuning.
- **Non-Goals**
  - Adding wholly new algorithmic families without justification.
- **Stakeholders**
  - End users – Benefit from intuitive dashboards and refined interactions.
  - Administrators – Require monitoring and control over long-running tasks and plugin management.
  - Ethics & Governance – Need detailed reporting and transparency to audit decisions.
- **Rationale & Constraints**
  - Stage 3 focuses on user experience, extensibility, and reliability. Constraints include cross-platform UI frameworks, plugin security, and user privacy.

2. **Modular File & Directory Plan (Stage 3)**

```
runner_project/
├── src/
│   ├── ui/
│   │   ├── dashboard.py        # Serves visual dashboards via a web interface.
│   │   ├── templates/
│   │   │   ├── index.html      # HTML templates styled per aesthetic rules.
│   ├── plugins/
│   │   └── __init__.py        # Plugin loader; discovers modules implementing a defined interface.
│   ├── agents/
│   │   ├── collective_agent.py# Extended for global intelligence sharing.
│   │   ├── ethics_agent.py    # Extended for dynamic thresholds and cross-domain fairness.
│   ├── utils/
│   │   ├── observer.py        # Health check and self-healing routines.
│   │   ├── plugin_loader.py   # Discovers and validates plugins in `plugins/`.
│   ├── api/
│   │   ├── server.py           # Adds endpoints for dashboards, plugin management, health checks.
│   │   ├── schemas.py          # Adds models for UI and plugin operations.
├── tests/
│   ├── test_ui.py            # Tests UI endpoints and templates.
│   ├── test_plugins.py       # Tests plugin loading and sandboxing.
│   ├── test_resilience.py    # Tests auto-restart and health checks.
└── README.md                 # Extended usage docs, plugin guidelines, UI explanation.
```

3. **Variant Analysis & Decision Making (Stage 3)**

- **Variant A: Server-Side Rendering UI & Built-in Plugin Loader** – Dashboards are served by FastAPI using Jinja2 templates; plugin loader runs within Python runtime, discovering modules at startup. Pros: simpler deployment. Cons: limited interactivity; reload required for new plugins.
- **Variant B: Decoupled Frontend & Hot-Swappable Plugins (Chosen)** – A separate frontend consumes the REST API; plugin loader monitors the plugins directory and can load new plugins at runtime via importlib with sandboxing. Pros: rich interactive UI, dynamic extensibility. Cons: requires building and serving a frontend; plugin sandboxing is more complex.

4. **File Structure & Contents Format (Stage 3)**

- **ui/dashboard.py** – Provides endpoints returning dashboard data; may render templates or serve static assets; handles missing data gracefully.
- **utils/plugin_loader.py** – Discovers Python modules in the plugins directory, validates interface adherence, loads them into isolated namespaces, and manages metadata.
- **utils/observer.py** – Implements health checks, failure tracking, and auto-healing hooks.
- **agents** – Collective and ethics agents expanded for global intelligence and dynamic fairness.
- **api/server.py** – Handles UI, plugin management, and health endpoints.

5. **Security, Risk & Threat Disclosure (Stage 3)**

- **Plugin Injection** – Mitigate with sandboxing, signatures, and whitelisting.
- **UI Data Exposure** – Enforce authentication and authorization; escape user input.
- **Data Sharing & Privacy** – Implement opt-in, anonymization, encryption, and compliance checks.
- **Cross-Site Scripting (XSS)** – Sanitize JSON and enforce CSP headers.
- **Denial of Service** – Apply rate limiting and resource quotas.

6. **Performance & Scalability (Stage 3)**

- Use asynchronous websockets or efficient polling for real-time updates.
- Lazy-load heavy dashboard components; compress data.
- Use worker threads/processes for plugin operations; provide configuration for scaling.

7. **Test Intelligence & Coverage (Stage 3)**

- Tests for UI, plugin system, resilience routines, ethics and global intelligence, and performance benchmarks under load.

8. **Stage 3 Summary**

Stage 3 elevates the runner to a polished platform with dashboards, plugin ecosystem, global intelligence, advanced ethics, resilience, and optimisation.

9. **Future Hooks Beyond Stage 3**

- Deep learning and advanced RL.
- Cross-device synchronization.
- Marketplace for plugins and models.
- A/B experimentation framework.

10. **Metadata & Compliance (Stage 3)**

```
{
  "task_id": "codex-compiler-20250924-stage3",
  "feature": "Polished Multi-Agent Runner",
  "mode": "production",
  "variants_compared": true,
  "lint_passed": true,
  "test_coverage": "nominal+edge+negative+schema+performance+ui+plugin+resilience",
  "risk_surface_declared": true,
  "assumptions_listed": true
}
```

---

Maintaining this document alongside the codebase ensures that audits can quickly verify the system against the agreed-upon plan. It also provides the automation runner with explicit prompts for repeating the build, refinement, and polishing cycles whenever new tasks begin.
