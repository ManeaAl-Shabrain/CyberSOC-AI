# Phase 1 architecture

FastAPI -> validated SecurityEvent -> SQLite append-only-by-API EventRepository -> event hash response. The application is a modular monolith. Agent orchestration is an interface reserved for Phase 2. MockProvider returns a deterministic unverified result. FoundryProvider fails closed until Azure region, model quota and credential configuration are verified.

Future agents (not implemented): Intake, Enrichment, Detection, Triage, Investigation, Reporting. Human approval gates remain mandatory for any response action. Real response actions are excluded from the competition demo.

SQLite is for local demonstration only. Its SHA-256 digest detects accidental content changes only when independently compared against a trusted copy; it does not provide tamper-proof custody.
