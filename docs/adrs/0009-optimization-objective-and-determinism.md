# ADR 0009: Optimization Objective And Deterministic Search

- Status: Accepted
- Date: 2026-03-28

## Context

The repository now has a deterministic policy engine, but it still lacks a real optimizer that can:

- choose a best-to-post collateral set for a required obligation amount
- recommend substitutions when an existing posted set is economically inferior
- respect concentration and control constraints rather than treating them as after-the-fact warnings
- explain its choices deterministically for operators, auditors, and legal review

The optimizer must remain explicitly advisory. Canton workflow execution continues to be the authoritative state transition layer.

## Decision

The first optimization engine will be implemented as a separate off-ledger Python service under `app/optimizer/` with a separate machine-readable `OptimizationReport` contract.

Specific decisions:

1. The optimizer consumes one `CPL v0.1` policy, one normalized inventory snapshot, and one obligation input that expresses a required coverage amount in lendable-value terms.
2. The optimizer reuses the policy engine's non-concentration lot screening and report-finalization logic rather than re-implementing eligibility or haircut semantics.
3. Candidate lots are screened first for hard per-lot admissibility. Portfolio feasibility is then evaluated by enumerating admissible subsets and applying the same concentration and policy-decision path used by `PolicyEvaluationReport`.
4. Only `ACCEPT` portfolios that cover the requested obligation amount are eligible for automatic recommendation in `v0.1`. `REVIEW` and `ESCALATE` outputs remain visible in explanation traces but are not auto-selected.
5. The optimization objective is lexicographic:
   - minimize posted market value
   - then minimize haircut cost
   - then minimize excess coverage posted above the obligation amount
   - then minimize lot count
   - then break remaining ties by sorted lot identifiers
6. If the current posted set is economically equal to the best discovered alternative on the first four objective dimensions, the optimizer keeps the current set rather than recommending churn solely because of the deterministic tie-break.
7. The optimizer produces a deterministic `OptimizationReport` with screened-candidate results, portfolio summaries, substitution deltas, and step-by-step explanation traces.

## Consequences

Positive:

- the repository now has a real best-to-post and substitution path rather than documentation-only intent
- policy semantics remain centralized in the policy engine instead of drifting into a second opaque implementation
- concentration control is enforced inside allocation selection rather than as a post-selection afterthought
- deterministic explanation traces support operational review, legal defensibility, and reproducible tests

Tradeoffs:

- the first search strategy is exhaustive over the admissible subset space, which is acceptable for the current small deterministic prototype but not a production-scale algorithm
- the objective uses explicit economic proxies such as market value consumed and haircut drag because live funding curves, repo specialness, and inventory financing costs are not yet pinned
- the optimizer remains advisory and off-ledger, so workflow-coupled reservation, consent, and settlement sequencing are still future work

These tradeoffs are accepted because the repository needs a transparent, deterministic baseline optimizer before it adds live market-data contracts, workflow-coupled reservation logic, or larger-scale search methods.
