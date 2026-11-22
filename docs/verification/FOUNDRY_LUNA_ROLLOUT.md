# GPT-6 Luna rollout and competition verification

The local Competition Edition dashboard handles synthetic sign-in analysis for Tier 1 and Tier 2 SOC analysts. Foundry provides two evidence-linked opinions on the selected built-in scenario. The analyst owns the case disposition. The approval queue continues to use the deterministic replay and stores only simulated decisions.

## Roles and handoff

| Role | Implementation | Input and output |
|---|---|---|
| Intake | Local rules | Loads the fixture and normalizes sign-in events for replay. |
| Enrichment | Local rules | Adds synthetic inventory and change records. |
| Detection | Local rules | Correlates on asset ID and a five-minute window and passes signal evidence IDs. |
| Triage | GPT-6 Luna or local baseline | Uses the evidence and severity rubric to return severity, rationale and citations. |
| Investigation | GPT-6 Luna or local baseline | Reads validated triage and the evidence and returns findings, limitations, citations and an analyst next step. |
| Reporting | Local application | Renders the results, citations and stage durations. The baseline also shows the timeline, evidence digests and playbook. |

The dashboard runs the local replay first. Selecting **Run with GPT-6 Luna** invokes a separate synthetic replay. The Azure requests have bounded SDK timeouts and no automatic retries. The server passes event types, synthetic asset IDs, timestamps, inventory/change status and evidence IDs. Model results must pass the Pydantic contracts and each cited ID must match the current fixture. The model output is displayed as plain text. The cloud request has no tools, raw log fields, arbitrary case input or write access to the approval queue.

## Task ledger

| Task | Status | Acceptance evidence |
|---|---|---|
| Offline scenario replay, traces and approval simulation | Verified locally | Python suite and labeled deterministic evaluation. |
| Repository integration and dashboard | Verified locally | Foundry route and pinned-agent adapter tested with simulated provider responses. |
| GPT-6 Luna model deployment | Blocked | On 22 November 2026, Foundry showed 0 TPM of Global Standard quota and insufficient Data Zone Standard quota. The 5,000 TPM Global Standard request returned `MFARequired` and was not accepted. |
| Publish Luna agent versions and activate them | Pending quota | Deploy as `gpt-6-luna`, run the configure command, pin both versions and verify the version/model shown by the project. |
| Cloud workflow and quality evaluation | Pending deployment | Reproduce the privileged sign-in case in CLI and dashboard, run all eight fixtures, record failures and review output for semantic support and advisory wording. |
| Contest package and review | Pending author review and recording | Use the design review as reference. Verify the submission requirements, write the final description and record the demonstration. |

## Operate and evaluate

- Keep the demo dashboard bound to loopback. Use Microsoft Entra credentials server-side. Require organizational identity, RBAC, controlled ingress and request budgets for any shared deployment.
- Compare severity to the eight repository labels. Require valid, unique evidence IDs for both agent responses. Check the investigation with a human for relevance, factual support and uncertainty. These are engineering acceptance checks.
- Collect completion status, model deployment, pinned version, durations and evidence validation outcome. Record quota failures separately from contract failures. Review request percentiles and model consumption with Azure metrics during a pilot.
- Run lint, tests and offline evaluation in CI. After quota approval, run a fresh cloud evaluation before changing the pinned versions in any shared environment. If a live test fails, use the documented offline path and review the redacted error.
- Document the business problem, two distinct model-backed roles, four deterministic roles, handoffs, governance and test results in the submission. Show a labeled synthetic run and explain what the analyst reviews. Keep credentials and portal identifiers out of the recording. The competition upload limit shown in Founderz is three minutes and 150 MB.

## Local verification record

- Python 3.12.14, 58 passing tests and 93.26% coverage. Ruff and JavaScript syntax checks passed.
- All eight deterministic labeled scenarios passed. Severity agreement, detection precision, recall and evidence-link validation each scored 100% on these fixtures.
- Chromium checks passed on desktop and mobile. The checks exercised replay, evidence, evaluation, simulated approvals and the dashboard rendering of a mocked Luna response.
- The live Luna result and cloud evaluation remain pending the Azure deployment.
