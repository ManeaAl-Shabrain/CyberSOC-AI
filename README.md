# CyberSOC AI — Competition Edition

Phase 1 foundation for a proposed multi-agent SOC architecture. This is **not** a production SOC and has **no live containment capability**.

**Authoritative plan:** [docs/MASTER_PLAN.md](docs/MASTER_PLAN.md) — requirements, phase ledger, architecture, submission checklist and quality gates.

## Local quickstart

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
uvicorn apps.api.main:app --reload
```

API documentation: http://127.0.0.1:8000/docs

Run checks:

```bash
ruff check .
pytest --cov=cybersoc --cov-report=term-missing --cov-fail-under=80
```

## Scope

- Synthetic event ingestion, immutable-by-API event records, validation and evidence hashes.
- Human approval state machine for **simulated** actions only.
- Offline mock AI provider; Microsoft Foundry is intentionally not enabled.
- No authentication or production authorization is implemented; run on localhost only.

See docs for architecture, security limitations, and verification.
