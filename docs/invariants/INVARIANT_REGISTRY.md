# Invariant Registry

This registry defines system properties that future code, reports, and tests must preserve. Each future implementation change should link affected invariants to evidence and verification.

## Taxonomy

- authorization and role control
- eligibility determinism
- haircut and lendable-value correctness
- no double-encumbrance
- atomic substitution and return
- report fidelity
- replay safety
- auditability

## Starter Invariants

| ID | Theme | Invariant Statement | Planned Evidence |
| --- | --- | --- | --- |
| AUTH-001 | Authorization and role control | Only authorized roles may create, approve, amend, or release collateral policy and workflow actions, and every authorization decision must be attributable to an identity and role. | policy schema, access-control tests, audit records |
| ELIG-001 | Eligibility determinism | Given the same policy version, asset facts, valuation inputs, and concentration state, eligibility evaluation must produce the same decision and explanation every time. | decision procedure spec, deterministic tests, execution reports |
| HAIR-001 | Haircut and lendable-value correctness | Lendable value must equal the policy-defined valuation basis adjusted by the policy-defined haircut and rounding rules, with no hidden adjustments. | valuation formulas, test vectors, report fields |
| ENC-001 | No double-encumbrance | A collateral position or lot must not be concurrently committed to overlapping obligations beyond its available encumberable amount. | state model, concurrency tests, ledger evidence |
| ATOM-001 | Atomic substitution and return | Collateral substitution and collateral return must complete atomically so that exposure coverage is not broken by intermediate visible states. | workflow spec, transactional tests, Canton proof artifacts |
| REPT-001 | Report fidelity | Every machine-readable execution report must correspond exactly to committed workflow state and must not invent or omit materially relevant actions. | report schema, state-to-report checks, demo evidence |
| REPL-001 | Replay safety | Retried or replayed messages, commands, or events must not create duplicate pledges, duplicate releases, or inconsistent reports. | idempotency design, replay tests, event-correlation evidence |
| AUD-001 | Auditability | Every material state transition must be traceable to inputs, policy version, actors, timestamps, and resulting state changes without requiring hidden manual reconstruction. | audit log design, report schema, operational runbooks |

## Notes

- These invariants are initial and intentionally technology-agnostic.
- Future invariants should add explicit links to tests and evidence entries once implementation begins.
