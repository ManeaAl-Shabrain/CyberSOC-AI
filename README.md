# CyberSOC AI — Competition Edition

A local, synthetic-data SOC workspace that replays suspicious sign-ins, correlates evidence, proposes analyst next steps, and records human decisions for simulated actions. The six agents are deterministic specialists. The Foundry provider is disabled until cloud access and runtime behavior can be verified.

## Start the demo

Use Python 3.11 or later. From this directory:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8000
```

On PowerShell, activate with `.venv\Scripts\Activate.ps1`. Open
[http://127.0.0.1:8000](http://127.0.0.1:8000). Replay the default privileged sign-in, review the linked evidence, and run the evaluation. Swagger is at `/docs`. For a read-only walkthrough, the commands above are sufficient.

To enable the approval walkthrough, generate two separate random tokens in a private terminal before starting Uvicorn:

```bash
export CYBERSOC_ANALYST_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
export CYBERSOC_REVIEWER_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
```

Use the analyst token to request a simulation on the high-severity case. Replace it with the reviewer token, load the queue, approve, select **Simulate**, then load the audit. Use different tokens and keep them off the recording. Leave both unset to disable approvals. The store defaults to in-memory SQLite. Set `CYBERSOC_DB` to a local path to keep event and approval records across restarts. Set `CYBERSOC_API_TOKEN` to require a separate bearer token for the prototype event endpoints. Bind the demo to loopback.

## Verify

```bash
ruff check .
python -m pytest --cov=cybersoc --cov=apps --cov-fail-under=80
python -m cybersoc.evaluation
```

The evaluation checks severity agreement, detection precision and recall, evidence references and hashes, workflow completeness, stage tools and redaction. The current result applies to eight labeled synthetic fixtures. It measures citation integrity and rule behavior. Analyst assessment of semantic grounding and alert-triage quality belongs in a later pilot.

## Container option

```bash
docker build -t cybersoc-competition .
docker run --rm -p 127.0.0.1:8000:8000 cybersoc-competition
```

Pass the two approval variables with `-e CYBERSOC_ANALYST_TOKEN -e CYBERSOC_REVIEWER_TOKEN` when needed. The image definition uses a non-root user. The container build needs a Docker-enabled machine.

## Project evidence

- [Master plan](docs/MASTER_PLAN.md)
- [Implemented architecture and production path](docs/architecture/ARCHITECTURE.md)
- [Security baseline](docs/security/SECURITY_BASELINE.md)
- [Phase verification](docs/verification/COMPETITION_REVIEW.md)
- [Measured evaluation baseline](docs/verification/evaluation-baseline.json)
