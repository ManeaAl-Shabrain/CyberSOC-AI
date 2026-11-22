# CyberSOC AI — Competition Edition

A local, synthetic-data SOC workspace that replays suspicious sign-ins, correlates evidence, proposes analyst next steps, and records human decisions for simulated actions. The offline replay includes six deterministic specialists. The optional Foundry replay uses two GPT-4.1 mini agents for triage and investigation for the same synthetic scenarios.

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

## Replay with Microsoft Foundry

The Competition Edition uses the existing `gpt-4.1-mini` deployment. Attach the
two existing prompt agents by their versions or create versions in a fresh
project with `python -m cybersoc.foundry_demo configure`. That command prints
the versions it created. Both agents must use the configured deployment and have
empty tool lists. See the [competition operations plan](docs/verification/FOUNDRY_GPT41_ROLLOUT.md)
for stage ownership, rehearsal steps and acceptance criteria.

From PowerShell at the repository root, with your virtual environment active:

```powershell
az login
python -m pip install -e '.[foundry]'
$env:FOUNDRY_PROJECT_ENDPOINT = '<Foundry project endpoint ending in /api/projects/<project>>'
$env:FOUNDRY_DEPLOYMENT = 'gpt-4.1-mini'
$env:FOUNDRY_TRIAGE_VERSION = '2'
$env:FOUNDRY_INVESTIGATION_VERSION = '2'
$env:FOUNDRY_STAGE_DELAY_SECONDS = '61'
python -m cybersoc.foundry_demo run --scenario privileged-sign-in
python -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8000
```

The example version numbers apply to the existing `cybersoc-ai` project. Use
your project's actual version numbers. The optional pause is for the 1,000 TPM
competition deployment. Open the dashboard and select **Run with gpt-4.1-mini**.
The Foundry panel shows classification, limitations, citations, stage duration
(including any configured pause in investigation) and the trace ID. Review any recommendation before taking action.

Run `python -m cybersoc.foundry_demo evaluate` for all eight fixtures. With
61-second pacing, the live suite takes about 15 minutes plus response times.
The routine uses true model calls and consumes tokens. Use the
[Foundry agent quickstart](https://learn.microsoft.com/en-us/azure/foundry/agents/quickstarts/prompt-agent)
for credential and project setup.
