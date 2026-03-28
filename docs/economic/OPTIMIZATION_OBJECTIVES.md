# Optimization Objectives

## Purpose

This note explains why the first optimizer objective is aligned with institutional collateral practice even though the repository does not yet consume live funding curves, repo specials, or custody-fee schedules.

## Best-To-Post And Cheapest-To-Deliver Intuition

Institutional collateral managers generally prefer to satisfy an obligation with the assets that impose the lowest economic opportunity cost while still meeting policy and operational constraints. In this repository's first optimizer, that intuition is represented conservatively by minimizing:

1. posted market value
2. haircut cost
3. excess coverage
4. lot count

Minimizing posted market value is the first proxy for best-to-post or cheapest-to-deliver behavior because, absent live market funding inputs, it captures the amount of economically useful inventory consumed to satisfy the call. Haircut cost is next because two portfolios with similar gross market value can still consume different amounts of policy-adjusted collateral capacity.

## Concentration And Control Constraints

Institutional practice does not treat concentration or control as optional overlays. Central-bank collateral frameworks, tri-party programs, and CCP rulebooks all embed hard eligibility and concentration conditions into the usable collateral set itself.

The optimizer therefore excludes portfolios that:

- fail policy eligibility or control checks
- breach concentration limits
- fail to cover the obligation after haircuts

This means the objective ranks only compliant candidate portfolios. The engine does not first choose the cheapest portfolio and only then discover that it cannot actually be posted.

## Substitution Economics

Substitution exists because the posted set that was feasible yesterday may not remain the best use of scarce inventory today. A substitution recommendation is economically sensible when a replacement set:

- preserves policy compliance
- preserves or improves coverage of the required obligation amount
- releases higher-value or lower-haircut inventory back into the firm's available pool
- reduces unnecessary overposting or collateral drag

The first optimizer compares the current posted set to the best feasible alternative on the same published objective vector. If the current set is economically equal on the real economic dimensions, the engine keeps it rather than forcing churn based on a deterministic tie-break alone. That mirrors operational practice: unnecessary substitutions create settlement and control overhead with no compensating economic gain.

## Why Deterministic Explainability Matters

Collateral optimization is not just a math problem. It is subject to operational challenge, legal review, and post-trade reconstruction.

Deterministic explainability matters because:

- operations teams need to understand why a set was chosen or rejected before instructing movement
- secured parties, custodians, and internal reviewers may need to challenge a substitution or concentration conclusion
- legal and audit review require a stable record that can be re-run from the same inputs
- workflow authority remains on Canton, so off-ledger optimizer advice must be attributable rather than opaque

For that reason, the optimizer emits:

- screened-candidate outcomes
- portfolio summaries
- concentration results
- substitution deltas
- ordered explanation traces

This is intentionally conservative institutional practice: explain the recommendation, make the constraints explicit, and keep authoritative execution separate from the advisory optimization layer.
