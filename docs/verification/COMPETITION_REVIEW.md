# Competition Edition verification

## P0 — Source review

The latest verified archive matches the current authoritative plan. Lesson 8 calls for design, a readiness plan, a complete workflow, a PDF or Word document, and a recorded presentation up to 3 minutes and 150 MB. A live deployment, deadline and independent judging rubric were not established by the supplied materials. The local demo uses synthetic fixtures.

## P1 — Foundation

On Python 3.11.18, Ruff, compilation and diff checks passed. Pytest: 21 passed, 97.25% combined application and core line coverage. Before remediation: 16 tests passed and Ruff found eight lint issues. Reviewed issues included unrestricted API access, SQLite lifetime and concurrent access, unbounded event input, permissive simulation flags, and validation echo. Updated local host controls, optional bearer access, storage, payload limits and validation errors. Production identity and shared deployment remain separate concerns.

Remote clone and branch listing confirmed an empty repository. GitHub returned 409 creating a development branch from main. Git HTTPS dry run had no credentials. Local branches preserve review history. Remote CI and review are unverified.

## P2 — Contracts and replay

Ruff and 30 pytest cases passed on Python 3.11.18. The eight v1 synthetic cases replay deterministic timestamps, identifiers, hashes and severity labels. Case contracts reject dangling evidence links. Package metadata is generated at install time and excluded from the source release.
