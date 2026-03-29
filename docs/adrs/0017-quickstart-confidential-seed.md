# ADR 0017: Seed The Quickstart Confidential Scenario Through Repo-Owned Overlay Scripts

- Status: Accepted
- Date: 2026-03-29

## Context

ADR 0015 established a pinned, overlay-first Quickstart foundation and ADR 0016 closed the runtime bridge needed to build and deploy the Canton Collateral Control Plane DAR into that pinned LocalNet. After Prompt 13, the Control Plane package could be installed into Quickstart, but the repository still lacked a real confidential scenario on the running LocalNet.

Prompt 14 requires more than package presence:

- start the pinned LocalNet from repo-owned command surfaces
- allocate the parties and roles needed for one confidential collateral scenario
- seed one real margin-style obligation plus supporting inventory and posting state
- emit evidence that proves the seeded state lives on Quickstart rather than only on the IDE ledger

The repository still needs to stay overlay-first. It should not fork upstream Quickstart merely to allocate parties, create users, or seed one scenario.

## Decision

Use a repo-owned Quickstart control-plane overlay that combines upstream-preserving shell wrappers with a multi-participant Daml Script seed and status layer.

The concrete shape is:

1. `make localnet-start-control-plane` remains upstream-preserving for runtime ownership:
   - bootstrap the pinned checkout if needed
   - run the upstream Quickstart build or start path when the stack is not already running
   - deploy the Control Plane DAR through the existing Quickstart runtime bridge
   - write a machine-readable package deployment receipt
2. Party and user allocation stays repo-owned but does not patch upstream Quickstart:
   - discover the existing Quickstart app-user and app-provider parties from the onboarding container
   - allocate any additional scenario parties, such as custodian and operator, through the participant-management APIs exposed by the running LocalNet
   - create or reuse participant users with explicit `CanActAs` plus `CanReadAs` rights for those seeded parties
3. Scenario contract seeding and status queries run through Daml Script against the running Quickstart participants:
   - use a participant-config file with explicit participant aliases, tokens, and party-to-participant mapping
   - seed the obligation, inventory, role registrations, and posting intent through the shared Control Plane DAR rather than hand-crafted JSON command payloads
   - generate status from provider-visible ledger queries so the evidence surface is derived from active contracts on Quickstart
4. The first seeded confidential scenario maps roles as follows:
   - existing Quickstart `app-user` party acts as the collateral provider
   - existing Quickstart `app-provider` party acts as the secured party
   - repo-allocated Quickstart party acts as the custodian
   - repo-allocated Quickstart party acts as the optional operator for role registration
5. Evidence must be written to repo-visible artifacts:
   - package deployment receipt
   - seed receipt with party and contract identifiers
   - Quickstart-oriented status summary and ledger query snapshot

## Rejected Alternatives

### Alternative 1: Fork upstream Quickstart to add Control-Plane-specific seed containers

Rejected because the required behavior can be expressed by overlays and adjacent scripts.

- the onboarding container already exposes the auth and package-upload hooks needed for repo-owned automation
- participant-management APIs already exist on the running LocalNet
- a fork would increase long-lived drift without buying a necessary extension point

### Alternative 2: Seed the scenario through hand-written participant JSON payloads only

Rejected because the Daml contract surface is already shared across the IDE-ledger and Quickstart paths.

- direct JSON payloads would duplicate template encoding knowledge outside the Daml package
- variant and user-submission semantics would become harder to keep aligned across runtime lines
- machine-readable seed evidence is cleaner when the ledger-returned contract ids come from the shared package and Daml Script output

### Alternative 3: Keep Quickstart proof at package deployment only

Rejected because Prompt 14 explicitly requires a real confidential scenario on Quickstart.

- package presence alone does not prove the seeded role or contract topology
- the Control Plane needs at least one real LocalNet scenario before workflow execution and adapter work can build on it safely

## Consequences

Positive:

- the repository now exposes a real Quickstart control-plane bootstrap, deploy, seed, and status surface without forking upstream Quickstart
- the first confidential scenario becomes a real LocalNet artifact with ledger-returned contract identifiers
- Quickstart evidence now includes contract state rather than only package state

Tradeoffs:

- the seeded scenario still stops at seeded ledger state rather than full Quickstart-backed workflow execution
- the command surface now depends on both participant-management permissions and Daml Script participant-config generation
- app-user and app-provider remain the first provider and secured-party anchors until dedicated app-specific parties are justified

These tradeoffs are accepted because they provide the smallest credible path from package deployment to a real confidential Quickstart scenario while preserving upstream ownership and one shared Control Plane Daml source tree.
