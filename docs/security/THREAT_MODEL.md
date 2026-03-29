# Threat Model

## Scope

The future system will manage confidential collateral policy, inventory, valuation, workflow, and reporting state across multiple parties. This document records the threat posture implied by the architecture package and the design areas that must remain visible as implementation begins.

The current repository state now includes an initial off-ledger policy evaluation engine, an initial off-ledger optimizer, initial Daml workflow templates for obligations, posting, substitution, return, settlement intent, and execution reporting, end-to-end margin-call, return, and substitution demo runners plus their machine-readable report contracts, an aggregate conformance suite, a final demo pack, and a pinned Quickstart bootstrap plus package-deployment bridge layer. Those surfaces make privacy, determinism, authority, audit boundaries, and runtime-version boundaries concrete, but they are still a skeleton layer rather than a full disclosure-profile, replay-hardening, or adapter-integrated implementation.

## Protected Assets

- confidential policy and position data
- policy version and effective-window data
- inventory-lot and custody-account facts
- authorization decisions and role assignments
- valuation inputs and haircut parameters
- policy evaluation reports and machine-readable failure reasons
- optimization reports, substitution deltas, and explanation traces
- retained-set recommendations and return lot selections
- substitution request scope, required-release lot sets, and atomicity flags
- margin-call demo manifests and workflow-input payloads
- return demo manifests, workflow-input payloads, and return reports
- substitution demo manifests, workflow-input payloads, and substitution reports
- conformance-suite reports and supporting determinism plus haircut evidence
- final demo-pack indexes and artifact maps
- third-party integration guidance
- encumbrance state
- settlement instructions and control acknowledgments
- execution reports and audit evidence
- pinned Quickstart overlay configuration and upstream commit metadata

## Threat Actors

- unauthorized internal user
- authorized user exceeding their role
- compromised integration endpoint
- compromised adjacent service
- operator error during substitution or release
- external observer attempting to infer confidential state

## Core Threats

| Threat | Why It Matters | Initial Control Direction |
| --- | --- | --- |
| Broken authorization or role separation | Users could approve or release collateral outside policy. | Explicit role model, auditable authorization checks, contract-specific controllers, and invariant tracking. |
| Confidentiality leakage | Sensitive counterparty or position information could escape intended visibility. | Privacy-preserving workflow boundaries, explicit observer lists, and minimal reporting disclosure. |
| Over-broad contract visibility | Parties could see obligations, inventory, or settlement data unrelated to their role. | Narrow signatory and observer sets, separate request and settlement templates, role-specific report profiles. |
| Replay or duplicate execution | Repeated events could create duplicate pledges or releases. | Idempotent command design and replay-focused tests. |
| Stale obligation state at release time | A return could release too much collateral if the workflow trusts stale retained-coverage data. | Carry current secured amount and remaining required coverage into the Daml request and reject mismatches on-ledger. |
| Optimizer or reporter treated as authority | Off-ledger services could become hidden sources of truth. | Keep workflow state authoritative on Canton and derive reports from committed state only. |
| Hidden optimizer objective drift or non-deterministic tie handling | Similar requests could yield different substitutions or recommendations that operators cannot defend. | Publish the objective in ADRs and report contracts, keep search order deterministic, and retain explanation traces plus no-churn handling for equal economics. |
| Substitution scope drift or partial settlement acceptance | A request that was approved for one replacement scope could settle a different or incomplete scope. | Carry replacement scope explicitly, enforce atomicity on the Daml boundary, and fail retained-lot or partial-settlement attempts closed. |
| Non-atomic substitution or return | Coverage could be lost during workflow transitions. | Treat atomic workflow completion as a blocking invariant. |
| Report tampering or drift | Operators could rely on incorrect evidence. | State-derived report generation, schema validation, and report-fidelity checks. |
| Integration-boundary drift | Future Canton projects or external participants could couple to unstable demo shapes rather than the intended contract boundary. | Publish an explicit integration guide, final demo pack, and artifact index, and keep boundary moves ADR-backed. |
| Scenario-manifest drift | The operator demo could silently stop representing the documented margin-call shape. | Keep scenario inputs versioned in-repo, validate expected outcomes inside the orchestration layer, and fail closed when they drift. |
| Policy-evaluation report over-disclosure | Off-ledger reports could leak more inventory or counterparty detail than a consumer needs. | Keep report schemas explicit, add role-scoped disclosure profiles later, and avoid hidden joins to external reference data. |
| Optimization-report over-disclosure | Advisory optimization output could reveal more inventory detail or operational preference than a consumer needs. | Keep the optimization report schema explicit, defer role-scoped report profiles, and preserve workflow authority boundaries. |
| Schema downgrade or undeclared extension | Consumers could derive different results from materially different policy documents. | Pin `cplVersion`, reject unknown fields, and validate policy documents before load. |
| Tool-download tampering or drift | A compromised or drifting bootstrap source could change local behavior invisibly. | Pin download URLs and SHA-256 checksums and install runtime tools repo-locally. |
| Runtime overlay drift | Demo or LocalNet shortcuts could alter behavior relative to the documented architecture. | Separate runtime concerns from business semantics and keep overlay changes explicit. |
| Host-versus-Quickstart runtime drift | Operators could trust the host-native IDE-ledger path while the Quickstart-compatible DAR build or deploy path has silently broken. | Keep the dual-runtime bridge explicit, pin the containerized Quickstart build inputs, and verify package build plus deployment through documented commands and evidence. |
| Environment drift | The system could become impossible to reproduce or validate consistently. | Pinned dependencies, checksum-verified bootstrap commands, and release evidence. |

## Trust Boundaries

- policy authoring and registry versus workflow execution
- policy evaluation versus optimization proposal generation
- published CPL schema versus runtime policy ingestion
- optimization proposal generation versus settlement authority
- workflow request contracts versus settlement instructions versus execution-report contracts
- confidential ledger state versus report-generation views
- LocalNet overlay and adjacent services versus upstream Quickstart base
- business roles versus demo and runtime operators

## Open Questions

- which Quickstart topology extensions can be expressed purely through overlays?
- what minimum report profiles satisfy auditability without over-disclosure?
- what minimum substitution-report profile satisfies auditability without exposing unnecessary inventory detail?
- which current demo-pack and conformance-report fields should be elevated into versioned external integration contracts first?
- what freshness and provenance guarantees must a valuation snapshot prove?
- which asset-control semantics belong in the adapter layer versus the workflow package?
- when can the current dual-runtime bridge be retired in favor of one runtime line without losing reproducibility on Apple Silicon and Linux?
- when should future workflow-coupled optimization respect operational churn budgets or consent costs in addition to the current deterministic economic proxy objective?
- how should the current workflow-party execution reports be transformed into narrower operator, auditor, or external-integration views?
- how should future consumers reject or negotiate policies that require a newer `cplVersion` than they support?
- when should the current scenario-derived return approval requirements become first-class CPL return-right clauses?
