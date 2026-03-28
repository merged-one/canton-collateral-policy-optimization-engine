# Dependency Policy

## Goal

Keep the prototype's runtime and verification surface reproducible, easy to audit, and conservative enough for later Canton adoption work.

## Pinned Dependencies

| Dependency | Pinned Version | Source Of Truth | Why It Is Pinned |
| --- | --- | --- | --- |
| Daml SDK 2.10.4 | `2.10.4` | [daml.yaml](../../daml.yaml), [scripts/toolchain.env](../../scripts/toolchain.env) | canonical workflow-modeling toolchain for the repository's Daml package |
| Canton open-source 2.10.4 | `2.10.4` | [scripts/toolchain.env](../../scripts/toolchain.env) | runtime compatibility baseline aligned with the Daml SDK release |
| Temurin JDK 17.0.18+8 | `17.0.18+8` | [scripts/toolchain.env](../../scripts/toolchain.env), [`.tool-versions`](../../.tool-versions) | stable LTS Java baseline for Daml and Canton tooling |
| Python | `3.14.3` | [`.tool-versions`](../../.tool-versions) | recommended local version for repeatable bootstrap and schema validation |
| `check-jsonschema` | `0.37.1` | [requirements-cpl-validation.txt](../../requirements-cpl-validation.txt) | strict pinned validator for `CPL v0.1` inputs and `PolicyEvaluationReport` schema checks |
| CN Quickstart | `fe56d460af650b71b8e20098b3e76693397a8bf9` | [infra/quickstart/overlay/upstream-pin.env](../../infra/quickstart/overlay/upstream-pin.env) | pinned upstream LocalNet source used by the Quickstart demo foundation |
| Quickstart Daml runtime | `3.4.10` | [infra/quickstart/overlay/upstream-pin.env](../../infra/quickstart/overlay/upstream-pin.env) | records the upstream runtime version that must be bridged before DAR deployment |
| Quickstart Splice image set | `0.5.3` | [infra/quickstart/overlay/upstream-pin.env](../../infra/quickstart/overlay/upstream-pin.env) | records the upstream LocalNet image baseline used by the pinned Quickstart commit |

## Installation Policy

- bootstrap from official upstream release archives, not ad hoc mirrors
- verify all downloaded archives with pinned SHA-256 checksums
- install runtime tools under repo-local `.runtime/` rather than relying on mutable global installations
- keep Python validation tooling in repo-local `.venv/`
- keep the Quickstart LocalNet foundation as a pinned upstream checkout plus repo-owned overlays instead of a long-lived fork
- avoid adding service runtimes or package managers until a concrete repository need exists

## Service-Layer Policy

The repository may add off-ledger services only for:

- policy evaluation
- optimization orchestration
- report generation
- integration helpers

Those services must remain small and non-authoritative. Daml remains the intended authority for workflow state and transitions.

## Update Rules

1. Change pins through an ADR or an ADR-backed tracker update.
2. Update `daml.yaml`, `scripts/toolchain.env`, `.tool-versions`, and setup docs together when a pinned tool changes.
3. Keep the Makefile command surface stable unless there is a concrete need to change it.
4. Re-run `make bootstrap`, `make localnet-smoke`, `make daml-build`, `make demo-run`, and `make verify` after any dependency change.

## Deferred Dependencies

These remain intentionally deferred until later phases:

- Quickstart overlay selection and packaging details
- additional report-schema validation tooling beyond `check-jsonschema`
- integration-service frameworks
- any optimizer-specific solver libraries
- automated DAR deployment into the pinned Quickstart runtime before the version bridge is closed
