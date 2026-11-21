# Competition Edition verification

## P0 — Source review

The latest verified archive matches the current authoritative plan. Lesson 8 calls for design, a readiness plan, a complete workflow, a PDF or Word document, and a recorded presentation up to 3 minutes and 150 MB. A live deployment, deadline and independent judging rubric were not established by the supplied materials. The local demo uses synthetic fixtures.

## P1 — Foundation

On Python 3.11.18, Ruff, compilation and diff checks passed. Pytest: 21 passed, 97.25% combined application and core line coverage. Before remediation: 16 tests passed and Ruff found eight lint issues. Reviewed issues included unrestricted API access, SQLite lifetime and concurrent access, unbounded event input, permissive simulation flags, and validation echo. Updated local host controls, optional bearer access, storage, payload limits and validation errors. Production identity and shared deployment remain separate concerns.

Remote clone and branch listing confirmed an empty repository. GitHub returned 409 creating a development branch from main. Git HTTPS dry run had no credentials. Local branches preserve review history. Remote CI and review are unverified.

## P2 — Contracts and replay

Ruff and 30 pytest cases passed on Python 3.11.18. The eight v1 synthetic cases replay deterministic timestamps, identifiers, hashes and severity labels. Case contracts reject dangling evidence links. Package metadata is generated at install time and excluded from the source release.

## P3 — Agents and orchestration

41 Python 3.11 tests and Ruff passed. The six deterministic roles exchange typed event, evidence and case records. Replay produces identical case reports. Stage failures give a redacted manual-review result and bounded read-only retries. Foundry execution is unverified and remains disabled. The elapsed-time budget is checked between synchronous local operations and after they return.

## P4 — Local approval safety

46 tests passed, with 98.44% combined coverage. API integration tests verified deny-by-default configuration, role separation, an eligibility check, approval before simulation, denial terminality, de-duplication and correct audit actors. Changes are transactional in SQLite. Simulation writes only the local state and audit record. Local role tokens are demo authentication. Enterprise identity, multi-tenant authorization and production audit custody remain deployment requirements.

## P5 — Tracing and evaluation

48 tests passed with 98.43% coverage. The checked-in JSON baseline records eight labeled synthetic cases, 100% severity agreement, precision, recall and grounded-link rate. Grounded-link scoring verifies source IDs and evidence digests. It is a proxy for factual grounding and does not replace analyst review. No model tokens are used. A negative control forces incorrect severity and verifies a failed evaluation exit code. The workflow definition runs this check in CI.

## P6 — Dashboard and install

50 tests passed, with 98.51% combined coverage. The integration load smoke test replayed 64 cases via eight worker threads and recorded 64 distinct trace IDs. A Chromium walkthrough verified desktop and 375-pixel mobile layouts, replay, timeline, trace expansion, evaluation, analyst and reviewer roles, simulation and audit. A clean Python 3.11 environment installed the built wheel and found its static UI and packaged fixtures. Docker hardware/runtime and Azure resources were unavailable, so container execution and cloud deployment are unverified.
