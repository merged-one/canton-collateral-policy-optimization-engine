# Threat Model

## Scope

The future system will manage confidential collateral policy and workflow state across multiple parties. This document records the initial threat posture and the design areas that must remain visible as implementation begins.

## Protected Assets

- confidential policy and position data
- authorization decisions and role assignments
- valuation inputs and haircut parameters
- encumbrance state
- execution reports and audit evidence

## Threat Actors

- unauthorized internal user
- authorized user exceeding their role
- compromised integration endpoint
- operator error during substitution or release
- external observer attempting to infer confidential state

## Core Threats

| Threat | Why It Matters | Initial Control Direction |
| --- | --- | --- |
| Broken authorization or role separation | Users could approve or release collateral outside policy. | Explicit role model, auditable authorization checks, invariant tracking. |
| Confidentiality leakage | Sensitive counterparty or position information could escape intended visibility. | Privacy-preserving workflow boundaries and minimal reporting disclosure. |
| Replay or duplicate execution | Repeated events could create duplicate pledges or releases. | Idempotent command design and replay-focused tests. |
| Non-atomic substitution or return | Coverage could be lost during workflow transitions. | Treat atomic workflow completion as a blocking invariant. |
| Report tampering or drift | Operators could rely on incorrect evidence. | State-derived report generation and report-fidelity checks. |
| Environment drift | The system could become impossible to reproduce or validate consistently. | Pinned dependencies, explicit bootstrap commands, and release evidence. |

## Trust Boundaries

- policy authoring versus workflow execution
- optimization proposal generation versus settlement
- confidential ledger state versus operator-facing reports
- local development environment versus external dependencies

## Open Questions

- which Canton domains, parties, and application boundaries should be explicit in the LocalNet?
- what minimum report content is needed for auditability without over-disclosure?
- what reference data freshness and provenance guarantees are required for valuation inputs?
