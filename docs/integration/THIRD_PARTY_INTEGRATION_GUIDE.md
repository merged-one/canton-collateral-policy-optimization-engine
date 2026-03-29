# Third-Party Integration Guide

## Purpose

This guide explains how a future venue, financing application, token issuer, custodian, or other Canton project would integrate with the Canton Collateral Control Plane without collapsing policy, optimization, workflow authority, or reporting into one opaque endpoint.

The current repository remains a prototype. The integration surface described here is the stable boundary the prototype already demonstrates through real commands and artifacts, not a claim that all live adapters already exist.

## Integration Principles

1. The Control Plane owns policy evaluation, optimization, workflow orchestration, conformance, and reporting.
2. External systems provide declared inputs and consume declared outputs. They do not gain hidden authority over policy semantics or workflow state.
3. Canton remains the intended authority for workflow state transitions. Off-ledger services may propose, validate, and report, but they must not authoritatively mutate encumbrance state.
4. Every integration should preserve confidentiality, role control, replay safety, and auditability.

## Stable Prototype Surfaces

| Surface | Producer | Consumer | Current Form |
| --- | --- | --- | --- |
| `CPL v0.1` policy package | policy author or governance process | policy engine, optimizer, workflow orchestration | JSON plus schema validation |
| inventory snapshot | venue, custodian, financing app, or asset adapter | policy engine and optimizer | normalized JSON input |
| obligation snapshot | venue or financing app | optimizer and workflow orchestration | normalized JSON input |
| policy decision output | policy engine | operator, venue, financing app, conformance suite | `PolicyEvaluationReport` JSON |
| optimization output | optimizer | operator, workflow orchestration, venue, financing app | `OptimizationReport` JSON |
| workflow input payload | orchestration layer | Daml workflow package | generated JSON input file |
| workflow result output | Daml workflow package | reporting layer, conformance suite, operators | generated JSON output file |
| execution evidence | reporting and conformance layers | operators, reviewers, future integrators | `ExecutionReport`, `SubstitutionReport`, `ReturnReport`, conformance report, final demo pack |

## Integration Patterns

### Venue

A future venue integration would typically:

1. create or expose an obligation snapshot
2. hand the declared policy version, inventory snapshot, and obligation to the Control Plane
3. consume the resulting optimization and workflow execution outputs
4. use the execution artifacts as the venue-facing audit record

Required inputs:

- `obligationId`
- `obligationAmount`
- `settlementCurrency`
- `currentPostedLotIds` when substitution or return is relevant
- optional substitution request scope and atomicity requirements

Expected outputs:

- `OptimizationReport`
- `ExecutionReport`, `SubstitutionReport`, or `ReturnReport`
- correlation identifiers and event identifiers for downstream reconciliation

### Financing Application

A financing or derivatives application integrates at the decision boundary:

1. supply the policy package, inventory snapshot, and obligation snapshot
2. call policy evaluation and optimization first
3. if the workflow should proceed, hand the resulting workflow input payload to the workflow layer
4. persist the resulting machine-readable report as the authoritative integration receipt

This lets the application stay product-specific while the Control Plane remains reusable shared infrastructure.

### Token Issuer

A token issuer or asset-network adapter integrates at the settlement and control boundary, not the policy boundary.

The issuer should consume:

- settlement-system routing
- source and destination accounts
- token adapter reference
- asset and lot identifiers

The issuer should not reinterpret:

- eligibility rules
- haircuting rules
- optimizer objectives
- approval semantics

Those remain Control Plane responsibilities.

### Custodian

A custodian integration participates in approval and settlement confirmation.

The custodian needs:

- workflow request identifiers
- current encumbered lot ids
- replacement or return lot ids
- settlement-system references
- correlation ids and audit event ids

The custodian returns:

- approval or rejection
- settlement confirmation or failure
- the evidence needed to support the resulting workflow report

### Future Canton Project

Another Canton project should integrate with the Control Plane through documented contracts rather than by importing internal Python or Daml modules ad hoc.

The recommended order is:

1. consume published JSON inputs and outputs first
2. align to the current workflow and report contracts
3. only then negotiate deeper package or contract sharing through a new ADR if the boundary truly needs to move

## What The Prototype Already Demonstrates

The repository already proves that a third party can inspect and rely on:

- deterministic policy evaluation
- deterministic optimizer recommendations
- parameterized workflow input payloads
- machine-readable workflow results
- aggregate conformance output
- an operator-ready final demo pack

The prototype does not yet prove:

- live Quickstart deployment of the Control Plane DAR
- live token or custody adapter execution
- production disclosure profiles for different external roles
- reference-data contracts for valuation, FX, or issuer facts

## Recommended Consumption Path

For a future integration, start with these commands and artifacts:

```sh
make policy-eval
make optimize
make demo-margin-call
make demo-substitution
make demo-return
make test-conformance
make demo-all
```

Read these artifacts in order:

1. `reports/generated/central-bank-domestic-window-policy-central-bank-eligible-set-policy-evaluation-report.json`
2. `reports/generated/central-bank-domestic-window-policy-central-bank-eligible-set-central-bank-window-call-optimization-report.json`
3. `reports/generated/margin-call-demo-execution-report.json`
4. `reports/generated/substitution-demo-report.json`
5. `reports/generated/return-demo-report.json`
6. `reports/generated/conformance-suite-report.json`
7. `reports/generated/final-demo-pack.json`

## Boundary Discipline

Do not integrate by:

- scraping Markdown summaries instead of consuming JSON artifacts
- bypassing the workflow layer and mutating encumbrance state directly
- treating optimization output as settlement authority
- extending `CPL` with undeclared fields
- assuming the current prototype already implies a live adapter or Quickstart deployment

If an integration needs a new contract, reference field, or workflow state, record that change through the ADR process and update invariants plus evidence alongside the new interface.
