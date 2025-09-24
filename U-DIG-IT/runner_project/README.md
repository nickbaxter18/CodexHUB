# Probabilistic Multi-Agent Runner

This project now implements Stage 3 of the Probabilistic Multi-Agent Runner blueprint.

The runner exposes a probabilistic multi-agent system capable of:

- Loading curated NDJSON knowledge bases into a searchable knowledge graph.
- Deriving contextual insights through a collective intelligence layer with caching and opt-in sharing.
- Selecting actions using Bayesian bandits, value iteration heuristics, and Monte Carlo simulations.
- Enforcing adaptive fairness thresholds with an ethics agent before delegating to execution layers.
- Executing whitelisted shell and Git commands, as well as Cursor CLI operations, inside asynchronous tasks.
- Serving REST endpoints for command scheduling, knowledge queries, simulations, cursor integrations, plugin management, dashboard data, and system health.
- Rendering an HTML dashboard summarising task throughput, knowledge coverage, ethics metrics, and active plugins.
- Loading runtime plugins via a hot-reloadable plugin loader and exposing health checks for resilience.

Run the automated test suite from the project root:

```bash
pytest
```
