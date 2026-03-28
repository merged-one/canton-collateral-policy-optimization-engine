# Security Policy

## Scope

This repository is the control-plane and prototype planning surface for a safety-critical collateral workflow system. Even at the documentation stage, treat confidentiality, integrity, authorization, replay safety, and auditability as core security concerns.

## Reporting A Vulnerability

Until a dedicated disclosure channel is established:

- do not open public issues containing exploit details, credentials, or sensitive architecture weaknesses
- report vulnerabilities privately to the repository owner or designated maintainer
- include affected document or component names, impact, reproduction steps, and assumptions

## Current Security Expectations

- no secrets or credentials in the repository
- no synthetic success artifacts that could be mistaken for validated system output
- no undocumented trust-boundary changes
- security-sensitive design changes must update:
  - [docs/security/THREAT_MODEL.md](./docs/security/THREAT_MODEL.md)
  - [docs/risks/RISK_REGISTER.md](./docs/risks/RISK_REGISTER.md)
  - [docs/evidence/EVIDENCE_MANIFEST.md](./docs/evidence/EVIDENCE_MANIFEST.md)

## Prototype Warning

This repository is not production-ready. Future code should be evaluated as experimental until the threat model, tests, and operational controls have implementation-grade evidence behind them.
