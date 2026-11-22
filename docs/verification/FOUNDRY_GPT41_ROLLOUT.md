# CyberSOC-AI competition operations plan

The demo supports analysts triaging synthetic sign-in signals. It combines the local evidence trace with an optional Foundry replay. The Foundry agents recommend next steps for a human analyst. The approval queue records hypothetical response actions in a local audit log.

## Roles and acceptance checks

| Role | Runtime | Task and acceptance check |
|---|---|---|
| Intake | Local | Validate a known synthetic scenario and normalize the sign-in sequence. Reject unknown scenarios. |
| Enrichment | Local | Attach synthetic asset privilege and change status. Treat free-form event content as untrusted and keep it out of the cloud payload. |
| Detection | Local | Correlate the events using the existing sign-in rules. Supply evidence IDs for the contributing events. |
| Triage | Foundry or local baseline | Classify severity from evidence and return a rationale with citations from the input case. |
| Investigation | Foundry or local baseline | Use validated triage and evidence to summarize the case, state missing facts and recommend an analyst next step. |
| Reporting | Local | Render the timeline, evidence, trace and model notes. Keep the result advisory and preserve the analyst's decision. |

Each replay runs all six roles under one trace. The Foundry replay calls tool-free `cybersoc-triage` and `cybersoc-investigation`.
The endpoint pins both versions and checks that they use the configured
deployment before contacting the model. Malformed output and evidence IDs outside the current
scenario stop the workflow and trigger manual review. Reporting validates the
complete case, attaches the chronological timeline and marks AI findings unverified. The UI renders response text as
plain text. Only built-in fixture fields are sent. The model has no external
tools or write access to the simulated approval queue.

## Task and release checklist

| Order | Task | Owner and exit condition |
|---|---|---|
| 1 | Start the synthetic demo | Maintainer verifies startup, the scenario list and desktop and mobile replay. |
| 2 | Verify the cloud connection | Maintainer confirms the GPT-4.1 mini deployment and the two pinned agent versions, then runs the privileged sign-in case. |
| 3 | Evaluate quality | Maintainer runs all eight offline scenarios in CI and records live results separately. An analyst checks severity, cited evidence, uncertainty and recommendations. |
| 4 | Rehearse review | Analyst proposes a simulated response. A separate reviewer approves or denies it. The audit shows the actual decision. |
| 5 | Prepare the submission | Owner records the demonstration, adds architecture documentation and checks for credentials, real data and unsupported claims. |
| 6 | Review model availability | Owner checks the separate quota requests. Change the model only after approval, deployment, new pinned versions and a rerun of the case and evaluation. |

## Deployment, monitoring and rollback

Keep the competition server on loopback. For shared staging, require Entra
authentication, restrict ingress, apply least privilege and configure rate and
cost monitoring. Capture response duration, error class, version and evidence
validation outcomes. Treat a failed smoke test as a deployment blocker. Keep
the existing GPT-4.1 mini deployment and pinned version pair available for
rollback. To rehearse with the offline dashboard, clear the Foundry endpoint
before restarting.

## Presentation sequence

Use the privileged sign-in case already run in Foundry to avoid waiting on the
demo deployment's between-call pause during recording.

- 0:00–0:25. Explain the alert and the analyst's goal.
- 0:25–1:15. Show the scenario, timeline and cited evidence.
- 1:15–2:10. Show the triage classification and the investigation's uncertainty.
- 2:10–2:45. Show the independent reviewer decision and simulated audit.
- 2:45–3:00. Explain the eight-case evaluation and the limits of the demo.

The screenshot supplied on 22 November confirms the submission of a 5,000 TPM
Global Standard quota request for GPT-6.2 Astra. The screenshot records
submission only. GPT-4.1 mini remains the configured competition model.

## Verification record

- Foundry Playground, GPT-4.1 mini, agent version 2 for both roles. On the
  privileged sign-in fixture, triage returned High and six valid evidence IDs.
  Investigation received the triage JSON, cited the same six IDs and described
  what the analyst should verify. The handoff in the portal was manual.
- A local replay of those two captured JSON responses completed the six-stage
  workflow and generated one validated advisory report and trace.
- Python 3.12.14, 59 passing tests and 92.56% coverage. All eight offline
  synthetic cases passed. Ruff and JavaScript syntax checks passed.
- Chromium desktop and mobile verified local replay and simulated approvals.
  Browser checks also exercised the integrated Foundry display and manual-review
  branch with simulated API responses.
- The current branch still needs a live end-to-end SDK run and the complete
  eight-fixture cloud evaluation. Production staging and the author's own
  recording and competition submission are separate release steps.
