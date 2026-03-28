# Canton Collateral Policy Optimization Engine

## What this prototype is

This repository is a documentation-first prototype for a confidential collateral management system built around Canton-style workflows. The target system will cover:

- confidential collateral policy definition
- margin call processing
- collateral substitution
- margin return and release
- machine-readable execution reporting

The intended runtime shape is a Quickstart-based LocalNet with token-standard-style assets and auditable reports that can be checked against invariants, evidence, and tests.

## Why documentation-first

Collateral policy, control, substitution, and release handling are safety-critical. Before business logic exists, this repository establishes the operating rules needed to build the prototype safely:

- requirements must trace to invariants, evidence, and tests
- significant design choices must be captured as ADRs
- changes must leave behind reproducible commands
- demos must be reproducible and must not contain fake success artifacts

This order of work is deliberate. In a mission-critical collateral system, undocumented assumptions are defects.

## Target High-Level Architecture

The target architecture separates concerns that are often conflated in ad hoc prototypes:

1. Policy layer
   Versioned eligibility, haircut, concentration, and control rules.
2. Optimization layer
   Deterministic collateral selection and substitution proposals under policy constraints.
3. Workflow execution layer
   Confidential, atomic multi-party flows on Canton for pledge, substitution, and release.
4. Reporting layer
   Machine-readable execution reports tied to committed workflow outcomes.
5. Evidence and control layer
   ADRs, invariants, risk records, runbooks, and reproducible verification commands.

This maps to established practice:

- central-bank collateral frameworks separate eligibility, valuation, haircuting, control, and settlement concerns
- tri-party repo utilities manage selection, valuation, substitution, and operational coordination
- CCP-style controls apply conservative haircuts and concentration limits
- Canton provides privacy-preserving, atomic workflows across multiple parties and applications

## Scope

Current scope:

- repository governance and operating rules
- mission-control documents and decision tracking
- initial architecture, invariant, risk, and evidence structure
- implementation-ready planning for LocalNet, asset, workflow, and reporting phases

## Non-Goals

Current non-goals:

- production-ready economic calibration
- live integrations with custodians, CCPs, or central-bank systems
- UI development
- performance tuning
- implementation of business logic in this prompt

## Mission Control

Mission control is the repository's operating spine. Start here:

- [AGENTS.md](./AGENTS.md)
- [docs/mission-control/MASTER_TRACKER.md](./docs/mission-control/MASTER_TRACKER.md)
- [docs/mission-control/WORKLOG.md](./docs/mission-control/WORKLOG.md)
- [docs/invariants/INVARIANT_REGISTRY.md](./docs/invariants/INVARIANT_REGISTRY.md)
- [docs/evidence/EVIDENCE_MANIFEST.md](./docs/evidence/EVIDENCE_MANIFEST.md)

Working rules:

- read `AGENTS.md` and `MASTER_TRACKER.md` before making changes
- update `WORKLOG.md` before and after each task
- update invariants and evidence for every new feature
- record significant design choices as ADRs

Reproducible commands today:

```sh
make status
make docs-lint
make verify
```

## Upcoming Phases

- Phase 0: documentation and mission-control spine
- Phase 1: pinned LocalNet baseline, interface contracts, and dependency decisions
- Phase 2: token-standard-style asset model and policy data contracts
- Phase 3: policy evaluation and optimization specifications with invariant-linked tests
- Phase 4: Canton workflows for margin call, substitution, and margin return
- Phase 5: machine-readable execution reports, demo flows, and release evidence
