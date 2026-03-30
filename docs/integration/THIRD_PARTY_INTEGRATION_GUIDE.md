# Third-Party Integration Guide

## Purpose

This guide explains how a future venue, financing application, token issuer, custodian, or other Canton project should integrate with the Canton Collateral Control Plane without collapsing policy, optimization, workflow authority, or reporting into one opaque endpoint.

The current repository remains a prototype. The surfaces below describe what is already runtime-proven on Quickstart and what remains staged prototype scope.

## Core Boundary

The boundary is simple and deliberate:

1. The Control Plane owns policy evaluation, optimization, workflow orchestration, conformance, and reporting.
2. External systems supply declared inputs and consume declared outputs.
3. Asset adapters consume workflow-declared settlement intent and emit receipts.
4. Asset adapters do not decide eligibility, approve releases, reinterpret optimization output, or mutate workflow state off-ledger.

That split is the main integration discipline future adopters must preserve.

## Where To Plug In

### Input Boundary

External projects plug into the Control Plane first by supplying:

- a `CPL v0.1` policy package
- an inventory snapshot
- an obligation snapshot
- current posted lot ids when substitution or return scope matters
- workflow correlation or request identifiers for downstream reconciliation

The current prototype proves this boundary through the policy engine, optimizer, and the Quickstart-backed demo manifests.

### Workflow Boundary

Once policy and optimization accept a path, the orchestration layer generates workflow input payloads and Canton becomes authoritative for state transition:

- posting intent
- substitution request and approval flow
- return request and approval flow
- settlement instruction exposure
- final closure or blocked outcome

Future projects should integrate here by consuming generated workflow input or output artifacts, not by importing internal Python or Daml modules ad hoc.

### Settlement And Adapter Boundary

Once Canton exposes a `SettlementInstruction`, an adapter may consume:

- settlement action
- workflow correlation id
- source and destination accounts
- asset and lot identifiers
- allocation scope
- adapter reference metadata

This is the only boundary where an external asset-network integration should move collateral.

## What The Reference Token Adapter Path Does Today

The repository now proves one concrete adapter path on Quickstart.

The reference token adapter path:

- consumes a real `SettlementInstruction` produced by the Control Plane workflow
- reads the lot-level account mapping in `allocationsInScope`
- performs token-style movement on `ReferenceTokenHolding`
- emits a `ReferenceTokenAdapterReceipt`
- emits machine-readable execution and provider-visible status artifacts
- returns control to Canton for workflow confirmation and final closure

The reference token adapter path does not:

- decide whether collateral is eligible
- choose which lots to post, replace, or return
- create settlement instructions on its own
- bypass approval gates
- change obligation, encumbrance, or workflow state outside Canton

That makes it a replacement seam for future adapters, not a special-case authority path.

## What Is Real On Quickstart

The current prototype now proves:

- pinned Quickstart deployment of the Control Plane DAR into `app-provider` and `app-user`
- one concrete reference token adapter posting path with execution and status receipts
- confidential margin call on Quickstart with workflow-to-adapter handoff evidence
- confidential substitution on Quickstart with atomic replacement evidence
- confidential return on Quickstart with approval-gated release and replay-safe duplicate handling evidence
- aggregate conformance and final packaging across those runtime-backed paths

The primary reproducible commands are:

```sh
make localnet-start-control-plane
make localnet-run-token-adapter
make localnet-adapter-status
make demo-margin-call-quickstart
make demo-substitution-quickstart
make demo-return-quickstart
make test-conformance
make demo-all
```

## What Remains Prototype Scope

The repository does not yet prove:

- production-grade custodian or issuer adapters
- a generalized adapter bus or settlement network abstraction
- role-scoped disclosure profiles beyond the current workflow-party and provider-visible baseline
- workflow-coupled optimizer reservation or consent interfaces
- production settlement-window enforcement and retry or recovery semantics
- reference-data contracts for valuation, FX, issuer, and counterparty facts

Future adopters should treat those items as roadmap scope, not as implied current capability.

## How To Replace The Reference Adapter Later

If a future project wants to replace the reference token adapter with a production asset-network, custodian, or token-issuer integration, keep this sequence:

1. Preserve the `SettlementInstruction` contract as the adapter handoff.
2. Preserve Canton as the authority for approval, encumbrance, substitution, and return state.
3. Preserve machine-readable adapter receipts and status artifacts.
4. Add any new routing, custody, or network fields through ADR-backed contract changes.
5. Keep policy, optimization, and workflow semantics outside the adapter.

In practical terms, a replacement adapter may change:

- asset-side API calls
- custody account mapping logic
- receipt payload detail
- provider-visible status fields

A replacement adapter must not change:

- approval semantics
- workflow state authority
- policy or haircut logic
- optimizer objectives
- invariant ownership

## Recommended Consumption Path

For a future integration, consume the surfaces in this order:

1. policy and optimization outputs
2. generated workflow input payloads
3. workflow result artifacts
4. settlement-instruction-to-adapter handoff evidence
5. final execution, substitution, or return report
6. conformance and final demo package outputs

The most concrete artifacts to inspect first are:

1. `reports/generated/localnet-control-plane-deployment-receipt.json`
2. `reports/generated/localnet-reference-token-adapter-execution-report.json`
3. `reports/generated/localnet-reference-token-adapter-status.json`
4. `reports/generated/margin-call-quickstart-execution-report.json`
5. `reports/generated/substitution-quickstart-report.json`
6. `reports/generated/return-quickstart-report.json`
7. `reports/generated/conformance-suite-report.json`
8. `reports/generated/final-demo-pack.json`

## Boundary Discipline

Do not integrate by:

- scraping Markdown summaries instead of consuming JSON artifacts
- bypassing the workflow layer and mutating encumbrance state directly
- treating optimization output as settlement authority
- embedding product-specific settlement logic back into policy evaluation
- assuming the reference adapter path implies production-grade network coverage

If an integration needs a new contract, field, or workflow state, record that change through the ADR process and update invariants plus evidence alongside the new interface.
