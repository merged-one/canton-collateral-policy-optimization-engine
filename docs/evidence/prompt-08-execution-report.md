# Prompt 08 Execution Report

## Scope

Create the first credible Quickstart-based LocalNet demo foundation for the Canton Collateral Control Plane, including a pinned upstream CN Quickstart checkout path, overlay-first runtime customization, staged integration plans for a later confidential collateral demo, and reproducible LocalNet bootstrap and smoke commands.

## Commands

```sh
make localnet-bootstrap
make localnet-smoke
make status
make docs-lint
make verify
git status --short --branch
```

## Results

- `make localnet-bootstrap` passed and staged the pinned upstream CN Quickstart checkout at commit `fe56d460af650b71b8e20098b3e76693397a8bf9` under `.runtime/localnet/cn-quickstart/`.
- `make localnet-bootstrap` wrote `quickstart/.env.local` from the repo-owned `lean` overlay profile with `PARTY_HINT=canton-collateral-1`.
- `make localnet-smoke` passed after switching to the upstream `compose-config` target, validated the composed Quickstart stack, and correctly skipped runtime `readyz` probes because the LocalNet was not started in this prompt.
- `make status` passed and reported the pinned CN Quickstart commit plus the staged overlay values alongside the repo-local Daml toolchain.
- `make docs-lint` passed after the new Quickstart docs, ADR, integration plans, evidence file, and command-surface checks were added to the required repository documentation set.
- `make verify` passed and re-executed docs linting, CPL validation, policy-engine tests, optimizer tests, Daml build, Daml lifecycle tests, workflow smoke execution, and the new Quickstart LocalNet smoke check in one reproducible loop.
- `git status --short --branch` before commit showed only the expected Prompt 8 documentation, script, ADR, and infrastructure changes.

Notes:

- the LocalNet foundation intentionally stops at pinned checkout plus compose preflight because the repo Daml package is still pinned to `2.10.4` while the chosen Quickstart runtime line reports `DAML_RUNTIME_VERSION=3.4.10`
- the Daml helper again emitted an informational notice that SDK `3.4.11` exists upstream; the repository remains intentionally pinned to `2.10.4`
- no fake Quickstart-backed `ExecutionReport`, DAR deployment claim, seed-data load, or token movement artifact was added in this prompt
