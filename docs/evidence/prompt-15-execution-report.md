# Prompt 15 Execution Report

## Scope

Implement the first concrete Quickstart-backed reference token adapter path so the Control Plane can hand a real `SettlementInstruction` and related control context to a narrow data-plane adapter that performs a token-style movement and emits machine-readable execution evidence.

## Adapter Boundary

ADR 0018 chooses a narrow reference path rather than a generic integration bus:

- the Control Plane owns policy, optimization, workflow authority, and report generation
- the adapter consumes `SettlementInstruction` plus related lot and account references without reinterpreting policy
- the asset-side action executes against `ReferenceTokenHolding`
- the adapter emits `ReferenceTokenAdapterReceipt` on-ledger plus a schema-validated adapter execution report under `reports/generated/`

## Commands

```sh
make localnet-deploy-dar
make localnet-run-token-adapter
make localnet-adapter-status
make docs-lint
git diff --check
```

Additional command-level checks executed during implementation:

```sh
sh -n scripts/localnet-control-plane-common.sh
sh -n scripts/localnet-seed-demo.sh
sh -n scripts/localnet-status-control-plane.sh
sh -n scripts/localnet-run-token-adapter.sh
sh -n scripts/localnet-adapter-status.sh
make daml-build
```

## Results

- `make localnet-deploy-dar` passed and deployed `.daml/dist-quickstart/canton-collateral-control-plane-0.1.5.dar` with package id `7fb85f0678a49f3a07f3e4bf7233aeec7bbfbdce53f1bddd58d97d24b86b7ee6` into the pinned Quickstart `app-provider` and `app-user` participants.
- `make localnet-run-token-adapter` passed against scenario `quickstart-reference-token-margin-004` and wrote:
  - `reports/generated/localnet-reference-token-adapter-execution-report.json`
  - `reports/generated/localnet-reference-token-adapter-summary.md`
  - refreshed `reports/generated/localnet-reference-token-adapter-status.json`
  - refreshed `reports/generated/localnet-reference-token-adapter-status-summary.md`
- the adapter execution report proves the adapter consumed settlement instruction `quickstart-reference-token-posting-correlation-004-instruction` for obligation `quickstart-reference-token-obligation-004`.
- the adapter moved:
  - `60.0` of `us-tbill-2029-01` from `custody-provider-001` to `secured-account-001` for lot `quickstart-reference-token-lot-007`
  - `40.0` of `us-tbill-2030-03` from `custody-provider-001` to `secured-account-001` for lot `quickstart-reference-token-lot-008`
- the adapter emitted receipt `quickstart-reference-token-margin-004-reference-token-receipt` with external transaction id `quickstart-reference-token-posting-correlation-004-instruction-reference-token-transfer`.
- the adapter status artifact proves the provider-visible post-execution state is:
  - posting state `Closed`
  - settlement instruction state `Settled`
  - `2` provider-visible pledged encumbrances
  - `1` provider-visible execution report
  - `2` provider-visible reference token holdings in `secured-account-001`
  - `1` provider-visible adapter receipt
- `make localnet-adapter-status` therefore provides a stable inspection surface for the same adapter result from the provider-visible view.
- the implemented path is real Quickstart-backed execution evidence rather than a seeded-only state or a mock adapter artifact.

## Adapter Surface Summary

The implemented reference token adapter consumes:

- `SettlementInstruction`
- lot-level `allocationsInScope`
- obligation id, correlation id, source account, destination account, and asset identifiers

The implemented reference token adapter emits:

- `ReferenceTokenAdapterReceipt` on-ledger
- `adapter-execution-report-v0.1` JSON
- Markdown operator summaries for execution and provider-visible status

Other projects should integrate with this path by:

1. letting the Control Plane create and own the workflow contracts
2. consuming the declared settlement instruction and account references
3. executing the asset-side move on their own network or custody surface
4. returning a machine-readable adapter receipt without reinterpreting policy or rewriting workflow authority

## Remaining Gaps

- the current reference path is still posting-focused; substitution and return adapter paths remain future work
- the Quickstart reference token model is an in-repo reference implementation, not a production custodian or issuer integration
- settlement-window enforcement, production retries, and richer callback semantics remain intentionally absent
