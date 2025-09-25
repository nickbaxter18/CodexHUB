# AI Review Ledger

Store machine-assisted review artefacts in this directory. Recommended structure:

- `log.json` – Append-only log of accepted/rejected suggestions maintained via
  `scripts/metrics/log_ai_review.py`.
- `proposals/` – Optional folder for raw AI-generated diffs grouped by PR.

### Logging Guidance

Run the helper when AI suggestions are evaluated:

```bash
python scripts/metrics/log_ai_review.py \
  --agent cursor-meta \
  --source scripts/run-quality-gates.sh \
  --summary "<short outcome>" \
  --accepted <count> \
  --rejected <count> \
  --notes "<context>"
```

Each invocation appends to `log.json` and ensures a trailing newline so
downstream tooling can stream the ledger. Quality-gate runs use this flow to
capture which AI suggestions were accepted or rejected alongside the telemetry
emitted in `results/metrics/quality-gates-log.ndjson`.
