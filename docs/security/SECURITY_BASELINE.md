# Security baseline and threat model

## Trust boundaries
Untrusted event payloads must never become system instructions. AI output is advisory, unverified without cited evidence. CyberSOC AI uses synthetic data for its demo and submission. Never place credentials in source control.

## Threats
- Prompt injection embedded in logs: isolate log content as data and require grounded findings.
- Excessive agency: deny all real remediation; explicit human approval for simulated execution.
- Evidence alteration: retain the canonical validated event and digest; production requires signed append-only storage.
- Sensitive data leakage: synthetic inputs only; redaction and data classification are Phase 2+ requirements.
- Cloud cost runaway: Foundry integration disabled until explicit cost caps and quotas are verified.
- API abuse: Bind the demo to loopback. Host validation and an optional local API token reduce accidental access. Public deployment requires production identity, authorization and rate limiting.

## Non-goals
Production authentication, multi-tenant authorization, enterprise audit custody, network isolation, and incident response automation are not implemented in Phase 1.
