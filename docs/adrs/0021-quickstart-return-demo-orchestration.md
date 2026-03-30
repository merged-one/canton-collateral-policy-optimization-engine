# ADR 0021: Orchestrate The Return Demo Through Quickstart Workflow Handoff And Reference Token Adapter

- Status: Accepted
- Date: 2026-03-30

## Context

ADR 0013 established the first retained-set return prototype on the IDE ledger with approval-gated release, replay-safe request identifiers, and stale-coverage blocking. ADR 0018 established the first narrow Quickstart-backed reference token adapter path. ADR 0020 then bound substitution through Quickstart, but the confidential return demo still stopped before the real runtime and adapter surface.

That left four material gaps:

- `make demo-return` still stopped on the IDE ledger
- the Quickstart seed, return workflow, adapter, and provider-visible status surfaces were disconnected from the return demo command
- the return report could not yet prove approval-gated release plus final post-return state on the real runtime path
- blocked unauthorized or replayed return paths could not yet prove that no unintended adapter release side effect committed on Quickstart

Prompt 18 requires the repository to close those gaps without bypassing workflow authority and without fabricating blocked-path success.

## Decision

Implement a dedicated Quickstart runtime mode for the return orchestration layer and bind it to scenario-scoped Quickstart seed, return-workflow, return-adapter, and provider-visible status commands.

The concrete shape is:

1. The return orchestration layer gains an explicit runtime choice:
   - `IDE_LEDGER` remains the existing comparison path
   - `QUICKSTART` becomes a first-class execution mode for the end-to-end confidential return demo
2. Quickstart return scenarios become scenario-scoped runtime inputs:
   - each workflow-bearing Quickstart scenario declares its own seed manifest
   - orchestration writes scenario-scoped state and artifact directories
   - positive, unauthorized, replay, and stale-coverage paths can be tied back to one declared incumbent set and one observed runtime surface
3. Workflow execution stays authoritative on Canton:
   - a new `CantonCollateral.QuickstartReturn` Daml Script layer seeds confidential return scenarios, advances return workflow state, and exposes provider-visible status
   - the positive and replay paths expose a real pending-settlement `SettlementInstruction` for the adapter
   - the unauthorized and stale-coverage negative paths prove the workflow blocked or preserved state before any adapter release could commit
4. Adapter execution remains strictly downstream of workflow state:
   - orchestration invokes the return adapter only when the Quickstart workflow result proves the positive or replay handoff state
   - the adapter consumes the real `SettlementInstruction`, moves only the approved release scope, and then Canton confirms final return closure
   - the replay proof is executed after the original return settles by attempting to reuse the same `returnRequestId`, which must fail without a second adapter receipt
5. `ReturnReport` expands to carry the full Quickstart chain:
   - policy-evaluation artifact
   - optimization artifact
   - Quickstart workflow result artifact
   - Quickstart seed receipt
   - return adapter execution report
   - provider-visible return status artifact
   - explicit request identifier, approval state, release action, final post-return state, and replay handling result

## Rejected Alternatives

### Alternative 1: Keep return on the IDE ledger and document the Quickstart commands separately

Rejected because it would preserve the evidence gap between the operator demo and the real runtime path.

- the return report would still stop before the real adapter-backed release path
- reviewers would need to correlate separate commands manually
- Prompt 18 explicitly requires one real chained Quickstart return command

### Alternative 2: Invoke the return adapter directly from optimization output

Rejected because it would bypass workflow authority.

- the optimizer is advisory only
- the adapter must consume workflow-declared release scope, not re-derive it from off-ledger retained-set output
- skipping the workflow handoff would break the control-plane versus data-plane split defended by ADR 0003 and ADR 0018

### Alternative 3: Treat replay blocking as a workflow-only proof without adapter evidence

Rejected because it would weaken the no-double-release proof.

- reviewers need to see that the original release committed once and only once
- provider-visible adapter receipt count must remain `1` after the replay attempt
- the report must prove both the blocked duplicate identifier and the absence of a second adapter side effect

## Consequences

Positive:

- the repository now has one real Quickstart-backed end-to-end return command rather than disconnected seed, workflow, and adapter fragments
- `ReturnReport` can now prove approval-gated release, final post-return state, replay-safe handling, and blocked unauthorized release on the real runtime path
- the reference token adapter boundary is reused for return release without collapsing workflow authority into the data-plane layer

Tradeoffs:

- the Quickstart return path adds runtime-specific state, manifest, and artifact complexity
- the first Quickstart-backed return chain still uses the narrow reference token adapter rather than a production custodian integration
- conformance aggregation and final packaging still need to decide when or how to absorb the Quickstart return path

These tradeoffs are accepted because the repository needed one real Quickstart-backed return chain now, and Prompt 18 required proof of both committed release and blocked unauthorized or replayed return behavior without waiting for broader disclosure-profile or production adapter work.
